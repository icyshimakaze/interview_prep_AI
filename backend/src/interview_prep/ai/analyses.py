"""Validated opt-in analysis, isolated from extraction and objective grading."""

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.ai.analysis_models import AIAnalysis
from interview_prep.ai.errors import InvalidProviderOutput, ProviderError
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.rubric import EVALUATION_PROMPT_VERSION
from interview_prep.ai.schemas import (
    AnswerEvaluation,
    AnswerInput,
    Contract,
    Input,
    ProviderResult,
    ResumeAnalysis,
    ResumeInput,
)
from interview_prep.ai.validation import validate_domain
from interview_prep.core.config import Settings
from interview_prep.core.quotas import reserve
from interview_prep.modules.projects import defense
from interview_prep.modules.projects.defense_models import DefenseAnswer
from interview_prep.modules.resumes import service as resumes


async def saved[T: Contract](
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    provider: AIProvider,
    content: Input,
    schema: type[T],
    generate: Callable[[], Awaitable[ProviderResult[T]]],
    *,
    resume_id: UUID | None = None,
    defense_answer_id: UUID | None = None,
    source_revision: int | None = None,
    target_version_id: UUID | None = None,
    roadmap_id: UUID | None = None,
    project_analysis_id: UUID | None = None,
) -> ProviderResult[T]:
    result_type = cast(type[ProviderResult[T]], ProviderResult.__class_getitem__(schema))
    key = hashlib.sha256(
        json.dumps(
            [
                str(resume_id),
                str(defense_answer_id),
                source_revision,
                content.model_dump(mode="json"),
                schema.__name__,
                provider.name,
                provider.version,
                provider.model,
                EVALUATION_PROMPT_VERSION,
                "saved-analysis-v2",
            ]
            + (
                [str(target_version_id), str(roadmap_id), str(project_analysis_id)]
                if any((target_version_id, roadmap_id, project_analysis_id))
                else []
            ),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    async with factory() as session:
        await session.execute(
            delete(AIAnalysis).where(
                AIAnalysis.owner_id == owner,
                AIAnalysis.input_key == key,
                AIAnalysis.expires_at <= datetime.now(UTC),
            )
        )
        created = await session.scalar(
            insert(AIAnalysis)
            .values(
                owner_id=owner,
                input_key=key,
                resume_id=resume_id,
                defense_answer_id=defense_answer_id,
                target_version_id=target_version_id,
                roadmap_id=roadmap_id,
                project_analysis_id=project_analysis_id,
                attempts=1,
                state="started",
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
            .on_conflict_do_nothing()
            .returning(AIAnalysis.input_key)
        )
        receipt = await session.scalar(
            select(AIAnalysis)
            .where(AIAnalysis.owner_id == owner, AIAnalysis.input_key == key)
            .with_for_update()
        )
        if receipt is None:
            raise HTTPException(503)
        if receipt.state == "completed":
            result = result_type.model_validate(receipt.result)
            validate_domain(content, result.data)
            return result
        if not created:
            if receipt.state == "started" or receipt.attempts >= 2:
                raise HTTPException(409, detail="ai_analysis_pending")
            receipt.attempts += 1
            receipt.state = "started"
            receipt.dispatch_token = uuid4()
        dispatch_token = receipt.dispatch_token
        if provider.kind == "model_assisted":
            await reserve(factory, settings, owner, "ai")
        await session.commit()
    try:
        result = result_type.model_validate(await generate())
        validate_domain(content, result.data)
        if (
            result.provenance.provider != provider.name
            or result.provenance.provider_version != provider.version
            or result.provenance.kind != provider.kind
        ):
            raise InvalidProviderOutput()
        payload = result.model_dump(mode="json")
        if len(json.dumps(payload).encode()) > 131072:
            raise InvalidProviderOutput()
    except Exception as exc:
        async with factory() as session:
            receipt = await session.scalar(
                select(AIAnalysis)
                .where(
                    AIAnalysis.owner_id == owner,
                    AIAnalysis.input_key == key,
                    AIAnalysis.dispatch_token == dispatch_token,
                )
                .with_for_update()
            )
            if receipt:
                receipt.state = "failed"
                await session.commit()
        if isinstance(exc, ProviderError):
            raise HTTPException(503, detail=exc.code) from None
        raise HTTPException(503, detail="ai_invalid_output") from None
    # Cancellation leaves started; ambiguous provider work is not auto-dispatched again.
    async with factory() as session:
        receipt = await session.scalar(
            select(AIAnalysis)
            .where(
                AIAnalysis.owner_id == owner,
                AIAnalysis.input_key == key,
                AIAnalysis.dispatch_token == dispatch_token,
            )
            .with_for_update()
        )
        if receipt is None:
            raise HTTPException(404)  # Source/owner was deleted while the provider worked.
        receipt.state, receipt.result = "completed", payload
        await session.commit()
    return result


async def resume_analysis(
    session: AsyncSession,
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    identifier: UUID,
    provider: AIProvider,
) -> ProviderResult[ResumeAnalysis]:
    resume = await resumes.get_resume(session, owner, identifier)
    # Raw PDFs/text are intentionally discarded by the existing upload pipeline.
    # Review retained evidence only; never pretend it is a full-document analysis.
    text = "\n".join(
        f"Claim: {e.user_correction or e.claim}\nExcerpt: {e.source_excerpt or ''}"
        for e in resume.evidence
        if e.review_status != "rejected"
    )[:50000]
    if not text.strip():
        raise HTTPException(422, detail="ai_no_evidence")
    content = ResumeInput(text=text)
    revision = resume.revision
    await session.rollback()  # Release the read connection before waiting on a model.
    return await saved(
        factory,
        settings,
        owner,
        provider,
        content,
        ResumeAnalysis,
        lambda: provider.analyze_resume(content),
        resume_id=identifier,
        source_revision=revision,
    )


async def defense_feedback(
    session: AsyncSession,
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    identifier: UUID,
    position: int,
    provider: AIProvider,
) -> ProviderResult[AnswerEvaluation]:
    run = await defense.view(session, owner, identifier)
    answer = await session.scalar(
        select(DefenseAnswer).where(
            DefenseAnswer.owner_id == owner,
            DefenseAnswer.run_id == identifier,
            DefenseAnswer.position == position,
            DefenseAnswer.status == "submitted",
        )
    )
    if not answer or not answer.answer_text:
        raise HTTPException(404)
    question = next(r.question for r in run.responses if r.position == position)
    content = AnswerInput(
        question=question.prompt,
        answer=answer.answer_text,
        rubric=["Explain decisions, evidence, alternatives and failure cases."],
        profile="technical",
    )
    answer_id = answer.id
    await session.rollback()
    return await saved(
        factory,
        settings,
        owner,
        provider,
        content,
        AnswerEvaluation,
        lambda: provider.evaluate_answer(content),
        defense_answer_id=answer_id,
    )
