import asyncio
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.assessments.evaluation import (
    POLICY_VERSION,
    ConceptualInput,
    EvaluationProvider,
    ProviderEvaluationAdapter,
    validate_evaluation,
)
from interview_prep.modules.assessments.models import AnswerStatus, QuestionAttempt
from interview_prep.modules.assessments.schemas import EvaluationMetadata
from interview_prep.modules.assessments.scoring import score_options, score_short_answer
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    QuestionOption,
    QuestionRubricCriterion,
    QuestionType,
    QuestionVersion,
    ShortAnswerKey,
)


async def grade(
    session: AsyncSession,
    answer: QuestionAttempt,
    version: QuestionVersion,
    provider: EvaluationProvider,
) -> None:
    if not (answer.answer_text or answer.selected_option_ids or answer.selected_option_id):
        answer.status = AnswerStatus.SKIPPED
        return
    selected = answer.selected_option_ids or (
        [answer.selected_option_id] if answer.selected_option_id else []
    )
    matched: list[str] = []
    model: str | None = None
    prompt_version: str | None = None
    provider_name, provider_version = "deterministic", POLICY_VERSION
    if version.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT):
        correct = list(
            (
                await session.scalars(
                    select(QuestionOption.id).where(
                        QuestionOption.question_version_id == version.id,
                        QuestionOption.is_correct.is_(True),
                    )
                )
            ).all()
        )
        answer.score = score_options(selected, correct)
        answer.max_score = 1
    elif version.question_type == QuestionType.SHORT_ANSWER:
        keys = (
            await session.execute(
                select(
                    ShortAnswerKey.normalized_answer, ShortAnswerKey.normalization_version
                ).where(ShortAnswerKey.question_version_id == version.id)
            )
        ).all()
        try:
            answer.score = score_short_answer(answer.answer_text or "", [(a, v) for a, v in keys])
        except ValueError:
            raise HTTPException(status_code=503) from None
        answer.max_score = 1
    elif version.question_type == QuestionType.WRITTEN:
        concepts = list(
            (
                await session.scalars(
                    select(ExpectedConcept.text)
                    .where(ExpectedConcept.question_version_id == version.id)
                    .order_by(ExpectedConcept.position)
                )
            ).all()
        )
        rubric = tuple(
            (
                await session.scalars(
                    select(QuestionRubricCriterion.description)
                    .where(QuestionRubricCriterion.question_version_id == version.id)
                    .order_by(QuestionRubricCriterion.code)
                )
            ).all()
        )
        try:
            deadline = (
                provider.timeout_seconds if isinstance(provider, ProviderEvaluationAdapter) else 5
            )
            async with asyncio.timeout(deadline):
                raw = await provider.evaluate(
                    ConceptualInput(
                        prompt=version.prompt or "",
                        response=answer.answer_text or "",
                        expected_concepts=tuple(concepts),
                        rubric=rubric,
                    )
                )
            evaluated = validate_evaluation(raw, provider, concepts)
        except Exception:
            # Never persist partial grades or leak provider payloads/errors.
            raise HTTPException(status_code=503, detail="assessment_evaluation") from None
        answer.score, answer.max_score = evaluated.score, 4
        answer.result_kind, answer.feedback = evaluated.kind, evaluated.feedback
        provider_name, provider_version = provider.name, provider.version
        matched = evaluated.matched_concepts
        if isinstance(provider, ProviderEvaluationAdapter):
            model, prompt_version = provider.model, "ai-prompts-v1"
    else:
        raise HTTPException(status_code=409, detail="assessment_closed")
    now = datetime.now(UTC)
    answer.status = AnswerStatus.SUBMITTED
    answer.submitted_at = now
    answer.grading_version = POLICY_VERSION
    if version.question_type != QuestionType.WRITTEN:
        answer.result_kind = "deterministic"
        answer.is_correct = answer.score == 1
        answer.feedback = (
            "Correct."
            if answer.is_correct
            else "Review the expected answer and try a fresh assessment."
        )
    answer.evaluation_metadata = EvaluationMetadata(
        model=model,
        prompt_version=prompt_version,
        provider=provider_name,
        provider_version=provider_version,
        policy_version=POLICY_VERSION,
        rubric_version=version.rubric_version,
        evaluated_at=now,
        matched_concepts=matched,
    ).model_dump(mode="json")
