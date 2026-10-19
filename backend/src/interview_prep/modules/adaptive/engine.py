"""Pure, bounded, replayable editorial policy. Scores are priorities, not probabilities."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from interview_prep.modules.adaptive.schemas import (
    Candidate,
    Choice,
    Exposure,
    Performance,
    Selection,
    SelectionInput,
    SkillContext,
)
from interview_prep.modules.questions.models import Difficulty

LEVELS = (Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD)
IMPORTANCE = {"Low relevance": 0, "Mentioned": 1, "Preferred": 2, "Required": 3}
NEED = {"maintain": 0.0, "unknown": 0.5, "practice": 1.0}
RECENT = 5
COVERAGE = 20


@dataclass(frozen=True)
class DifficultyState:
    level: int
    reason: str
    floor_failure: bool = False


def difficulty_state(performance: tuple[Performance, ...], skill: str) -> DifficultyState:
    records = sorted(
        (p for p in performance if p.eligible and p.skill == skill),
        key=lambda p: (p.occurred_at, p.id),
    )
    if not records:
        return DifficultyState(0, "Cold start: easy diagnostic; missing evidence is not failure.")
    level = min(
        LEVELS.index(record.difficulty)
        for record in records
        if record.occurred_at == records[0].occurred_at
    )
    reason = "Start from earliest eligible difficulty; tied timestamps use the easier level."
    streak: set[str] = set()
    previous: str | None = None
    floor_failure = False
    for record in records:
        observed = LEVELS.index(record.difficulty)
        # Easier successes and harder failures cannot move the current target.
        relevant = observed >= level if record.outcome == "met" else observed <= level
        if not relevant:
            streak.clear()
            previous = None
            continue
        if previous != record.outcome:
            streak.clear()
        previous = record.outcome
        # Repeated success on one concept can reflect memorization. Repeated
        # failure on that concept still warrants relief, using distinct result IDs.
        streak.add(record.concept if record.outcome == "met" else record.id)
        if len(streak) < 2:
            continue
        if record.outcome == "met":
            level = min(2, level + 1)
            floor_failure = False
            reason = "Two distinct concepts succeeded at/above target; raise one level (cap hard)."
        else:
            floor_failure = level == 0
            level = max(0, level - 1)
            reason = "Two eligible results failed at/below target; lower one level (floor easy)."
        streak.clear()
        previous = None
    return DifficultyState(level, reason, floor_failure)


def select_questions(data: SelectionInput) -> Selection:
    """Greedy batch selection, updating exposures but never inventing batch outcomes."""
    contexts = {s.key: s for s in data.skills}
    states = {
        key: difficulty_state(data.performance, key)
        for key in {key for c in data.candidates for key in c.skills}
    }

    def context(candidate: Candidate) -> SkillContext | None:
        # One accountable driver, never sum several skills to inflate relevance.
        return max(
            (contexts.get(key, SkillContext(key=key)) for key in candidate.skills),
            key=lambda s: (IMPORTANCE[s.importance], NEED[s.need], s.key),
            default=None,
        )

    def state(candidate: Candidate) -> DifficultyState:
        driver = context(candidate)
        return (
            states[driver.key]
            if driver
            else DifficultyState(0, "No skill mapping: easy diagnostic.")
        )

    def group(candidate: Candidate) -> tuple[str, str | None]:
        driver = context(candidate)
        return candidate.topic, driver.key if driver else None

    remaining = list(data.candidates)
    history = list(data.history)
    choices: list[Choice] = []
    notices: list[str] = []
    for _ in range(data.count):
        if not remaining:
            notices.append("Inventory exhausted; returned fewer questions than requested.")
            break
        reasons: list[str] = []
        last_seen = {h.question_id: i for i, h in enumerate(history)}
        recent = {h.question_id for h in history[-RECENT:]}
        pool = [c for c in remaining if c.question_id not in recent]
        if not pool:
            oldest = min(last_seen[c.question_id] for c in remaining)
            pool = [c for c in remaining if last_seen[c.question_id] == oldest]
            reasons.append(
                "Recent-question cooldown exhausted; reuse the least recently allocated question."
            )
        else:
            reasons.append("Excluded questions from the last five allocations across versions.")
        concepts = {h.concept for h in history[-2:]}
        fresh = [c for c in pool if c.concept not in concepts]
        if fresh:
            pool = fresh
            reasons.append("Avoid concepts from the last two allocations when alternatives exist.")
        if len(history) >= 2 and history[-1].topic == history[-2].topic:
            diverse = [c for c in pool if c.topic != history[-1].topic]
            if diverse:
                pool = diverse
                reasons.append("Redirect after two consecutive allocations in one topic.")
        coverage = Counter(h.topic for h in history[-COVERAGE:])
        sequence = data.history_count if data.history_count is not None else len(data.history)
        sequence += len(choices)
        if (sequence + 1) % 4 == 0:
            minimum = min(coverage[c.topic] for c in pool)
            pool = [c for c in pool if coverage[c.topic] == minimum]
            reasons.append("Every fourth allocation explores the least-covered available topic.")
        # Within each topic/driver choose the closest available level, preferring
        # an easier neighbor on an equal distance. Never relax caller filters here.
        distances: dict[tuple[str, str | None], tuple[int, int]] = {}
        for candidate in pool:
            driver = context(candidate)
            key = (candidate.topic, driver.key if driver else None)
            actual = LEVELS.index(candidate.difficulty)
            distance = (abs(actual - state(candidate).level), actual)
            distances[key] = min(distances.get(key, distance), distance)
        pool = [
            c
            for c in pool
            if (abs(LEVELS.index(c.difficulty) - state(c).level), LEVELS.index(c.difficulty))
            == distances[group(c)]
        ]

        def components(
            candidate: Candidate,
            coverage: Counter[str] = coverage,
        ) -> dict[str, float]:
            driver = context(candidate)
            relevance = IMPORTANCE[driver.importance] if driver else 0
            need = NEED[driver.need] if driver else 0.5
            difficulty = state(candidate)
            return {
                "job_relevance": 20.0 * relevance,
                "practice_need": (10.0 + 10.0 * relevance) * need,
                "coverage": 12.0 / (1 + coverage[candidate.topic]),
                "difficulty_distance": -18.0
                * abs(LEVELS.index(candidate.difficulty) - difficulty.level),
                "failure_break": -40.0
                if difficulty.floor_failure and history and history[-1].topic == candidate.topic
                else 0.0,
            }

        def order(
            candidate: Candidate,
            last_seen: dict[UUID, int] = last_seen,
            sequence: int = sequence,
        ) -> tuple[float, int, str, str]:
            digest = sha256(f"{data.seed}:{sequence}:{candidate.question_id}".encode()).hexdigest()
            return (
                -sum(components(candidate).values()),
                last_seen.get(candidate.question_id, -1),
                digest,
                str(candidate.question_id),
            )

        selected = min(pool, key=order)
        driver = context(selected)
        difficulty = state(selected)
        values = components(selected)
        reasons.extend(
            [
                difficulty.reason,
                f"Driver importance: {driver.importance if driver else 'Low relevance'}; "
                f"need: {driver.need if driver else 'unknown'}.",
                "Ties: least recent use, then seeded SHA-256; scores are editorial priorities.",
            ]
        )
        if LEVELS[difficulty.level] != selected.difficulty:
            reasons.append(
                "Target difficulty unavailable after filters/cooldowns; use nearest level."
            )
        choices.append(
            Choice(
                question_id=selected.question_id,
                version_id=selected.version_id,
                topic=selected.topic,
                skill=driver.key if driver else None,
                difficulty=selected.difficulty,
                target_difficulty=LEVELS[difficulty.level],
                score=sum(values.values()),
                components=values,
                reasons=tuple(reasons),
            )
        )
        history.append(
            Exposure(
                question_id=selected.question_id,
                topic=selected.topic,
                concept=selected.concept,
            )
        )
        remaining.remove(selected)
    return Selection(choices=tuple(choices), notices=tuple(notices))
