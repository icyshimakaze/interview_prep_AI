"""Cache validated paid results across grading rollback; fence ambiguous dispatch."""

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.ai.rubric import EVALUATION_PROMPT_VERSION
from interview_prep.ai.schemas import AnswerEvaluation, AnswerInput
from interview_prep.ai.validation import validate_domain
from interview_prep.core.config import Settings, get_settings
from interview_prep.core.quotas import reserve
from interview_prep.core.security_models import EvaluationReceipt
from interview_prep.modules.assessments.evaluation import (
    ConceptualEvaluation,
    ConceptualInput,
    EvaluationProvider,
    ProviderEvaluationAdapter,
    validate_evaluation,
)
from interview_prep.modules.assessments.models import QuestionAttempt


async def evaluate(
    session: AsyncSession,
    answer: QuestionAttempt,
    provider: EvaluationProvider,
    content: ConceptualInput,
) -> object:
    if provider.kind == "simulation":
        return await provider.evaluate(content)
    material = json.dumps(
        [
            str(answer.assessment_attempt_id),
            str(answer.assessment_question_id),
            asdict(content),
            provider.name,
            provider.version,
            provider.model if isinstance(provider, ProviderEvaluationAdapter) else None,
            EVALUATION_PROMPT_VERSION,
        ],
        sort_keys=True,
    )
    key = hashlib.sha256(material.encode()).hexdigest()
    factory = async_sessionmaker(session.bind, expire_on_commit=False)
    settings = session.info.get("settings")
    if not isinstance(settings, Settings):
        settings = get_settings()
    async with factory() as independent:
        created = await independent.scalar(
            insert(EvaluationReceipt)
            .values(
                owner_id=answer.owner_id,
                input_key=key,
                attempts=1,
                state="started",
                result=None,
                expires_at=datetime.now(UTC) + timedelta(days=2),
            )
            .on_conflict_do_nothing()
            .returning(EvaluationReceipt.input_key)
        )
        receipt = await independent.scalar(
            select(EvaluationReceipt)
            .where(
                EvaluationReceipt.owner_id == answer.owner_id,
                EvaluationReceipt.input_key == key,
            )
            .with_for_update()
        )
        if receipt is None:
            raise HTTPException(503)
        if receipt.state == "completed":
            return validate_evaluation(receipt.result, provider, list(content.expected_concepts))
        if not created:
            if receipt.state == "started" or receipt.attempts >= 2:
                raise HTTPException(409, detail="assessment_evaluation_limit")
            receipt.attempts += 1
            receipt.state = "started"
        await reserve(factory, settings, answer.owner_id, "ai")
        await independent.commit()  # Durable before sending any candidate text.
    try:
        raw = await provider.evaluate(content)
        result: ConceptualEvaluation = validate_evaluation(
            raw, provider, list(content.expected_concepts)
        )
        validate_domain(
            AnswerInput(
                question=content.prompt,
                answer=content.response,
                expected_concepts=list(content.expected_concepts),
                rubric=list(content.rubric),
                profile=content.profile,
            ),
            AnswerEvaluation.model_validate(result.model_dump(exclude={"kind"})),
        )
    except Exception:
        async with factory() as independent:
            receipt = await independent.get(EvaluationReceipt, (answer.owner_id, key))
            if receipt:
                receipt.state = "failed"
                await independent.commit()
        raise
    # Cancellation/process loss leaves "started": ambiguous work is never replayed.
    async with factory() as independent:
        receipt = await independent.get(EvaluationReceipt, (answer.owner_id, key))
        if receipt is None:
            raise HTTPException(503)
        receipt.state, receipt.result = "completed", result.model_dump(mode="json")
        await independent.commit()
    return result
