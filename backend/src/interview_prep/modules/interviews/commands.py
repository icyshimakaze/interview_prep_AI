"""Short owned transactions. Provider calls never occur in this module."""

import hashlib
import json
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai.provider import AIProvider
from interview_prep.modules.assessments.models import AnswerStatus
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews import queries, selection
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationKind,
    EvaluationStatus,
    InterviewAnswer,
    InterviewMode,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.interviews.policy import VERSION, Clock, clean_text, conflict, utc_now
from interview_prep.modules.interviews.schemas import (
    AdvanceInterview,
    ConfigureInterview,
    CreateInterview,
    EndInterview,
    InterviewCommandResponse,
    InterviewDraft,
    InterviewMutation,
    InterviewReceipt,
    InterviewText,
    PauseInterview,
    RetryInterviewEvaluation,
)
from interview_prep.modules.interviews.work_models import (
    FollowupContent,
    InterviewCommand,
    InterviewWork,
)
from interview_prep.modules.questions.models import QuestionVersion


def digest(operation: str, body: BaseModel) -> str:
    return hashlib.sha256(
        json.dumps(
            [operation, body.model_dump(mode="json")], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


async def replay(
    session: AsyncSession, owner: UUID, key: UUID, operation: str, body: BaseModel
) -> InterviewCommand | None:
    receipt = await session.scalar(
        select(InterviewCommand).where(
            InterviewCommand.owner_id == owner, InterviewCommand.command_key == key
        )
    )
    if receipt and (receipt.operation != operation or receipt.digest != digest(operation, body)):
        conflict("command_conflict")
    return receipt


async def response(session: AsyncSession, receipt: InterviewCommand) -> InterviewCommandResponse:
    return InterviewCommandResponse(
        receipt=InterviewReceipt(
            command_key=receipt.command_key,
            operation=receipt.operation,
            session_id=receipt.session_id,
            applied_revision=receipt.applied_revision,
        ),
        session=await queries.read(session, receipt.owner_id, receipt.session_id),
    )


async def record(
    session: AsyncSession,
    interview: InterviewSession,
    body: CreateInterview | InterviewMutation,
    operation: str,
    status: int,
) -> tuple[InterviewCommandResponse, int]:
    receipt = InterviewCommand(
        owner_id=interview.owner_id,
        session_id=interview.id,
        command_key=body.command_key,
        operation=operation,
        digest=digest(operation, body),
        applied_revision=interview.revision,
        response_status=status,
    )
    session.add(receipt)
    await session.commit()
    return await response(session, receipt), status


async def create(
    session: AsyncSession,
    user: User,
    body: CreateInterview,
    provider: AIProvider,
    clock: Clock = utc_now,
) -> tuple[InterviewCommandResponse, int]:
    await session.scalar(select(User).where(User.id == user.id).with_for_update())
    receipt = await replay(session, user.id, body.command_key, "create", body)
    if receipt:
        return await response(session, receipt), receipt.response_status
    await selection.validate_target(session, user.id, body.configuration.target_id)
    total = (
        await session.scalar(
            select(func.count())
            .select_from(InterviewSession)
            .where(InterviewSession.owner_id == user.id)
        )
        or 0
    )
    unfinished = (
        await session.scalar(
            select(func.count())
            .select_from(InterviewSession)
            .where(
                InterviewSession.owner_id == user.id,
                InterviewSession.status.in_(
                    [
                        SessionStatus.DRAFT,
                        SessionStatus.ACTIVE,
                        SessionStatus.PAUSED,
                        SessionStatus.FINALIZING,
                    ]
                ),
            )
        )
        or 0
    )
    if total >= 100 or unfinished >= 5:
        conflict("interview_limit")
    now = clock()
    interview = InterviewSession(
        owner_id=user.id,
        contract_version=VERSION,
        mode=InterviewMode.MOCK_INTERVIEW,
        status=SessionStatus.DRAFT,
        configuration=body.configuration.model_dump(mode="json"),
        context_version="adaptive-v1",
        policy_version=VERSION,
        provider=provider.name,
        model=provider.model,
        provider_descriptor=queries.descriptor(provider).model_dump(mode="json"),
        main_question_limit=body.configuration.question_count,
        revision=1,
        deadline_at=min(now + timedelta(hours=24), user.expires_at)
        if user.expires_at
        else now + timedelta(hours=24),
    )
    session.add(interview)
    await session.flush()
    return await record(session, interview, body, "create", 201)


def stop_timer(turn: InterviewQuestion, now: datetime) -> None:
    if turn.running_since:
        turn.answering_ms += max(0, int((now - turn.running_since).total_seconds() * 1000))
        turn.running_since = None


async def allocate(
    session: AsyncSession,
    interview: InterviewSession,
    turns: list[InterviewQuestion],
    now: datetime,
    *,
    content: FollowupContent | None = None,
    parent: InterviewQuestion | None = None,
) -> None:
    if content and parent:
        turn = InterviewQuestion(
            owner_id=interview.owner_id,
            session_id=interview.id,
            source_kind="followup",
            followup_content_id=content.id,
            parent_question_id=parent.id,
            main_ordinal=parent.main_ordinal,
            sequence=len(turns) + 1,
            status=TurnStatus.AWAITING_ANSWER,
            presented_at=now,
            running_since=now,
        )
        parent.followup_decision = "consumed"
    else:
        version_id, trace = selection.choose(interview, turns)
        version = await session.get(QuestionVersion, version_id)
        if version is None:
            conflict("interview_pool")
        turn = InterviewQuestion(
            owner_id=interview.owner_id,
            session_id=interview.id,
            question_version_id=version_id,
            stable_question_id=version.question_id,
            source_kind="bank",
            main_ordinal=1 + sum(t.parent_question_id is None for t in turns),
            sequence=len(turns) + 1,
            status=TurnStatus.AWAITING_ANSWER,
            presented_at=now,
            running_since=now,
            selection_trace=trace,
        )
    session.add(turn)
    await session.flush()
    session.add(
        InterviewAnswer(
            owner_id=interview.owner_id,
            interview_question_id=turn.id,
            status=AnswerStatus.DRAFT,
            revision=1,
        )
    )
    interview.current_turn_id = turn.id


async def queue_evaluation(
    session: AsyncSession,
    interview: InterviewSession,
    turn: InterviewQuestion,
    answer: InterviewAnswer,
    now: datetime,
    previous: AnswerEvaluation | None = None,
) -> None:
    child = turn.parent_question_id is not None
    provider = interview.provider_descriptor or {}
    version = (
        await session.get(QuestionVersion, turn.question_version_id)
        if turn.question_version_id
        else None
    )
    evaluation = AnswerEvaluation(
        owner_id=interview.owner_id,
        interview_answer_id=answer.id,
        version=previous.version + 1 if previous else 1,
        supersedes_id=previous.id if previous else None,
        kind=EvaluationKind.SELF_REVIEW
        if child or (provider.get("kind") == "model_assisted" and not interview.model)
        else EvaluationKind(str(provider.get("kind", "simulation"))),
        status=EvaluationStatus.NOT_EVALUABLE if child else EvaluationStatus.PENDING,
        evaluator_version="interview-followup-review-v1"
        if child
        else str(provider.get("version", VERSION)),
        rubric_version="interview-followup-review-v1"
        if child
        else (version.rubric_version or VERSION)
        if version
        else VERSION,
        provider=None if child else interview.provider,
        model=None if child else interview.model,
        prompt_version=None if child else "ai-prompts-v1",
        schema_version=VERSION,
        feedback="Not scored: this contextual practice probe has no reviewed scoring rubric."
        if child
        else None,
        score_scale_max=None if child else 4,
    )
    session.add(evaluation)
    await session.flush()
    if child:
        turn.status = TurnStatus.EVALUATED
    else:
        turn.status = TurnStatus.SUBMITTED
        session.add(
            InterviewWork(
                owner_id=interview.owner_id,
                session_id=interview.id,
                turn_id=turn.id,
                evaluation_id=evaluation.id,
                operation="evaluate",
                dedupe_key=f"evaluate:{answer.id}:{evaluation.version}",
                state="pending",
                deadline_at=now + timedelta(seconds=120),
            )
        )


async def resolve_answer(
    session: AsyncSession,
    data: queries.SessionData,
    turn: InterviewQuestion,
    text: str | None,
    action: str,
    key: UUID,
    now: datetime,
) -> None:
    answer = data.answers.get(turn.id)
    if turn.status != TurnStatus.AWAITING_ANSWER or answer is None:
        conflict("interview_turn")
    cleaned = clean_text(text)
    if action == "submit" and cleaned is None:
        raise HTTPException(status_code=422)
    answer.answer_text, answer.revision = cleaned, answer.revision + 1
    stop_timer(turn, now)
    turn.resolved_at = now
    if action == "submit":
        answer.status, answer.submitted_at, answer.submission_key = AnswerStatus.SUBMITTED, now, key
        await queue_evaluation(session, data.interview, turn, answer, now)
    elif action == "skip":
        answer.status, turn.status = AnswerStatus.SKIPPED, TurnStatus.SKIPPED
    else:
        turn.status = TurnStatus.UNANSWERED


async def cancel_offers(session: AsyncSession, data: queries.SessionData) -> None:
    for turn in data.turns:
        if turn.followup_decision in ("pending", "ready"):
            turn.followup_decision = "declined"
    work = (
        await session.scalars(
            select(InterviewWork).where(
                InterviewWork.owner_id == data.interview.owner_id,
                InterviewWork.session_id == data.interview.id,
                InterviewWork.operation == "followup",
                InterviewWork.state.in_(["pending", "running"]),
            )
        )
    ).all()
    for job in work:
        job.state = "cancelled"


async def close(
    session: AsyncSession, data: queries.SessionData, now: datetime, reason: str
) -> None:
    await cancel_offers(session, data)
    data.interview.status = SessionStatus.FINALIZING
    data.interview.end_reason, data.interview.ended_at = reason, now
    data.interview.finalization_deadline = now + timedelta(seconds=120)


def save_draft(data: queries.SessionData, draft: InterviewDraft | None) -> None:
    if draft is None:
        return
    current = next((t for t in data.turns if t.id == data.interview.current_turn_id), None)
    if (
        current is None
        or current.id != draft.turn_id
        or current.status != TurnStatus.AWAITING_ANSWER
    ):
        conflict("interview_turn")
    answer = data.answers[current.id]
    answer.answer_text, answer.revision = clean_text(draft.answer_text), answer.revision + 1


async def mutate(
    session: AsyncSession,
    user: User,
    identifier: UUID,
    action: str,
    body: InterviewMutation,
    provider: AIProvider,
    turn_id: UUID | None = None,
    clock: Clock = utc_now,
) -> tuple[InterviewCommandResponse, int]:
    await session.scalar(select(User).where(User.id == user.id).with_for_update())
    interview = await queries.owned(session, user.id, identifier, lock=True)
    if turn_id and not await session.scalar(
        select(InterviewQuestion.id).where(
            InterviewQuestion.id == turn_id,
            InterviewQuestion.owner_id == user.id,
            InterviewQuestion.session_id == identifier,
        )
    ):
        raise HTTPException(status_code=404)
    operation = f"{identifier}/{turn_id or ''}/{action}"
    receipt = await replay(session, user.id, body.command_key, operation, body)
    if receipt:
        return await response(session, receipt), receipt.response_status
    if interview.contract_version != VERSION:
        conflict("interview_legacy")
    now = clock()
    if interview.deadline_at and now >= interview.deadline_at:
        conflict("interview_expired")
    if interview.revision != body.revision:
        conflict("interview_revision")
    data = await queries.load(session, interview)
    current = next((t for t in data.turns if t.id == interview.current_turn_id), None)
    if action in ("save", "submit", "skip", "followup", "retry") and (
        current is None or (turn_id != current.id and action != "retry")
    ):
        conflict("interview_turn")
    active, paused = (
        interview.status == SessionStatus.ACTIVE,
        interview.status == SessionStatus.PAUSED,
    )
    status = 200
    if (
        action == "configure"
        and isinstance(body, ConfigureInterview)
        and interview.status == SessionStatus.DRAFT
    ):
        await selection.validate_target(session, user.id, body.configuration.target_id)
        interview.configuration = body.configuration.model_dump(mode="json")
        interview.main_question_limit = body.configuration.question_count
    elif action == "start" and interview.status == SessionStatus.DRAFT:
        from interview_prep.modules.interviews.schemas import InterviewConfiguration

        config = InterviewConfiguration.model_validate(interview.configuration)
        await selection.freeze(session, interview, user, config)
        interview.provider, interview.model = provider.name, provider.model
        interview.provider_descriptor = queries.descriptor(provider).model_dump(mode="json")
        interview.status, interview.started_at = SessionStatus.ACTIVE, now
        interview.deadline_at = (
            min(now + timedelta(hours=24), user.expires_at)
            if user.expires_at
            else now + timedelta(hours=24)
        )
        await session.flush()
        await allocate(session, interview, [], now)
    elif (
        action in ("save", "submit", "skip")
        and isinstance(body, InterviewText)
        and active
        and current
    ):
        if action == "save":
            save_draft(data, InterviewDraft(turn_id=current.id, answer_text=body.answer_text))
        else:
            await resolve_answer(
                session, data, current, body.answer_text, action, body.command_key, now
            )
            status = 202 if action == "submit" and current.parent_question_id is None else 200
    elif (
        action == "followup"
        and active
        and current
        and current.parent_question_id is None
        and current.status
        not in (TurnStatus.AWAITING_ANSWER, TurnStatus.SKIPPED, TurnStatus.UNANSWERED)
    ):
        if (
            current.followup_decision != "none"
            or sum(t.followup_decision != "none" for t in data.turns) >= 3
        ):
            conflict("followup_limit")
        current.followup_decision = "pending"
        session.add(
            InterviewWork(
                owner_id=user.id,
                session_id=identifier,
                turn_id=current.id,
                operation="followup",
                dedupe_key=f"followup:{current.id}",
                state="pending",
                deadline_at=now + timedelta(seconds=120),
            )
        )
        status = 202
    elif (
        action == "advance"
        and isinstance(body, AdvanceInterview)
        and active
        and current
        and current.status != TurnStatus.AWAITING_ANSWER
    ):
        if current.id != body.from_turn_id:
            conflict("interview_turn")
        if body.next_kind == "followup":
            content = await session.scalar(
                select(FollowupContent).where(
                    FollowupContent.owner_id == user.id,
                    FollowupContent.session_id == identifier,
                    FollowupContent.parent_id == current.id,
                )
            )
            if current.followup_decision != "ready" or content is None:
                conflict("followup_not_ready")
            await allocate(session, interview, data.turns, now, content=content, parent=current)
        else:
            if (
                sum(t.parent_question_id is None for t in data.turns)
                >= interview.main_question_limit
            ):
                conflict("interview_turn")
            await cancel_offers(session, data)
            await session.flush()
            await allocate(session, interview, data.turns, now)
    elif action == "pause" and isinstance(body, PauseInterview) and active:
        save_draft(data, body.draft)
        if current:
            stop_timer(current, now)
        interview.status = SessionStatus.PAUSED
    elif action == "resume" and paused:
        interview.status = SessionStatus.ACTIVE
        if current and current.status == TurnStatus.AWAITING_ANSWER:
            current.running_since = now
    elif (
        action == "complete" and active and current and current.status != TurnStatus.AWAITING_ANSWER
    ):
        if queries.progress(data).resolved != interview.main_question_limit:
            conflict()
        await close(session, data, now, "full")
        status = 202
    elif (
        action == "end"
        and isinstance(body, EndInterview)
        and (active or paused or interview.status == SessionStatus.DRAFT)
    ):
        if current and current.status == TurnStatus.AWAITING_ANSWER:
            if (
                not body.draft
                or body.draft.turn_id != current.id
                or body.current_answer_action == "none"
            ):
                conflict("interview_turn")
            await resolve_answer(
                session,
                data,
                current,
                body.draft.answer_text,
                body.current_answer_action,
                body.command_key,
                now,
            )
        elif body.current_answer_action != "none" or body.draft is not None:
            conflict("interview_turn")
        if interview.status == SessionStatus.DRAFT:
            interview.status, interview.end_reason, interview.ended_at = (
                SessionStatus.ABANDONED,
                "cancelled_before_start",
                now,
            )
        else:
            await close(session, data, now, "early")
            status = 202
    elif action == "retry" and isinstance(body, RetryInterviewEvaluation) and (active or paused):
        turn = next((t for t in data.turns if t.id == turn_id), None)
        answer = data.answers.get(turn.id) if turn else None
        previous = data.evaluations.get(answer.id) if answer else None
        if (
            not turn
            or not answer
            or not previous
            or previous.id != body.evaluation_id
            or previous.status != EvaluationStatus.FAILED
            or previous.version >= 2
        ):
            conflict("evaluation_retry_limit")
        await queue_evaluation(session, interview, turn, answer, now, previous)
        status = 202
    else:
        conflict()
    interview.revision += 1
    return await record(session, interview, body, operation, status)
