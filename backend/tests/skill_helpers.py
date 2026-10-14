"""Authored test records created through the real immutable-content lifecycle."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentStatus,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.context.models import Skill
from interview_prep.modules.identity.models import PrincipalKind, User
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationDimension,
    EvaluationKind,
    EvaluationStatus,
    InterviewAnswer,
    InterviewMode,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.questions.models import (
    Difficulty,
    PublicationStatus,
    Question,
    QuestionRubricCriterion,
    QuestionSkill,
    QuestionType,
    QuestionVersion,
    QuestionVisibility,
    ShortAnswerKey,
)


async def prepare(
    engine: AsyncEngine,
    problem: str = "",
    score: int = 4,
    assessment_kind: str = "deterministic",
    demo: bool = False,
) -> UUID:
    now = datetime.now(UTC)
    async with async_sessionmaker(engine)() as session, session.begin():
        user = User(
            kind=PrincipalKind.DEMO if demo else PrincipalKind.ACCOUNT,
            expires_at=now + timedelta(days=1) if demo else None,
            issuer=None if demo else "test",
            subject=None if demo else "evidence-test",
        )
        skill, extra = Skill(name="Python", slug="python"), Skill(name="SQL", slug="sql")
        session.add_all([user, skill, extra])
        await session.flush()
        owner = user.id
        versions: list[QuestionVersion] = []
        criterion: QuestionRubricCriterion | None = None
        for index in range(3):
            question = Question(
                owner_id=owner,
                visibility=QuestionVisibility.PRIVATE,
                canonical_concept=f"fixture/concept-{index}",
            )
            session.add(question)
            await session.flush()
            version = QuestionVersion(
                question_id=question.id,
                version=1,
                title=f"Concept {index}",
                prompt="Explain the tested concept.",
                question_type=QuestionType.SHORT_ANSWER if index < 2 else QuestionType.WRITTEN,
                difficulty=Difficulty.EASY,
                status=PublicationStatus.DRAFT,
                provenance_reviewed=True,
                source_license="CC0-1.0",
                rubric_version="rubric-v1",
            )
            session.add(version)
            await session.flush()
            session.add(QuestionSkill(question_version_id=version.id, skill_id=skill.id))
            if problem == "multi_skill":
                session.add(QuestionSkill(question_version_id=version.id, skill_id=extra.id))
            if index < 2:
                session.add(
                    ShortAnswerKey(
                        question_version_id=version.id,
                        normalized_answer="answer",
                        normalization_version="literal-v1",
                    )
                )
            else:
                criterion = QuestionRubricCriterion(
                    question_version_id=version.id,
                    code="ownership",
                    description="Explain owner scoping",
                    weight=1,
                    anchor_0="No check",
                    anchor_1="Login only",
                    anchor_2="Check owner",
                    anchor_3="Scope queries",
                    anchor_4="Scope queries and test isolation",
                )
                session.add(criterion)
            await session.flush()
            version.status = PublicationStatus.PUBLISHED
            await session.flush()
            versions.append(version)
        assessment = Assessment(
            owner_id=owner,
            title="Test assessment",
            status=AssessmentStatus.READY,
            context_version="test-v1",
            policy_version="test-v1",
        )
        session.add(assessment)
        await session.flush()
        allocations = [
            AssessmentQuestion(
                owner_id=owner,
                assessment_id=assessment.id,
                question_version_id=v.id,
                position=index + 1,
            )
            for index, v in enumerate(versions[:2])
        ]
        session.add_all(allocations)
        await session.flush()
        for index in range(2):
            completed = now - timedelta(days=3 - index)
            attempt = AssessmentAttempt(
                owner_id=owner,
                assessment_id=assessment.id,
                attempt_number=index + 1,
                submission_key=uuid4(),
                status=AttemptStatus.IN_PROGRESS
                if problem == "incomplete"
                else AttemptStatus.COMPLETED,
                started_at=completed - timedelta(minutes=10),
                completed_at=None if problem == "incomplete" else completed,
            )
            session.add(attempt)
            await session.flush()
            for position, allocation in enumerate(allocations):
                session.add(
                    QuestionAttempt(
                        owner_id=owner,
                        assessment_id=assessment.id,
                        assessment_attempt_id=attempt.id,
                        assessment_question_id=allocation.id,
                        status=AnswerStatus.SUBMITTED,
                        answer_text="answer",
                        submitted_at=completed,
                        is_correct=None if problem == "ungraded" else index == 1 or position == 0,
                        result_kind=assessment_kind,
                        grading_version=None if problem == "ungraded" else "literal-v1",
                    )
                )
        active = problem == "active"
        interview = InterviewSession(
            owner_id=owner,
            mode=InterviewMode.MOCK_INTERVIEW,
            status=SessionStatus.ACTIVE if active else SessionStatus.COMPLETED,
            context_version="test-v1",
            policy_version="test-v1",
            provider="test",
            main_question_limit=1,
            started_at=now - timedelta(minutes=10),
            completed_at=None if active else now,
        )
        session.add(interview)
        await session.flush()
        turn = InterviewQuestion(
            owner_id=owner,
            session_id=interview.id,
            question_version_id=versions[2].id,
            sequence=1,
            status=TurnStatus.EVALUATED,
        )
        session.add(turn)
        await session.flush()
        answer = InterviewAnswer(
            owner_id=owner,
            interview_question_id=turn.id,
            answer_text="Scope every query by verified owner.",
            status=AnswerStatus.SUBMITTED,
            submitted_at=now,
        )
        session.add(answer)
        await session.flush()
        kind = (
            EvaluationKind(problem)
            if problem in ("simulation", "self_review", "model_assisted")
            else EvaluationKind.DETERMINISTIC
        )
        if problem in ("multi_skill", "incomplete", "ungraded"):
            kind = EvaluationKind.SIMULATION
        evaluation = AnswerEvaluation(
            owner_id=owner,
            interview_answer_id=answer.id,
            version=1,
            kind=kind,
            status=EvaluationStatus.PENDING,
            evaluator_version="test-v1",
            rubric_version="wrong-version" if problem == "rubric" else "rubric-v1",
            provider="test" if kind == EvaluationKind.MODEL_ASSISTED else None,
            model="test" if kind == EvaluationKind.MODEL_ASSISTED else None,
        )
        session.add(evaluation)
        await session.flush()
        assert criterion
        if problem != "missing":
            session.add(
                EvaluationDimension(
                    owner_id=owner,
                    evaluation_id=evaluation.id,
                    criterion_id=criterion.id,
                    score=None if problem == "not_evaluable" else score,
                    not_evaluable=problem == "not_evaluable",
                    feedback="Authored fixture",
                )
            )
        await session.flush()
        evaluation.status = (
            EvaluationStatus.FAILED if problem == "failed" else EvaluationStatus.COMPLETED
        )
        return owner
