from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import pytest
from pydantic import ValidationError

from interview_prep.modules.adaptive.engine import difficulty_state, select_questions
from interview_prep.modules.adaptive.schemas import (
    Candidate,
    Exposure,
    Performance,
    SelectionInput,
    SkillContext,
)
from interview_prep.modules.questions.models import Difficulty


def candidate(
    n: int,
    difficulty: Difficulty = Difficulty.EASY,
    topic: str = "SQL",
    skill: str = "sql",
    concept: str | None = None,
) -> Candidate:
    return Candidate(
        question_id=UUID(int=n),
        version_id=UUID(int=n + 10000),
        topic=topic,
        concept=concept or f"concept-{n}",
        skills=(skill,),
        difficulty=difficulty,
    )


def performance(
    n: int,
    difficulty: Difficulty = Difficulty.EASY,
    outcome: Literal["met", "practice"] = "met",
    skill: str = "sql",
    concept: str | None = None,
    eligible: bool = True,
    channel: Literal["assessment", "interview"] = "assessment",
) -> Performance:
    return Performance(
        id=str(n),
        skill=skill,
        concept=concept or f"concept-{n}",
        difficulty=difficulty,
        outcome=outcome,
        eligible=eligible,
        channel=channel,
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=n),
    )


def exposure(c: Candidate) -> Exposure:
    return Exposure(question_id=c.question_id, topic=c.topic, concept=c.concept)


POOL = tuple(candidate(i + 1, level) for i, level in enumerate(Difficulty))


def test_new_candidate_starts_easy_with_explanation_and_no_mutation() -> None:
    data = SelectionInput(candidates=POOL)
    snapshot = data.model_dump_json()
    choice = select_questions(data).choices[0]
    assert choice.difficulty == Difficulty.EASY
    assert choice.target_difficulty == Difficulty.EASY
    assert "Cold start" in " ".join(choice.reasons)
    assert choice.score == sum(choice.components.values())
    assert data.model_dump_json() == snapshot


def test_strong_candidate_starts_hard_from_demonstrated_medium_success() -> None:
    result = select_questions(
        SelectionInput(
            candidates=POOL,
            performance=(
                performance(1, Difficulty.MEDIUM),
                performance(2, Difficulty.MEDIUM),
            ),
        )
    )
    assert result.choices[0].difficulty == Difficulty.HARD


def test_weak_candidate_reduces_medium_to_easy() -> None:
    result = select_questions(
        SelectionInput(
            candidates=POOL,
            performance=(
                performance(1, Difficulty.MEDIUM, "practice"),
                performance(2, Difficulty.MEDIUM, "practice"),
            ),
        )
    )
    assert result.choices[0].difficulty == Difficulty.EASY


def test_role_specific_high_relevance_weak_area_wins() -> None:
    result = select_questions(
        SelectionInput(
            candidates=(
                candidate(1),
                candidate(2, topic="Python", skill="python"),
                candidate(3, topic="Systems", skill="systems"),
            ),
            skills=(
                SkillContext(key="sql", importance="Required", need="practice"),
                SkillContext(key="python", importance="Required", need="maintain"),
                SkillContext(key="systems", importance="Low relevance", need="practice"),
            ),
        )
    )
    assert result.choices[0].skill == "sql"
    assert result.choices[0].components["job_relevance"] == 60
    assert result.choices[0].components["practice_need"] == 40


def test_missing_historical_data_is_unknown_not_weak() -> None:
    result = select_questions(SelectionInput(candidates=POOL))
    assert result.choices[0].components["practice_need"] == 5
    assert result.choices[0].target_difficulty == Difficulty.EASY


def test_ineligible_mock_or_self_review_cannot_raise_difficulty() -> None:
    records = tuple(performance(i, Difficulty.HARD, eligible=False) for i in range(5))
    assert difficulty_state(records, "sql").level == 0


def test_one_success_or_repeated_same_concept_cannot_raise_difficulty() -> None:
    assert difficulty_state((performance(1),), "sql").level == 0
    assert (
        difficulty_state(tuple(performance(i, concept="same") for i in range(5)), "sql").level == 0
    )


def test_one_failure_does_not_lower_difficulty() -> None:
    assert difficulty_state((performance(1, Difficulty.MEDIUM, "practice"),), "sql").level == 1


def test_repeated_failure_on_same_concept_still_reduces_difficulty() -> None:
    records = (
        performance(1, Difficulty.MEDIUM, "practice", concept="same"),
        performance(2, Difficulty.MEDIUM, "practice", concept="same"),
    )
    assert difficulty_state(records, "sql").level == 0


def test_harder_failures_do_not_reduce_an_easier_target() -> None:
    records = (
        performance(1, Difficulty.MEDIUM),
        performance(2, Difficulty.HARD, "practice"),
        performance(3, Difficulty.HARD, "practice"),
    )
    assert difficulty_state(records, "sql").level == 1


def test_difficulty_increases_only_one_step_per_distinct_pair() -> None:
    records: tuple[Performance, ...] = (performance(1), performance(2))
    assert difficulty_state(records, "sql").level == 1
    records += (performance(3), performance(4))
    assert difficulty_state(records, "sql").level == 1  # easy successes cannot reach hard
    records += (performance(5, Difficulty.MEDIUM), performance(6, Difficulty.MEDIUM))
    assert difficulty_state(records, "sql").level == 2


def test_difficulty_decreases_and_clamps_at_easy() -> None:
    records: tuple[Performance, ...] = (
        performance(1, Difficulty.HARD, "practice"),
        performance(2, Difficulty.HARD, "practice"),
    )
    assert difficulty_state(records, "sql").level == 1
    records += (
        performance(3, Difficulty.MEDIUM, "practice"),
        performance(4, Difficulty.MEDIUM, "practice"),
    )
    assert difficulty_state(records, "sql").level == 0
    records += (performance(5, outcome="practice"), performance(6, outcome="practice"))
    assert difficulty_state(records, "sql").floor_failure


def test_difficulty_ceiling_and_mixed_results_reset_streaks() -> None:
    assert (
        difficulty_state(tuple(performance(i, Difficulty.HARD) for i in range(6)), "sql").level == 2
    )
    mixed = (performance(1), performance(2, outcome="practice"), performance(3))
    assert difficulty_state(mixed, "sql").level == 0


def test_interview_results_contribute_but_other_skills_do_not() -> None:
    records = (performance(1, channel="interview"), performance(2, channel="interview"))
    assert difficulty_state(records, "sql").level == 1
    assert difficulty_state(records, "python").level == 0


def test_performance_order_is_chronological() -> None:
    records = (
        performance(1),
        performance(2),
        performance(3, Difficulty.MEDIUM, "practice"),
        performance(4, Difficulty.MEDIUM, "practice"),
    )
    assert difficulty_state(records, "sql") == difficulty_state(tuple(reversed(records)), "sql")


def test_mixed_difficulty_at_first_timestamp_uses_conservative_baseline() -> None:
    hard = performance(1, Difficulty.HARD)
    easy = performance(2).model_copy(update={"occurred_at": hard.occurred_at})
    # Two successes move easy to medium; arbitrary source ID order cannot start hard.
    assert difficulty_state((hard, easy), "sql").level == 1


def test_recent_question_avoidance_survives_version_change() -> None:
    original, other = candidate(1), candidate(2)
    updated = original.model_copy(update={"version_id": UUID(int=9999)})
    result = select_questions(
        SelectionInput(
            candidates=(updated, other),
            history=(exposure(original),),
        )
    )
    assert result.choices[0].question_id == other.question_id


def test_same_concept_variants_avoided_when_possible() -> None:
    original = candidate(1)
    variant = candidate(2, concept=original.concept)
    other = candidate(3)
    result = select_questions(
        SelectionInput(
            candidates=(variant, other),
            history=(exposure(original),),
        )
    )
    assert result.choices[0].question_id == other.question_id


def test_cooldown_exhaustion_is_least_recent_and_disclosed() -> None:
    a, b = candidate(1), candidate(2)
    result = select_questions(
        SelectionInput(
            candidates=(a, b),
            history=(exposure(a), exposure(b)),
        )
    )
    assert result.choices[0].question_id == a.question_id
    assert "cooldown exhausted" in " ".join(result.choices[0].reasons)


def test_batch_has_no_duplicates_and_does_not_invent_success() -> None:
    result = select_questions(SelectionInput(candidates=POOL, count=3))
    assert len({c.question_id for c in result.choices}) == 3
    assert all(c.target_difficulty == Difficulty.EASY for c in result.choices)


def test_topic_diversity_redirects_after_two_allocations() -> None:
    result = select_questions(
        SelectionInput(
            candidates=(candidate(3), candidate(4, topic="Python", skill="python")),
            history=(exposure(candidate(1)), exposure(candidate(2))),
            skills=(SkillContext(key="sql", importance="Required", need="practice"),),
        )
    )
    assert result.choices[0].topic == "Python"


def test_fourth_turn_exploration_preserves_absolute_cursor_after_truncation() -> None:
    result = select_questions(
        SelectionInput(
            candidates=(candidate(3), candidate(4, topic="Python", skill="python")),
            history=(exposure(candidate(1)),),
            history_count=1003,
            skills=(SkillContext(key="sql", importance="Required", need="practice"),),
        )
    )
    assert result.choices[0].topic == "Python"
    assert "fourth" in " ".join(result.choices[0].reasons)


def test_easy_failure_penalty_favors_topic_break() -> None:
    result = select_questions(
        SelectionInput(
            candidates=(candidate(3), candidate(4, topic="Python", skill="python")),
            history=(exposure(candidate(1)),),
            performance=(performance(1, outcome="practice"), performance(2, outcome="practice")),
        )
    )
    assert result.choices[0].topic == "Python"


def test_nearest_difficulty_tie_prefers_easier() -> None:
    result = select_questions(
        SelectionInput(
            candidates=(POOL[0], POOL[2]),
            performance=(performance(1), performance(2)),
        )
    )
    assert result.choices[0].difficulty == Difficulty.EASY
    assert result.choices[0].target_difficulty == Difficulty.MEDIUM
    assert "unavailable" in " ".join(result.choices[0].reasons)


def test_empty_and_insufficient_inventory_are_explicit() -> None:
    assert not select_questions(SelectionInput(candidates=())).choices
    result = select_questions(SelectionInput(candidates=(POOL[0],), count=2))
    assert len(result.choices) == 1
    assert "exhausted" in result.notices[0]


def test_reproducible_and_independent_of_inventory_order() -> None:
    pool = tuple(candidate(i) for i in range(1, 12))
    a = SelectionInput(candidates=pool, count=5, seed="replay")
    b = SelectionInput(candidates=tuple(reversed(pool)), count=5, seed="replay")
    assert select_questions(a) == select_questions(b) == select_questions(a)
    assert (
        len(
            {
                select_questions(SelectionInput(candidates=pool, seed=str(i)))
                .choices[0]
                .question_id
                for i in range(20)
            }
        )
        > 1
    )


def test_repeated_calls_do_not_starve_topics_or_loop_over_two_questions() -> None:
    pool = tuple(candidate(i, topic=f"topic-{i % 4}", skill=f"skill-{i % 4}") for i in range(1, 17))
    history: list[Exposure] = []
    by_id = {c.question_id: c for c in pool}
    for _ in range(80):
        result = select_questions(
            SelectionInput(
                candidates=pool,
                history=tuple(history),
                seed="fixed",
                skills=(SkillContext(key="skill-0", importance="Required", need="practice"),),
            )
        )
        choice = result.choices[0]
        assert choice.question_id not in {h.question_id for h in history[-5:]}
        history.append(exposure(by_id[choice.question_id]))
    assert len({h.question_id for h in history}) == len(pool)


@pytest.mark.parametrize(
    "patch",
    [
        {"count": 0},
        {"count": 13},
        {"count": True},
        {"seed": ""},
        {"history_count": -1},
        {"candidates": (POOL[0], POOL[0])},
        {"skills": (SkillContext(key="sql"), SkillContext(key="sql"))},
        {"performance": (performance(1), performance(1))},
        {"history": (exposure(POOL[0]),), "history_count": 0},
    ],
)
def test_invalid_inputs_rejected(patch: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SelectionInput.model_validate({"candidates": POOL, **patch})


def test_no_skill_mapping_is_safe() -> None:
    c = candidate(1).model_copy(update={"skills": ()})
    choice = select_questions(SelectionInput(candidates=(c,))).choices[0]
    assert choice.skill is None and choice.target_difficulty == Difficulty.EASY
