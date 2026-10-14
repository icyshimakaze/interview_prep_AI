from uuid import UUID

import pytest
from relational_helpers import fictional_owner
from skill_helpers import prepare
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from interview_prep.modules.context.models import Skill
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationKind,
    EvaluationStatus,
)
from interview_prep.modules.questions.models import PublicationStatus, QuestionVersion
from interview_prep.modules.skills.engine import build_matrix
from interview_prep.modules.skills.matching import vocabulary
from interview_prep.modules.skills.performance import performance_facts
from interview_prep.modules.skills.schemas import SkillRow
from interview_prep.modules.skills.service import skill_matrix


async def rows(session: AsyncSession, owner: UUID) -> list[SkillRow]:
    skills = list((await session.scalars(select(Skill))).all())
    notices: list[str] = []
    result = build_matrix(await performance_facts(session, owner, vocabulary(skills, []), notices))
    assert not notices
    return result


@pytest.mark.parametrize("demo", [False, True])
async def test_real_adapters_retake_breadth_and_demo_guard(
    database: AsyncEngine, demo: bool
) -> None:
    owner = await prepare(database, demo=demo)
    async with async_sessionmaker(database)() as session:
        result = await rows(session, owner)
        assert result[0].competence_state == "Strong evidence"
        assert result[0].assessment_validated and len(result[0].sources) == 5
        user = await session.get(User, owner)
        assert user
        matrix = await skill_matrix(session, user, None)
        assert matrix.rows[0].assessment_validated is not demo
        assert matrix.rows[0].competence_state == (
            "Needs assessment validation" if demo else "Strong evidence"
        )


@pytest.mark.parametrize("kind", ["simulation", "self_review"])
async def test_non_deterministic_assessments_do_not_validate(
    database: AsyncEngine, kind: str
) -> None:
    owner = await prepare(database, assessment_kind=kind)
    async with async_sessionmaker(database)() as session:
        result = await rows(session, owner)
        assert result[0].competence_state == "Some evidence"
        assert not result[0].assessment_validated


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "Needs additional practice"),
        (2, "Needs additional practice"),
        (3, "Strong evidence"),
        (4, "Strong evidence"),
    ],
)
async def test_interview_anchor_threshold_conflicts_with_successful_assessments(
    database: AsyncEngine,
    score: int,
    expected: str,
) -> None:
    owner = await prepare(database, score=score)
    async with async_sessionmaker(database)() as session:
        result = await rows(session, owner)
        assert result[0].competence_state == expected
        assert result[0].assessment_validated


@pytest.mark.parametrize(
    "problem",
    [
        "missing",
        "not_evaluable",
        "rubric",
        "failed",
        "active",
        "simulation",
        "self_review",
        "model_assisted",
    ],
)
async def test_incomplete_or_untrusted_interview_does_not_establish_weakness(
    database: AsyncEngine,
    problem: str,
) -> None:
    owner = await prepare(database, problem=problem, score=0)
    async with async_sessionmaker(database)() as session:
        result = await rows(session, owner)
        assert result[0].competence_state == "Strong evidence"
        assert not next(s for s in result[0].sources if s.kind == "interview").eligible


async def test_latest_failed_evaluation_does_not_resurrect_previous_grade(
    database: AsyncEngine,
) -> None:
    owner = await prepare(database)
    async with async_sessionmaker(database)() as session, session.begin():
        evaluation = await session.scalar(select(AnswerEvaluation))
        assert evaluation
        session.add(
            AnswerEvaluation(
                owner_id=owner,
                interview_answer_id=evaluation.interview_answer_id,
                version=2,
                supersedes_id=evaluation.id,
                kind=EvaluationKind.DETERMINISTIC,
                status=EvaluationStatus.FAILED,
                evaluator_version="fixture-v2",
                rubric_version=evaluation.rubric_version,
            )
        )
        await session.flush()
        result = await rows(session, owner)
        interviews = [s for s in result[0].sources if s.kind == "interview"]
        assert len(interviews) == 1 and not interviews[0].eligible
        assert "evaluation version 2" in interviews[0].detail


@pytest.mark.parametrize("problem", ["multi_skill", "incomplete", "ungraded"])
async def test_invalid_question_or_attempt_cannot_validate(
    database: AsyncEngine, problem: str
) -> None:
    owner = await prepare(database, problem=problem)
    async with async_sessionmaker(database)() as session:
        assert all(
            row.competence_state == "Needs assessment validation"
            for row in await rows(session, owner)
        )


@pytest.mark.parametrize("problem", ["draft", "unreviewed"])
async def test_defensive_content_checks_on_in_memory_invalid_snapshot(
    database: AsyncEngine,
    problem: str,
) -> None:
    owner = await prepare(database)
    async with async_sessionmaker(database)() as session:
        versions = list((await session.scalars(select(QuestionVersion))).all())
        # DB already prohibits such corruption. Test adapter defense without
        # writing invalid data or disabling any database protection.
        with session.no_autoflush:
            for version in versions:
                if problem == "draft":
                    version.status = PublicationStatus.DRAFT
                else:
                    version.provenance_reviewed = False
            assert all(
                row.competence_state == "Needs assessment validation"
                for row in await rows(session, owner)
            )
        await session.rollback()


async def test_private_performance_cannot_cross_owners(database: AsyncEngine) -> None:
    owner = await prepare(database)
    other = await fictional_owner(database)
    async with async_sessionmaker(database)() as session:
        assert await rows(session, other) == []
        assert (await rows(session, owner))[0].assessment_validated


async def test_overflow_discloses_partial_data_and_withholds_validation(
    database: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = await prepare(database)
    monkeypatch.setattr("interview_prep.modules.skills.performance.INPUT_LIMIT", 1)
    monkeypatch.setattr("interview_prep.modules.skills.context.INPUT_LIMIT", 1)
    async with async_sessionmaker(database)() as session:
        user = await session.get(User, owner)
        assert user
        matrix = await skill_matrix(session, user, None)
        assert any("partial" in note for note in matrix.notices)
        assert any("withheld" in note for note in matrix.notices)
        assert all(not s.eligible for r in matrix.rows for s in r.sources)
