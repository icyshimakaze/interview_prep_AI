from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.adaptive.service import allocate
from interview_prep.modules.assessments import queries
from interview_prep.modules.assessments.evaluation import POLICY_VERSION, EvaluationProvider
from interview_prep.modules.assessments.grading import grade
from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentQuestionOption,
    AssessmentStatus,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.assessments.schemas import (
    AttemptView,
    Configuration,
    ResponseInput,
    StartInput,
)
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import EvaluationKind
from interview_prep.modules.questions.models import QuestionOption, QuestionType, QuestionVersion
from interview_prep.modules.roadmaps.models import ProgressEvent, ProgressEventType

MAX_ATTEMPTS = 100
MAX_UNFINISHED = 5


async def start(session: AsyncSession, owner: UUID, body: StartInput) -> AttemptView:
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    config = Configuration.model_validate(body.model_dump(exclude={"submission_key"})).model_dump(
        mode="json"
    )
    existing = await session.scalar(
        select(AssessmentAttempt).where(
            AssessmentAttempt.owner_id == owner,
            AssessmentAttempt.submission_key == body.submission_key,
        )
    )
    if existing:
        assessment = await session.scalar(
            select(Assessment).where(
                Assessment.id == existing.assessment_id, Assessment.owner_id == owner
            )
        )
        stored = (
            {
                key: value
                for key, value in (assessment.configuration or {}).items()
                if key != "selection"
            }
            if assessment
            else {}
        )
        if (
            assessment is None
            or assessment.configuration is None
            or Configuration.model_validate(stored).model_dump(mode="json") != config
        ):
            raise HTTPException(status_code=409, detail="submission_conflict")
        return await queries.read(session, owner, existing.id)
    attempts = (
        await session.scalars(select(AssessmentAttempt).where(AssessmentAttempt.owner_id == owner))
    ).all()
    if (
        len(attempts) >= MAX_ATTEMPTS
        or sum(queries.effective_status(a) == "in_progress" for a in attempts) >= MAX_UNFINISHED
    ):
        raise HTTPException(status_code=409, detail="assessment_limit")
    versions, selection = await allocate(session, owner, body, str(body.submission_key))
    if len(versions) != body.question_count:
        raise HTTPException(status_code=409, detail="assessment_pool")
    assessment = Assessment(
        owner_id=owner,
        title=f"{body.category or 'Mixed topics'} assessment",
        status=AssessmentStatus.READY,
        context_version="adaptive-v1",
        policy_version=POLICY_VERSION,
        configuration={**config, "selection": selection.model_dump(mode="json")},
    )
    session.add(assessment)
    await session.flush()
    for index, version in enumerate(versions, 1):
        allocation = AssessmentQuestion(
            owner_id=owner,
            assessment_id=assessment.id,
            question_version_id=version.id,
            position=index,
            option_order_version="authored-order-v1",
        )
        session.add(allocation)
        await session.flush()
        options = (
            await session.scalars(
                select(QuestionOption)
                .where(QuestionOption.question_version_id == version.id)
                .order_by(QuestionOption.position)
            )
        ).all()
        session.add_all(
            [
                AssessmentQuestionOption(
                    owner_id=owner,
                    assessment_question_id=allocation.id,
                    question_version_id=version.id,
                    option_id=option.id,
                    position=position,
                )
                for position, option in enumerate(options, 1)
            ]
        )
    await session.flush()  # Freeze allocations only after every presented option is stored.
    now = datetime.now(UTC)
    attempt = AssessmentAttempt(
        owner_id=owner,
        assessment_id=assessment.id,
        attempt_number=1,
        submission_key=body.submission_key,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now,
        deadline_at=now + timedelta(hours=24),
    )
    session.add(attempt)
    await session.commit()
    return await queries.read(session, owner, attempt.id)


def require_editable(attempt: AssessmentAttempt, revision: int) -> None:
    status = queries.effective_status(attempt)
    if status == "expired":
        raise HTTPException(status_code=409, detail="assessment_expired")
    if status != "in_progress":
        raise HTTPException(status_code=409, detail="assessment_closed")
    if attempt.revision != revision:
        raise HTTPException(status_code=409, detail="assessment_revision")


async def save(
    session: AsyncSession, owner: UUID, identifier: UUID, question_id: UUID, body: ResponseInput
) -> AttemptView:
    attempt = await queries.owned_attempt(session, owner, identifier, lock=True)
    require_editable(attempt, body.revision)
    row = (
        await session.execute(
            select(AssessmentQuestion, QuestionVersion)
            .join(QuestionVersion, QuestionVersion.id == AssessmentQuestion.question_version_id)
            .where(
                AssessmentQuestion.id == question_id,
                AssessmentQuestion.owner_id == owner,
                AssessmentQuestion.assessment_id == attempt.assessment_id,
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404)
    allocation, version = row
    if version.question_type not in queries.SUPPORTED:
        raise HTTPException(status_code=409, detail="assessment_closed")
    text = body.answer_text.strip() if body.answer_text and body.answer_text.strip() else None
    if version.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT):
        available = set(
            (
                await session.scalars(
                    select(AssessmentQuestionOption.option_id).where(
                        AssessmentQuestionOption.owner_id == owner,
                        AssessmentQuestionOption.assessment_question_id == question_id,
                    )
                )
            ).all()
        )
        if (
            text
            or not set(body.selected_option_ids).issubset(available)
            or (
                version.question_type == QuestionType.MULTIPLE_CHOICE
                and len(body.selected_option_ids) > 1
            )
        ):
            raise HTTPException(status_code=422)
    elif body.selected_option_ids:
        raise HTTPException(status_code=422)
    answer = await session.scalar(
        select(QuestionAttempt).where(
            QuestionAttempt.owner_id == owner,
            QuestionAttempt.assessment_attempt_id == identifier,
            QuestionAttempt.assessment_question_id == question_id,
        )
    )
    if answer is None:
        answer = QuestionAttempt(
            owner_id=owner,
            assessment_id=attempt.assessment_id,
            assessment_attempt_id=identifier,
            assessment_question_id=allocation.id,
            status=AnswerStatus.DRAFT,
        )
        session.add(answer)
    answer.answer_text, answer.selected_option_ids = text, body.selected_option_ids
    answer.selected_option_id = None
    attempt.revision += 1
    await session.commit()
    return await queries.read(session, owner, identifier)


async def submit(
    session: AsyncSession,
    owner: UUID,
    identifier: UUID,
    revision: int,
    provider: EvaluationProvider,
) -> AttemptView:
    attempt = await queries.owned_attempt(session, owner, identifier, lock=True)
    if attempt.status == AttemptStatus.COMPLETED:
        return await queries.read(
            session, owner, identifier
        )  # Lost responses and concurrent retries are safe.
    require_editable(attempt, revision)
    rows = (
        await session.execute(
            select(AssessmentQuestion, QuestionVersion)
            .join(QuestionVersion, QuestionVersion.id == AssessmentQuestion.question_version_id)
            .where(
                AssessmentQuestion.assessment_id == attempt.assessment_id,
                AssessmentQuestion.owner_id == owner,
            )
            .order_by(AssessmentQuestion.position)
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=409, detail="assessment_closed")
    answers = {
        a.assessment_question_id: a
        for a in (
            await session.scalars(
                select(QuestionAttempt).where(
                    QuestionAttempt.owner_id == owner,
                    QuestionAttempt.assessment_attempt_id == identifier,
                )
            )
        ).all()
    }
    # Avoid autoflush of terminal rows while the rest of the attempt is still being evaluated.
    with session.no_autoflush:
        for allocation, version in rows:
            answer = answers.get(allocation.id)
            if answer is None:
                answer = QuestionAttempt(
                    owner_id=owner,
                    assessment_id=attempt.assessment_id,
                    assessment_attempt_id=identifier,
                    assessment_question_id=allocation.id,
                    status=AnswerStatus.DRAFT,
                    selected_option_ids=[],
                )
                session.add(answer)
            await grade(session, answer, version, provider)
        if attempt.deadline_at and datetime.now(UTC) >= attempt.deadline_at:
            raise HTTPException(status_code=409, detail="assessment_expired")
        attempt.status, attempt.completed_at = AttemptStatus.COMPLETED, datetime.now(UTC)
        attempt.revision += 1
        kinds = {a.result_kind for a in answers.values() if a.result_kind}
        event_kind = (
            EvaluationKind.SIMULATION
            if "simulation" in kinds
            else EvaluationKind.MODEL_ASSISTED
            if "model_assisted" in kinds
            else EvaluationKind.DETERMINISTIC
        )
        session.add(
            ProgressEvent(
                owner_id=owner,
                event_type=ProgressEventType.ASSESSMENT_COMPLETED,
                assessment_attempt_id=identifier,
                result_kind=event_kind,
                deduplication_key=identifier,
                occurred_at=attempt.completed_at,
            )
        )
    await session.commit()
    return await queries.read(session, owner, identifier)


async def abandon(
    session: AsyncSession, owner: UUID, identifier: UUID, revision: int
) -> AttemptView:
    attempt = await queries.owned_attempt(session, owner, identifier, lock=True)
    if attempt.status == AttemptStatus.ABANDONED:
        return await queries.read(session, owner, identifier)
    # Expired attempts can be explicitly abandoned, but never submitted or edited.
    if attempt.status != AttemptStatus.IN_PROGRESS or attempt.revision != revision:
        raise HTTPException(status_code=409, detail="assessment_closed")
    attempt.status, attempt.revision = AttemptStatus.ABANDONED, attempt.revision + 1
    await session.commit()
    return await queries.read(session, owner, identifier)
