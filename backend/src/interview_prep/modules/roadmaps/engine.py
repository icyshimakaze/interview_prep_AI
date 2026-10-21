"""Deterministic editorial recommendations and weekly capacity, never readiness."""

from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256

from interview_prep.modules.roadmaps.schemas import Recommendation
from interview_prep.modules.skills.schemas import SkillRow


@dataclass(frozen=True)
class DefenseSignal:
    project_id: str
    name: str
    question_id: str
    focus: str
    status: str
    answer_id: str = ""


@dataclass(frozen=True)
class Scheduled:
    recommendation: Recommendation
    minutes: int
    scheduled_on: date | None


def recommend(
    rows: list[SkillRow],
    defense: list[DefenseSignal],
    *,
    target_priority: str | None,
    has_target: bool,
    interview_count: int,
) -> list[Recommendation]:
    result: list[Recommendation] = []
    for row in rows:
        # Completion refers to this topic/activity, not to a competence level.
        action = row.action if row.action in {"Practice", "Maintain"} else "Validate"
        high = row.importance == "Required" or (
            target_priority == "high" and row.importance in {"Preferred", "Mentioned"}
        )
        all_sources = sorted({s.id for s in row.sources})
        sources = all_sources[:12]
        fingerprint = sha256("|".join(all_sources).encode()).hexdigest()[:16]
        reason = (
            f"{row.importance} for the selected target. {row.explanation[0]} "
            f"{row.resume_state}; resume mentions do not validate performance."
        )
        objectives = {
            "Practice": "Correct one observed gap and verify the correction on a fresh question.",
            "Validate": "Collect a reviewed assessment result to test the claimed scope.",
            "Maintain": "Revisit the tested scope on a different example and explain its limits.",
        }
        activities = {
            "Practice": "Review the relevant answer rationale, work a small example, then "
            "take a fresh assessment.",
            "Validate": "Choose a reviewed assessment for this topic; record an answer "
            "before reading its rationale.",
            "Maintain": "Solve an unfamiliar example and explain a trade-off; use a fresh "
            "assessment to check it.",
        }
        result.append(
            Recommendation(
                key=f"skill:{row.key}:{action.lower()}:{fingerprint}",
                topic=row.name,
                reason=reason,
                priority="low" if action == "Maintain" else "high" if high else "medium",
                objective=objectives[action],
                activity=activities[action],
                source_ids=sources,
            )
        )
    # Use at most two distinct focuses per project. Unasked/skipped is not failure.
    used: dict[str, int] = {}
    for signal in sorted(
        defense,
        key=lambda s: (
            {"skipped": 0, "draft": 1, "submitted": 2}.get(s.status, 3),
            s.project_id,
            s.focus,
            s.question_id,
        ),
    ):
        if used.get(signal.project_id, 0) >= 2:
            continue
        used[signal.project_id] = used.get(signal.project_id, 0) + 1
        result.append(
            Recommendation(
                key=f"defense:{signal.project_id}:{signal.focus}:{signal.answer_id}:{signal.status}",
                topic=f"Project explanation: {signal.focus}",
                reason=f"{signal.name}: latest defense answer is {signal.status}. "
                "Defense practice is unscored; this status does not establish a skill gap "
                "or strength.",
                priority="medium",
                objective="Explain a decision with source evidence and a testable failure case.",
                activity="Revisit this defense question. Separate your contributions "
                "from AI assistance, "
                "check the explanation against code/tests, and ask a reviewer to challenge it.",
                source_ids=[signal.question_id],
            )
        )
    if not has_target:
        result.append(
            Recommendation(
                key="context:target",
                topic="Choose and review a target job",
                reason="No target is selected. Topic ordering currently has no "
                "selected-job requirements.",
                priority="high",
                objective="Identify the role and requirements you want to practise.",
                activity="Save a target job, set its priority, and review its requirements "
                "in the skill matrix.",
            )
        )
    if not rows:
        result.append(
            Recommendation(
                key="baseline:assessment",
                topic="Establish an assessment baseline",
                reason="No mapped performance or skill context is available; "
                "missing evidence is not failure.",
                priority="high",
                objective="Record a reviewed objective assessment and examine its rationale.",
                activity="Take a small assessment in your target area. Add resume evidence "
                "if it helps identify topics.",
            )
        )
    result.append(
        Recommendation(
            key="baseline:interview"
            if not interview_count
            else f"validation:interview:{interview_count}",
            topic="Practise an explanation"
            if not interview_count
            else "Validate interview explanations",
            reason="No completed interview is recorded."
            if not interview_count
            else f"{interview_count} completed interviews are recorded; "
            "detail windows are bounded. "
            "Simulated/model feedback needs independent validation.",
            priority="medium",
            objective="Explain a decision, its trade-offs, and how you checked it.",
            activity="Run a short interview, then verify one explanation using "
            "a concrete example or reviewer.",
        )
    )
    return sorted(
        result,
        key=lambda r: (
            ("high", "medium", "low").index(r.priority),
            r.topic.casefold(),
            r.key,
        ),
    )


def schedule(
    recommendations: list[Recommendation],
    completed_keys: set[str],
    weekly_minutes: int,
    starts_on: date,
    interview_date: date | None,
) -> tuple[list[Scheduled], list[str]]:
    candidates = [r for r in recommendations if r.key not in completed_keys]
    notes = ["Editorial recommendations; task completion records activity, not competence."]
    if len(candidates) > 12:
        notes.append("Only the first 12 priorities are scheduled; regenerate after new evidence.")
    budget = (
        None
        if interview_date is None
        else max(
            0,
            weekly_minutes * ((interview_date - starts_on).days + 1) // 7,
        )
    )
    result: list[Scheduled] = []
    used = 0
    week_used = 0
    week = 0
    for item in candidates[:12]:
        minutes = min(weekly_minutes, 30 if item.priority == "low" else 60)
        if week_used + minutes > weekly_minutes:
            week += 1
            week_used = 0
        fits = budget is None or used + minutes <= budget
        proposed = starts_on + timedelta(days=week * 7)
        at = proposed if fits and (interview_date is None or proposed <= interview_date) else None
        if at is not None:
            used += minutes
            week_used += minutes
        result.append(Scheduled(item, minutes, at))
    if any(item.scheduled_on is None for item in result):
        notes.append(
            "Some tasks do not fit the estimated capacity before your interview date. "
            "They remain queued without a scheduled date; narrow priorities or adjust your budget."
        )
    if completed_keys:
        notes.append(
            "Already-completed topic/activity keys were omitted. Earlier tasks and "
            "completion history remain saved."
        )
    return result, notes
