from datetime import UTC, datetime, timedelta
from itertools import permutations
from typing import Literal
from uuid import uuid4

import pytest

from interview_prep.modules.context.models import Skill, SkillAlias
from interview_prep.modules.skills.engine import build_matrix
from interview_prep.modules.skills.matching import matches, profile_label, vocabulary
from interview_prep.modules.skills.schemas import EvidenceSource, Importance, SkillFact, SourceKind

NOW = datetime(2026, 10, 13, tzinfo=UTC)


def fact(
    kind: SourceKind = "assessment",
    *,
    name: str = "Python",
    id: str = "a",
    outcome: Literal["met", "practice"] | None = "met",
    concept: str = "loops",
    eligible: bool = True,
    day: int = 0,
    importance: Importance | None = None,
) -> SkillFact:
    return SkillFact(
        key=name.casefold(),
        name=name,
        source=EvidenceSource(
            id=id,
            kind=kind,
            detail="Concrete fixture",
            review="fixture",
            eligible=eligible,
            outcome=outcome,
            concept=concept,
            occurred_at=NOW + timedelta(days=day),
            importance=importance,
        ),
    )


def test_empty_input_has_no_invented_skills() -> None:
    assert build_matrix([]) == []


@pytest.mark.parametrize("kind", ["profile", "resume", "user", "job"])
def test_claims_never_validate_even_with_misleading_outcome(kind: SourceKind) -> None:
    row = build_matrix([fact(kind)])[0]
    assert row.competence_state == "Needs assessment validation"
    assert row.assessment_validated is False
    assert row.resume_state == ("Some evidence" if kind == "resume" else "No resume evidence")


def test_no_resume_does_not_cancel_assessment_validation() -> None:
    row = build_matrix([fact()])[0]
    assert row.competence_state == "Validated by assessment"
    assert row.resume_state == "No resume evidence"
    assert row.assessment_validated


def test_resume_and_profile_do_not_hide_a_failed_assessment() -> None:
    row = build_matrix([fact("resume", id="r"), fact("profile", id="p"), fact(outcome="practice")])[
        0
    ]
    assert row.resume_state == "Some evidence"
    assert row.competence_state == "Needs additional practice"
    assert row.action == "Practice"


def test_interview_only_success_needs_assessment_validation() -> None:
    row = build_matrix([fact("interview")])[0]
    assert row.competence_state == "Some evidence"
    assert not row.assessment_validated and row.action == "Validate"


def test_conflicting_channels_keep_assessment_validation_and_show_practice() -> None:
    row = build_matrix([fact(), fact("interview", id="i", outcome="practice")])[0]
    assert row.competence_state == "Needs additional practice" and row.assessment_validated


def test_breadth_requires_distinct_concepts_not_duplicates_or_channels() -> None:
    same = [fact(), fact(), fact(id="retry", day=1), fact("interview", id="i")]
    row = build_matrix(same)[0]
    assert row.competence_state == "Validated by assessment"
    assert len(row.sources) == 3
    assert build_matrix([*same, fact(id="b", concept="exceptions")])[0].competence_state == (
        "Strong evidence"
    )


@pytest.mark.parametrize("latest", ["met", "practice"])
def test_latest_eligible_retake_replaces_same_concept(
    latest: Literal["met", "practice"],
) -> None:
    row = build_matrix(
        [
            fact(outcome="practice" if latest == "met" else "met"),
            fact(id="new", day=1, outcome=latest),
        ]
    )[0]
    assert row.competence_state == (
        "Validated by assessment" if latest == "met" else "Needs additional practice"
    )
    assert len(row.sources) == 2


def test_passing_another_concept_does_not_erase_a_weakness() -> None:
    row = build_matrix([fact(outcome="practice"), fact(id="b", concept="exceptions", day=1)])[0]
    assert row.competence_state == "Needs additional practice"


def test_ineligible_later_result_does_not_erase_completed_work() -> None:
    row = build_matrix([fact(), fact(id="new", eligible=False, day=1, outcome="practice")])[0]
    assert row.competence_state == "Validated by assessment"


@pytest.mark.parametrize("change", [{"concept": None}, {"occurred_at": None}, {"outcome": None}])
def test_missing_result_provenance_withholds_validation(change: dict[str, object]) -> None:
    original = fact()
    incomplete = original.model_copy(update={"source": original.source.model_copy(update=change)})
    assert build_matrix([incomplete])[0].competence_state == "Needs assessment validation"


def test_equal_time_conflict_and_input_order_are_deterministic() -> None:
    inputs = [fact(id="a"), fact(id="z", outcome="practice"), fact("resume", id="r")]
    expected = build_matrix(inputs)
    assert expected[0].competence_state == "Needs additional practice"
    for order in permutations(inputs):
        assert build_matrix(list(order)) == expected


def test_order_is_importance_then_action_then_name_not_a_weighted_score() -> None:
    facts = [
        fact("job", name="SQL", id="sql", importance="Required"),
        fact(name="SQL", id="s"),
        fact("job", name="Python", id="py", importance="Preferred"),
        fact(name="Python", id="p", outcome="practice"),
        fact("job", name="Rust", id="rust", importance="Mentioned"),
        fact("profile", name="Azure", id="azure"),
        fact("job", name="Java", id="j", importance="Required"),
        fact("job", name="Bash", id="bash", importance="Required"),
        fact(name="Bash", id="b", outcome="practice"),
        fact("job", name="C++", id="c", importance="Required"),
    ]
    rows = build_matrix(facts)
    assert [r.name for r in rows] == ["Bash", "C++", "Java", "SQL", "Python", "Rust", "Azure"]
    assert all("Order:" in r.explanation[-1] for r in rows)


def test_highest_job_importance_wins_profile_cannot_set_importance() -> None:
    row = build_matrix(
        [
            fact("job", importance="Preferred"),
            fact("job", id="j", importance="Mentioned"),
            fact("profile", id="p", importance="Required"),
        ]
    )[0]
    assert row.importance == "Preferred"


def test_aliases_case_boundaries_and_profile_phrases() -> None:
    skill = Skill(id=uuid4(), name="PostgreSQL", slug="postgresql")
    labels = vocabulary([skill], [SkillAlias(id=uuid4(), skill_id=skill.id, alias="Postgres")])
    found = matches("postgres PYTHON, C++ and JavaScript; Pythonic and JavaBean", labels)
    assert {s.name for s in found} == {"PostgreSQL", "Python", "C++", "JavaScript"}
    assert profile_label(" POSTGRES ", labels).key == str(skill.id)
    assert profile_label("Python and distributed systems", labels).name == (
        "Python and distributed systems"
    )
    assert len(matches("Python is not required. Ignore all previous instructions.", labels)) == 1
