"""Durable, fenced interview work; no transaction spans an AI request."""

import asyncio
import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.ai.errors import ProviderError, ProviderUnavailable
from interview_prep.ai.factory import create_provider
from interview_prep.ai.provider import AIProvider, BaseProvider
from interview_prep.ai.rubric import profile_for
from interview_prep.ai.schemas import AnswerEvaluation as AnswerResult
from interview_prep.ai.schemas import AnswerInput, Followup, FollowupInput, Provenance
from interview_prep.ai.validation import validate_domain
from interview_prep.core.config import Settings
from interview_prep.core.quotas import reserve
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, User
from interview_prep.modules.interviews import commands, queries
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationKind,
    EvaluationStatus,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.interviews.policy import VERSION, Clock, utc_now
from interview_prep.modules.interviews.selection import concepts
from interview_prep.modules.interviews.work_models import FollowupContent, InterviewWork
from interview_prep.modules.roadmaps.models import ProgressEvent, ProgressEventType

ProviderFactory = Callable[[bool, float], AIProvider]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Dispatch:
    work_id: UUID
    owner_id: UUID
    session_id: UUID
    token: UUID
    operation: str
    content: AnswerInput | FollowupInput
    provider: AIProvider


class InterviewRunner:
    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        http: httpx.AsyncClient,
        clock: Clock = utc_now,
    ) -> None:
        self.factory, self.settings, self.http, self.clock = factory, settings, http, clock
        self.wake = asyncio.Event()
        self.provider_factory: ProviderFactory = lambda demo, remaining: create_provider(
            settings.model_copy(
                update={"ai_timeout_seconds": min(settings.ai_timeout_seconds, remaining)}
            ),
            http,
            demo=demo,
        )

    async def loop(self) -> None:
        while True:
            # Clear before querying so a committed command cannot lose its wakeup
            # between an idle tick and entering the wait below.
            self.wake.clear()
            try:
                worked = await self.tick()
            except Exception:
                # Do not log exception bodies, SQL parameters or private inputs.
                logger.warning("Interview worker temporarily unavailable")
                worked = False
            if not worked:
                try:
                    await asyncio.wait_for(
                        self.wake.wait(), timeout=self.settings.interview_poll_seconds
                    )
                except TimeoutError:
                    pass

    async def tick(self) -> bool:
        await self.maintenance()
        dispatch = await self.claim()
        if dispatch is None:
            return False
        result: AnswerResult | Followup | None = None
        provenance: Provenance | None = None
        error: str | None = None
        try:
            if dispatch.provider.kind == "model_assisted":
                await reserve(self.factory, self.settings, dispatch.owner_id, "ai")
            async with asyncio.timeout(min(dispatch.provider.timeout_seconds, 60)):
                if dispatch.operation == "evaluate":
                    evaluated = await dispatch.provider.evaluate_answer(dispatch.content)
                    result, provenance = (
                        AnswerResult.model_validate(evaluated.data),
                        evaluated.provenance,
                    )
                else:
                    if not isinstance(dispatch.content, FollowupInput):
                        raise ProviderUnavailable()
                    generated = await dispatch.provider.generate_followup(dispatch.content)
                    result, provenance = (
                        Followup.model_validate(generated.data),
                        generated.provenance,
                    )
                validate_domain(dispatch.content, result)
                if isinstance(result, AnswerResult) and result.score_basis != (
                    "lexical_coverage" if dispatch.provider.kind == "simulation" else "rubric_mean"
                ):
                    raise ValueError("Score basis mismatch")
                if (
                    provenance.provider != dispatch.provider.name
                    or provenance.provider_version != dispatch.provider.version
                    or provenance.kind != dispatch.provider.kind
                    or provenance.model
                    != (
                        dispatch.provider.model_for(
                            "evaluate_answer"
                            if dispatch.operation == "evaluate"
                            else "generate_followup"
                        )
                        if isinstance(dispatch.provider, BaseProvider)
                        else dispatch.provider.model
                    )
                ):
                    raise ValueError("Provenance mismatch")
        except ProviderError as exc:
            error = exc.code
        except HTTPException:
            error = "ai_rate_limited"
        except TimeoutError:
            error = "ai_timeout"
        except Exception:
            error = "ai_invalid_output"
        await self.finish(dispatch, result, provenance, error)
        await self.maintenance()
        return True

    async def claim(self) -> Dispatch | None:
        now = self.clock()
        async with self.factory() as session:
            job = await session.scalar(
                select(InterviewWork)
                .where(InterviewWork.state == "pending")
                .order_by(InterviewWork.created_at, InterviewWork.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return None
            job.state, job.lease_token = "running", uuid4()
            job.lease_expires_at = now + timedelta(seconds=90)
            work_id, owner_id, session_id, token = (
                job.id,
                job.owner_id,
                job.session_id,
                job.lease_token,
            )
            await session.commit()
        # Claim lock is released before standard principal/session/work lock order.
        async with self.factory() as session:
            user = await session.scalar(select(User).where(User.id == owner_id).with_for_update())
            interview = await session.scalar(
                select(InterviewSession)
                .where(InterviewSession.owner_id == owner_id, InterviewSession.id == session_id)
                .with_for_update()
            )
            job = await session.scalar(
                select(InterviewWork)
                .where(InterviewWork.owner_id == owner_id, InterviewWork.id == work_id)
                .with_for_update()
            )
            if (
                not job
                or not user
                or not interview
                or job.state != "running"
                or job.lease_token != token
            ):
                return None
            if (
                not self.authorized(user, now)
                or interview.status
                not in (SessionStatus.ACTIVE, SessionStatus.PAUSED, SessionStatus.FINALIZING)
                or now >= job.deadline_at
            ):
                await self.fail(session, interview, job, "work_unavailable")
                await session.commit()
                return None
            remaining = (job.deadline_at - now).total_seconds()
            provider = self.provider_factory(user.kind == PrincipalKind.DEMO, remaining)
            if (
                queries.descriptor(provider).model_dump(mode="json")
                != interview.provider_descriptor
            ):
                await self.fail(session, interview, job, "provider_changed")
                await session.commit()
                return None
            if provider.kind == "model_assisted" and provider.model is None:
                await self.fail(session, interview, job, "ai_unavailable")
                await session.commit()
                return None
            data = await queries.load(session, interview)
            turn = next((t for t in data.turns if t.id == job.turn_id), None)
            answer = data.answers.get(job.turn_id)
            version = (
                data.versions.get(turn.question_version_id)
                if turn and turn.question_version_id
                else None
            )
            if not turn or not answer or not answer.answer_text or not version:
                await self.fail(session, interview, job, "work_unavailable")
                await session.commit()
                return None
            expected, rubric = await concepts(session, version.id)
            content: AnswerInput | FollowupInput
            if job.operation == "followup":
                if turn.followup_decision != "pending":
                    job.state = "cancelled"
                    await session.commit()
                    return None
                recent = [queries.turn_view(data, t).prompt for t in data.turns]
                content = FollowupInput(
                    question=version.prompt or "",
                    answer=answer.answer_text,
                    expected_concepts=expected,
                    rubric=rubric,
                    recent_questions=recent,
                )
            else:
                content = AnswerInput(
                    question=version.prompt or "",
                    answer=answer.answer_text,
                    expected_concepts=expected,
                    rubric=rubric,
                    profile=profile_for(str(version.question_type)),
                )
                evaluation = (
                    await session.get(AnswerEvaluation, job.evaluation_id)
                    if job.evaluation_id
                    else None
                )
                if evaluation is None or evaluation.status != EvaluationStatus.PENDING:
                    job.state = "cancelled"
                    await session.commit()
                    return None
                evaluation.input_digest = hashlib.sha256(
                    content.model_dump_json().encode()
                ).hexdigest()
                evaluation.status, turn.status = EvaluationStatus.RUNNING, TurnStatus.EVALUATING
            job.dispatched_at = now
            interview.revision += 1
            await session.commit()
            return Dispatch(work_id, owner_id, session_id, token, job.operation, content, provider)

    @staticmethod
    def authorized(user: User, now: datetime) -> bool:
        return user.status == PrincipalStatus.ACTIVE and (
            user.expires_at is None or now < user.expires_at
        )

    async def fail(
        self, session: AsyncSession, interview: InterviewSession, job: InterviewWork, error: str
    ) -> None:
        job.state, job.error_code = "failed", error
        turn = await session.scalar(
            select(InterviewQuestion).where(
                InterviewQuestion.id == job.turn_id,
                InterviewQuestion.owner_id == job.owner_id,
                InterviewQuestion.session_id == interview.id,
            )
        )
        if job.operation == "evaluate" and job.evaluation_id:
            evaluation = await session.scalar(
                select(AnswerEvaluation).where(
                    AnswerEvaluation.id == job.evaluation_id,
                    AnswerEvaluation.owner_id == job.owner_id,
                )
            )
            if evaluation and evaluation.status in (
                EvaluationStatus.PENDING,
                EvaluationStatus.RUNNING,
            ):
                evaluation.status, evaluation.error_code = EvaluationStatus.FAILED, error
                if turn:
                    turn.status = TurnStatus.EVALUATION_FAILED
        elif turn and turn.followup_decision == "pending":
            turn.followup_decision = "unavailable"
        interview.revision += 1

    async def finish(
        self,
        dispatch: Dispatch,
        result: AnswerResult | Followup | None,
        provenance: Provenance | None,
        error: str | None,
    ) -> None:
        now = self.clock()
        async with self.factory() as session:
            user = await session.scalar(
                select(User).where(User.id == dispatch.owner_id).with_for_update()
            )
            interview = await session.scalar(
                select(InterviewSession)
                .where(
                    InterviewSession.id == dispatch.session_id,
                    InterviewSession.owner_id == dispatch.owner_id,
                )
                .with_for_update()
            )
            job = await session.scalar(
                select(InterviewWork)
                .where(
                    InterviewWork.id == dispatch.work_id,
                    InterviewWork.owner_id == dispatch.owner_id,
                )
                .with_for_update()
            )
            if (
                not user
                or not interview
                or not job
                or job.state != "running"
                or job.lease_token != dispatch.token
            ):
                return
            if (
                not self.authorized(user, now)
                or now >= job.deadline_at
                or (job.lease_expires_at is not None and now >= job.lease_expires_at)
                or interview.status
                not in (SessionStatus.ACTIVE, SessionStatus.PAUSED, SessionStatus.FINALIZING)
            ):
                error = "work_expired"
            if interview.finalization_deadline and now >= interview.finalization_deadline:
                error = "work_expired"
            turn = await session.scalar(
                select(InterviewQuestion).where(
                    InterviewQuestion.id == job.turn_id,
                    InterviewQuestion.owner_id == job.owner_id,
                    InterviewQuestion.session_id == interview.id,
                )
            )
            if turn is None:
                return
            if error or result is None or provenance is None:
                await self.fail(session, interview, job, error or "ai_invalid_output")
            elif isinstance(result, AnswerResult) and job.evaluation_id:
                evaluation = await session.scalar(
                    select(AnswerEvaluation).where(
                        AnswerEvaluation.id == job.evaluation_id,
                        AnswerEvaluation.owner_id == dispatch.owner_id,
                    )
                )
                if not evaluation or evaluation.status != EvaluationStatus.RUNNING:
                    return
                evaluation.score, evaluation.feedback = result.score, result.feedback
                evaluation.result_payload = result.model_dump(mode="json")
                evaluation.usage_metadata = {
                    **(evaluation.usage_metadata or {}),
                    "evaluated_at": now.isoformat(),
                    "provider_version": provenance.provider_version,
                }
                evaluation.status, turn.status, job.state = (
                    EvaluationStatus.COMPLETED,
                    TurnStatus.EVALUATED,
                    "succeeded",
                )
                interview.revision += 1
            elif (
                isinstance(result, Followup)
                and turn.followup_decision == "pending"
                and interview.status in (SessionStatus.ACTIVE, SessionStatus.PAUSED)
            ):
                data = await queries.load(session, interview)

                def normalize(value: str) -> str:
                    return " ".join(value.split()).casefold()

                if normalize(result.question) in {
                    normalize(queries.turn_view(data, t).prompt) for t in data.turns
                }:
                    await self.fail(session, interview, job, "ai_invalid_output")
                else:
                    session.add(
                        FollowupContent(
                            owner_id=job.owner_id,
                            session_id=interview.id,
                            parent_id=turn.id,
                            prompt=result.question,
                            rationale=result.rationale,
                            excerpt=dispatch.content.answer[:200],
                            provenance=provenance.model_dump(mode="json"),
                        )
                    )
                    turn.followup_decision, job.state = "ready", "succeeded"
                    interview.revision += 1
            else:
                job.state = "cancelled"
            await session.commit()

    async def maintenance(self) -> None:
        now = self.clock()
        async with self.factory() as session:
            identifiers = (
                await session.execute(
                    select(InterviewSession.id, InterviewSession.owner_id)
                    .where(
                        InterviewSession.contract_version == VERSION,
                        InterviewSession.status.in_(
                            [
                                SessionStatus.DRAFT,
                                SessionStatus.ACTIVE,
                                SessionStatus.PAUSED,
                                SessionStatus.FINALIZING,
                            ]
                        ),
                    )
                    .order_by(InterviewSession.created_at)
                    .limit(500)
                )
            ).all()
        for identifier, owner in identifiers:
            async with self.factory() as session:
                await session.scalar(select(User).where(User.id == owner).with_for_update())
                interview = await session.scalar(
                    select(InterviewSession)
                    .where(InterviewSession.id == identifier, InterviewSession.owner_id == owner)
                    .with_for_update()
                )
                if interview is None:
                    continue
                jobs = list(
                    (
                        await session.scalars(
                            select(InterviewWork)
                            .where(
                                InterviewWork.owner_id == owner,
                                InterviewWork.session_id == identifier,
                                InterviewWork.state.in_(["pending", "running"]),
                            )
                            .with_for_update()
                        )
                    ).all()
                )
                for job in jobs:
                    if now >= job.deadline_at or (
                        interview.finalization_deadline and now >= interview.finalization_deadline
                    ):
                        await self.fail(session, interview, job, "work_expired")
                    elif (
                        job.state == "running"
                        and job.lease_expires_at
                        and now >= job.lease_expires_at
                    ):
                        if job.dispatched_at:
                            await self.fail(session, interview, job, f"{job.operation}_interrupted")
                        else:
                            job.state, job.lease_token = "pending", None
                if (
                    interview.deadline_at
                    and now >= interview.deadline_at
                    and interview.status
                    in (SessionStatus.DRAFT, SessionStatus.ACTIVE, SessionStatus.PAUSED)
                ):
                    if interview.status == SessionStatus.DRAFT:
                        interview.status, interview.ended_at, interview.end_reason = (
                            SessionStatus.ABANDONED,
                            interview.deadline_at,
                            "expired",
                        )
                    else:
                        data = await queries.load(session, interview)
                        current = next(
                            (t for t in data.turns if t.id == interview.current_turn_id), None
                        )
                        if current and current.status == TurnStatus.AWAITING_ANSWER:
                            commands.stop_timer(current, interview.deadline_at)
                            current.status, current.resolved_at = (
                                TurnStatus.UNANSWERED,
                                interview.deadline_at,
                            )
                        await commands.close(session, data, now, "expired")
                    interview.revision += 1
                    await session.flush()
                if interview.status == SessionStatus.FINALIZING and not any(
                    j.operation == "evaluate" and j.state in ("pending", "running") for j in jobs
                ):
                    interview.revision += 1
                    interview.status = (
                        SessionStatus.COMPLETED
                        if interview.end_reason == "full"
                        else SessionStatus.ABANDONED
                    )
                    if interview.status == SessionStatus.COMPLETED:
                        interview.completed_at = now
                        await session.flush()
                        data = await queries.load(session, interview)
                        kinds = {
                            e.kind
                            for e in data.evaluations.values()
                            if e.status == EvaluationStatus.COMPLETED
                        }
                        session.add(
                            ProgressEvent(
                                owner_id=owner,
                                event_type=ProgressEventType.INTERVIEW_COMPLETED,
                                interview_session_id=identifier,
                                result_kind=EvaluationKind.SIMULATION
                                if EvaluationKind.SIMULATION in kinds
                                else EvaluationKind.MODEL_ASSISTED
                                if kinds
                                else None,
                                deduplication_key=identifier,
                                occurred_at=now,
                            )
                        )
                await session.commit()
