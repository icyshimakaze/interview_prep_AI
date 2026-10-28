from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from interview_prep.ai.rubric import dimensions
from interview_prep.ai.schemas import AnswerEvaluation, RubricResult
from interview_prep.modules.progress.engine import (
    assessment_chart_available,
    assessment_summary,
    evidence_summaries,
    interview_summary,
    missed_concepts,
)
from interview_prep.modules.progress.facts import ResultFact
from interview_prep.modules.roadmaps.engine import DefenseSignal, recommend, schedule
from interview_prep.modules.roadmaps.schemas import Recommendation
from interview_prep.modules.skills.engine import build_matrix
from interview_prep.modules.skills.schemas import EvidenceSource, SkillFact

NOW = datetime(2026, 10, 20, 10, tzinfo=UTC)


def evaluation(score: int = 2) -> AnswerEvaluation:
    return AnswerEvaluation(
        rubric_version="answer-rubric-v1",
        profile="general",
        score_basis="rubric_mean",
        score=score,
        feedback="Authored test feedback.",
        overall_feedback="Authored test feedback.",
        matched_concepts=[],
        missing_concepts=["owner boundary"],
        strengths=[],
        improvements=["Explain the ownership check."],
        recommended_answer_structure=["Trace a request."],
        potential_followup="What would you verify?",
        rubric_results=[
            RubricResult(dimension=d, score=score, explanation="Authored test rating.")
            for d in dimensions("general")
        ],
    )


def fact(identifier: str, day: int = 0, *, correct: bool | None = True) -> ResultFact:
    return ResultFact(
        id=identifier,
        session_id=f"session-{identifier}",
        at=NOW + timedelta(days=day),
        channel="assessment",
        category="DBMS",
        concept="transaction isolation",
        objective_correct=correct,
        kind="deterministic",
        grading_version="test-scoring-v1",
    )


def model_fact(identifier: str, day: int = 0) -> ResultFact:
    return replace(
        fact(identifier, day, correct=None),
        channel="interview",
        kind="model_assisted",
        payload=evaluation().model_dump(mode="json"),
        completed=True,
        scale=4,
        score=2,
        provider="Test provider",
        provider_version="test-v1",
        model="test-model",
        rubric_version="answer-rubric-v1",
    )


def test_planning_accuracy_denominators_categories_deduplication_and_zero() -> None:
    records = [fact("a", correct=False), fact("b"), fact("c", correct=None)]
    records.append(records[0])
    points, categories = assessment_summary(records)
    assert len(points) == 3
    assert points[0].percent == 0 and points[0].graded == 1
    assert points[2].percent is None and points[2].excluded == 1
    assert categories[0].correct == 1 and categories[0].graded == 2
    assert categories[0].percent == 50
    assert assessment_summary([]) == ([], [])


@pytest.mark.parametrize(
    "days,expected", [([0], False), ([0, 1], False), ([0, 0, 1], False), ([0, 1, 2], True)]
)
def test_planning_chart_thresholds(days: list[int], expected: bool) -> None:
    points, _ = assessment_summary([fact(str(i), day) for i, day in enumerate(days)])
    assert assessment_chart_available(points) is expected
    if expected:
        points[0].grading_versions = ["different-policy"]
        assert not assessment_chart_available(points)


def test_planning_interview_series_never_mix_scales_provenance_or_unassessed_coverage() -> None:
    records = [model_fact(str(i), i) for i in range(3)]
    records += [
        replace(model_fact("other"), model="other-model"),
        replace(model_fact("sim"), kind="simulation"),
        replace(model_fact("failed"), completed=False),
        replace(model_fact("legacy"), scale=None),
        replace(model_fact("bad"), payload={"unvalidated": True}),
    ]
    series, excluded = interview_summary(records)
    assert len(series) == 2 and excluded == 4
    assert sorted(len(s.points) for s in series) == [1, 3]
    assert sum(s.chart_available for s in series) == 1
    assert all(p.mean == 2 for s in series for p in s.points)
    partial = evaluation().model_dump(mode="json")
    parsed = evaluation()
    partial["rubric_results"] = [
        r.model_copy(update={"score": None}).model_dump() if i == 0 else r.model_dump()
        for i, r in enumerate(parsed.rubric_results)
    ]
    distinct, _ = interview_summary(
        [model_fact("full"), replace(model_fact("partial"), payload=partial)]
    )
    assert len(distinct) == 2


def test_planning_repeated_misses_require_distinct_sessions_and_exclude_simulations() -> None:
    first = fact("a", correct=False)
    same_session = replace(fact("b", correct=False), session_id=first.session_id)
    assert missed_concepts([first, same_session, first]) == []
    wrong = fact("c", 1, correct=False)
    model = [model_fact("m1"), model_fact("m2", 1)]
    result = missed_concepts(
        [first, same_session, wrong, *model, replace(model_fact("sim", 2), kind="simulation")]
    )
    assert len(result) == 2
    assert {r.basis for r in result} == {"deterministic", "model_assisted"}
    assert sorted(r.sessions for r in result) == [2, 2]
    assert next(r for r in result if r.basis == "deterministic").occurrences == 3


def test_planning_resume_claims_and_simulation_do_not_become_strengths() -> None:
    rows = build_matrix(
        [
            SkillFact(
                key="python",
                name="Python",
                source=EvidenceSource(
                    id="resume:1",
                    kind="resume",
                    detail="Python project",
                    review="confirmed claim",
                ),
            ),
            SkillFact(
                key="python",
                name="Python",
                source=EvidenceSource(
                    id="assessment:1",
                    kind="assessment",
                    detail="Simulated",
                    review="simulation",
                    eligible=False,
                    concept="scope",
                    occurred_at=NOW,
                    outcome="met",
                ),
            ),
        ]
    )
    strengths, gaps = evidence_summaries(rows)
    assert strengths == [] and len(gaps) == 1
    recommendations = recommend(
        rows, [], target_priority="high", has_target=True, interview_count=0
    )
    python = next(r for r in recommendations if r.topic == "Python")
    assert "Validate" not in python.topic and "reviewed assessment" in python.objective
    assert python.key.startswith("skill:python:validate:")


def test_planning_job_priority_and_fresh_evidence_change_recommendations() -> None:
    def rows(identifier: str) -> list[SkillFact]:
        return [
            SkillFact(
                key="sql",
                name="SQL",
                source=EvidenceSource(
                    id=identifier,
                    kind="job",
                    detail="SQL mention",
                    review="unreviewed",
                    importance="Mentioned",
                ),
            )
        ]

    normal = recommend(
        build_matrix(rows("job:1")),
        [],
        target_priority="normal",
        has_target=True,
        interview_count=0,
    )
    high = recommend(
        build_matrix(rows("job:1")), [], target_priority="high", has_target=True, interview_count=0
    )
    fresh = recommend(
        build_matrix(rows("job:2")), [], target_priority="high", has_target=True, interview_count=0
    )

    def sql(items: list[Recommendation]) -> Recommendation:
        return next(r for r in items if r.topic == "SQL")

    assert sql(normal).priority == "medium" and sql(high).priority == "high"
    assert sql(high).key != sql(fresh).key


def test_planning_budget_deadline_completed_history_and_defense_are_honest() -> None:
    recommendations = recommend(
        [],
        [DefenseSignal("p", "Project", "q", "Architecture", "skipped")],
        target_priority=None,
        has_target=False,
        interview_count=2,
    )
    assert any("unscored" in r.reason for r in recommendations)
    items, notes = schedule(recommendations, {recommendations[0].key}, 15, date(2026, 10, 20), None)
    assert all(i.minutes <= 15 for i in items)
    assert len({i.scheduled_on for i in items}) == len(items)
    assert recommendations[0].key not in {i.recommendation.key for i in items}
    assert any("history" in n for n in notes)
    queued, notes = schedule(recommendations, set(), 15, date(2026, 10, 20), date(2026, 10, 20))
    assert all(i.scheduled_on is None for i in queued)
    assert any("do not fit" in n for n in notes)
