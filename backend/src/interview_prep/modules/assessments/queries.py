from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.adaptive.schemas import Selection
from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentQuestionOption,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.assessments.schemas import (
    AttemptPage,
    AttemptSummary,
    AttemptView,
    CategoryPerformance,
    Configuration,
    EvaluationMetadata,
    Inventory,
    Options,
    PresentedOption,
    PresentedQuestion,
    Review,
)
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    PublicationStatus,
    QuestionOption,
    QuestionType,
    QuestionVersion,
    ShortAnswerKey,
)
from interview_prep.modules.questions.queries import visible_versions

SUPPORTED = (
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.MULTIPLE_SELECT,
    QuestionType.SHORT_ANSWER,
    QuestionType.WRITTEN,
)


def pool(owner: UUID, config: Configuration | None = None) -> Select[QuestionVersion]:
    query = visible_versions(owner).where(
        QuestionVersion.status == PublicationStatus.PUBLISHED,
        QuestionVersion.question_type.in_(SUPPORTED),
    )
    if config:
        query = query.where(QuestionVersion.question_type.in_(config.question_types))
        if config.category:
            query = query.where(QuestionVersion.category == config.category)
        if config.difficulty:
            query = query.where(QuestionVersion.difficulty == config.difficulty)
    return query


async def options(session: AsyncSession, owner: UUID) -> Options:
    available = pool(owner).subquery()
    rows = (
        await session.execute(
            select(
                available.c.category,
                available.c.difficulty,
                available.c.question_type,
                func.count(),
            )
            .group_by(available.c.category, available.c.difficulty, available.c.question_type)
            .order_by(available.c.category, available.c.difficulty, available.c.question_type)
        )
    ).all()
    return Options(
        inventory=[
            Inventory(category=c, difficulty=d, question_type=t, count=n) for c, d, t, n in rows
        ]
    )


async def owned_attempt(
    session: AsyncSession, owner: UUID, identifier: UUID, *, lock: bool = False
) -> AssessmentAttempt:
    query = select(AssessmentAttempt).where(
        AssessmentAttempt.id == identifier, AssessmentAttempt.owner_id == owner
    )
    if lock:
        query = query.with_for_update()
    attempt = await session.scalar(query)
    if attempt is None:
        raise HTTPException(status_code=404)
    return attempt


def effective_status(attempt: AssessmentAttempt) -> str:
    if (
        attempt.status == AttemptStatus.IN_PROGRESS
        and attempt.deadline_at
        and attempt.deadline_at <= datetime.now(UTC)
    ):
        return "expired"
    return str(attempt.status)


async def summary(session: AsyncSession, owner: UUID, attempt: AssessmentAttempt) -> AttemptSummary:
    assessment = await session.scalar(
        select(Assessment).where(
            Assessment.id == attempt.assessment_id, Assessment.owner_id == owner
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404)
    total = (
        await session.scalar(
            select(func.count())
            .select_from(AssessmentQuestion)
            .where(
                AssessmentQuestion.owner_id == owner,
                AssessmentQuestion.assessment_id == assessment.id,
            )
        )
        or 0
    )
    answers = (
        await session.scalars(
            select(QuestionAttempt).where(
                QuestionAttempt.owner_id == owner,
                QuestionAttempt.assessment_attempt_id == attempt.id,
            )
        )
    ).all()
    return AttemptSummary(
        id=attempt.id,
        title=assessment.title,
        status=effective_status(attempt),
        revision=attempt.revision,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        deadline_at=attempt.deadline_at,
        question_count=total,
        answered=sum(
            bool(a.answer_text or a.selected_option_id or a.selected_option_ids) for a in answers
        ),
        simulated=any(a.result_kind == "simulation" for a in answers),
    )


async def read(session: AsyncSession, owner: UUID, identifier: UUID) -> AttemptView:
    attempt = await owned_attempt(session, owner, identifier)
    assessment = await session.scalar(
        select(Assessment).where(
            Assessment.id == attempt.assessment_id, Assessment.owner_id == owner
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404)
    rows = (
        await session.execute(
            select(AssessmentQuestion, QuestionVersion)
            .join(QuestionVersion, QuestionVersion.id == AssessmentQuestion.question_version_id)
            .where(
                AssessmentQuestion.assessment_id == assessment.id,
                AssessmentQuestion.owner_id == owner,
            )
            .order_by(AssessmentQuestion.position)
        )
    ).all()
    answers = {
        a.assessment_question_id: a
        for a in (
            await session.scalars(
                select(QuestionAttempt).where(
                    QuestionAttempt.assessment_attempt_id == identifier,
                    QuestionAttempt.owner_id == owner,
                )
            )
        ).all()
    }
    questions: list[PresentedQuestion] = []
    completed = attempt.status == AttemptStatus.COMPLETED
    for allocation, version in rows:
        answer = answers.get(allocation.id)
        options_rows = (
            await session.scalars(
                select(QuestionOption)
                .join(
                    AssessmentQuestionOption,
                    AssessmentQuestionOption.option_id == QuestionOption.id,
                )
                .where(
                    AssessmentQuestionOption.assessment_question_id == allocation.id,
                    AssessmentQuestionOption.owner_id == owner,
                )
                .order_by(AssessmentQuestionOption.position)
            )
        ).all()
        review = None
        if completed:
            concepts = list(
                (
                    await session.scalars(
                        select(ExpectedConcept.text)
                        .where(ExpectedConcept.question_version_id == version.id)
                        .order_by(ExpectedConcept.position)
                    )
                ).all()
            )
            keys = list(
                (
                    await session.scalars(
                        select(ShortAnswerKey.normalized_answer).where(
                            ShortAnswerKey.question_version_id == version.id
                        )
                    )
                ).all()
            )
            review = Review(
                score=answer.score if answer else None,
                max_score=answer.max_score if answer else None,
                is_correct=answer.is_correct if answer else None,
                result_kind=answer.result_kind if answer else None,
                feedback=answer.feedback if answer else None,
                metadata=EvaluationMetadata.model_validate(answer.evaluation_metadata)
                if answer and answer.evaluation_metadata
                else None,
                expected_concepts=concepts,
                correct_option_ids=[o.id for o in options_rows if o.is_correct],
                accepted_answers=keys,
            )
        questions.append(
            PresentedQuestion(
                id=allocation.id,
                question_version_id=version.id,
                position=allocation.position,
                title=version.title,
                prompt=version.prompt or "",
                category=version.category or "Uncategorized",
                difficulty=version.difficulty,
                question_type=version.question_type or QuestionType.WRITTEN,
                options=[PresentedOption(id=o.id, text=o.text) for o in options_rows],
                answer_text=answer.answer_text if answer else None,
                selected_option_ids=(
                    answer.selected_option_ids
                    or ([answer.selected_option_id] if answer.selected_option_id else [])
                )
                if answer
                else [],
                saved_at=answer.updated_at if answer else None,
                skipped=answer.status == AnswerStatus.SKIPPED if answer else False,
                review=review,
            )
        )
    return AttemptView(
        **(await summary(session, owner, attempt)).model_dump(),
        selection=Selection.model_validate(assessment.configuration["selection"])
        if assessment.configuration and "selection" in assessment.configuration
        else None,
        configuration=Configuration.model_validate(
            {key: value for key, value in assessment.configuration.items() if key != "selection"}
        )
        if assessment.configuration
        else None,
        questions=questions,
        categories=category_performance(questions) if completed else [],
    )


def category_performance(questions: list[PresentedQuestion]) -> list[CategoryPerformance]:
    result: list[CategoryPerformance] = []
    for category in sorted({q.category for q in questions}):
        items = [q for q in questions if q.category == category]
        objective = [
            q
            for q in items
            if q.question_type != QuestionType.WRITTEN
            and (q.skipped or q.review and q.review.result_kind == "deterministic")
        ]
        conceptual = [
            q.review
            for q in items
            if q.question_type == QuestionType.WRITTEN and q.review and q.review.score is not None
        ]
        kinds = {r.result_kind for r in conceptual}
        result.append(
            CategoryPerformance(
                category=category,
                questions=len(items),
                answered=sum(bool(q.answer_text or q.selected_option_ids) for q in items),
                skipped=sum(q.skipped for q in items),
                objective_correct=sum(bool(q.review and q.review.is_correct) for q in objective),
                objective_total=len(objective),
                conceptual_score=sum(r.score or 0 for r in conceptual),
                conceptual_max=sum(r.max_score or 0 for r in conceptual),
                conceptual_kind=next(iter(kinds))
                if len(kinds) == 1
                else "mixed"
                if kinds
                else None,
            )
        )
    return result


async def history(session: AsyncSession, owner: UUID, offset: int, limit: int) -> AttemptPage:
    query = select(AssessmentAttempt).where(AssessmentAttempt.owner_id == owner)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    attempts = (
        await session.scalars(
            query.order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return AttemptPage(
        items=[await summary(session, owner, a) for a in attempts],
        total=total,
        offset=offset,
        limit=limit,
    )
