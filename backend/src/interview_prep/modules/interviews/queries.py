from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai.provider import AIProvider
from interview_prep.modules.assessments.models import AnswerStatus
from interview_prep.modules.context.models import TargetJob
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationStatus,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.interviews.policy import LABELS, VERSION, conflict, feasible, utc_now
from interview_prep.modules.interviews.schemas import (
    InterviewConfiguration,
    InterviewEvaluationView,
    InterviewHistory,
    InterviewInventory,
    InterviewOptions,
    InterviewProgress,
    InterviewProvider,
    InterviewReview,
    InterviewReviewTurn,
    InterviewSessionView,
    InterviewTarget,
    InterviewTurnView,
    InterviewType,
)
from interview_prep.modules.interviews.selection import concepts, pool, validate_target
from interview_prep.modules.interviews.work_models import FollowupContent
from interview_prep.modules.questions.models import QuestionVersion


def descriptor(provider: AIProvider) -> InterviewProvider:
    return InterviewProvider(
        name=provider.name,
        version=provider.version,
        model=provider.model,
        kind=provider.kind,
        disclosure="Demo/simulated practice; not verified competence."
        if provider.kind == "simulation"
        else (
            "AI-assisted practice; question, answer and review criteria are sent to "
            "the configured provider. Requires human review."
        ),
    )


async def owned(
    session: AsyncSession, owner: UUID, identifier: UUID, *, lock: bool = False
) -> InterviewSession:
    query = select(InterviewSession).where(
        InterviewSession.owner_id == owner, InterviewSession.id == identifier
    )
    row = await session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(status_code=404)
    return row


@dataclass
class SessionData:
    interview: InterviewSession
    turns: list[InterviewQuestion]
    answers: dict[UUID, InterviewAnswer]
    evaluations: dict[UUID, AnswerEvaluation]
    versions: dict[UUID, QuestionVersion]
    followups: dict[UUID, FollowupContent]


async def load(session: AsyncSession, interview: InterviewSession) -> SessionData:
    owner, identifier = interview.owner_id, interview.id
    turns = list(
        (
            await session.scalars(
                select(InterviewQuestion)
                .where(
                    InterviewQuestion.session_id == identifier, InterviewQuestion.owner_id == owner
                )
                .order_by(InterviewQuestion.sequence)
            )
        ).all()
    )
    answers = list(
        (
            await session.scalars(
                select(InterviewAnswer).where(
                    InterviewAnswer.owner_id == owner,
                    InterviewAnswer.interview_question_id.in_([t.id for t in turns]),
                )
            )
        ).all()
    )
    evaluations = (
        await session.scalars(
            select(AnswerEvaluation)
            .where(
                AnswerEvaluation.owner_id == owner,
                AnswerEvaluation.interview_answer_id.in_([a.id for a in answers]),
            )
            .order_by(AnswerEvaluation.version)
        )
    ).all()
    versions = (
        await session.scalars(
            select(QuestionVersion).where(
                QuestionVersion.id.in_(
                    [t.question_version_id for t in turns if t.question_version_id]
                )
            )
        )
    ).all()
    followups = (
        await session.scalars(
            select(FollowupContent).where(
                FollowupContent.owner_id == owner, FollowupContent.session_id == identifier
            )
        )
    ).all()
    return SessionData(
        interview,
        turns,
        {a.interview_question_id: a for a in answers},
        {e.interview_answer_id: e for e in evaluations},
        {v.id: v for v in versions},
        {f.id: f for f in followups},
    )


def turn_view(data: SessionData, turn: InterviewQuestion) -> InterviewTurnView:
    answer = data.answers.get(turn.id)
    evaluation = data.evaluations.get(answer.id) if answer else None
    version = data.versions.get(turn.question_version_id) if turn.question_version_id else None
    content = data.followups.get(turn.followup_content_id) if turn.followup_content_id else None
    return InterviewTurnView(
        id=turn.id,
        sequence=turn.sequence,
        main_ordinal=turn.main_ordinal,
        parent_id=turn.parent_question_id,
        kind=turn.source_kind,
        prompt=version.prompt or version.title
        if version
        else content.prompt
        if content
        else "Historical content unavailable.",
        category=version.category or "Uncategorized" if version else "Follow-up",
        difficulty=version.difficulty.value if version and version.difficulty else None,
        status=turn.status.value,
        answer_text=answer.answer_text if answer else None,
        answer_revision=answer.revision if answer else 1,
        answering_ms=turn.answering_ms,
        running_since=turn.running_since,
        context_excerpt=content.excerpt if content else None,
        evaluation_status=evaluation.status.value if evaluation else None,
        evaluation_id=evaluation.id if evaluation else None,
        evaluation_version=evaluation.version if evaluation else None,
    )


def progress(data: SessionData) -> InterviewProgress:
    mains = [t for t in data.turns if t.parent_question_id is None]
    return InterviewProgress(
        requested=data.interview.main_question_limit,
        presented=len(mains),
        resolved=sum(
            t.status != TurnStatus.AWAITING_ANSWER and t.status != TurnStatus.UNANSWERED
            for t in mains
        ),
        answered=sum(
            data.answers[t.id].status == AnswerStatus.SUBMITTED
            for t in mains
            if t.id in data.answers
        ),
        skipped=sum(t.status == TurnStatus.SKIPPED for t in mains),
        followups_reserved=sum(t.followup_decision != "none" for t in mains),
        followups_presented=sum(t.parent_question_id is not None for t in data.turns),
        evaluation_pending=sum(
            e.status in (EvaluationStatus.PENDING, EvaluationStatus.RUNNING)
            for e in data.evaluations.values()
        ),
        evaluation_failed=sum(
            e.status == EvaluationStatus.FAILED for e in data.evaluations.values()
        ),
    )


def view(data: SessionData, now: datetime) -> InterviewSessionView:
    interview = data.interview
    current = next((t for t in data.turns if t.id == interview.current_turn_id), None)
    counts = progress(data)
    expired = bool(
        interview.deadline_at
        and now >= interview.deadline_at
        and interview.status in (SessionStatus.DRAFT, SessionStatus.ACTIVE, SessionStatus.PAUSED)
    )
    phase: str | None = None
    actions: list[str] = []
    if interview.status in (SessionStatus.ACTIVE, SessionStatus.PAUSED):
        phase = (
            "answering"
            if current and current.status == TurnStatus.AWAITING_ANSWER
            else "followup_pending"
            if current and current.followup_decision == "pending"
            else "between_questions"
        )
    if not expired and interview.contract_version == VERSION:
        if interview.status == SessionStatus.DRAFT:
            actions = ["configure", "start", "end"]
        elif interview.status == SessionStatus.PAUSED:
            actions = ["resume", "end"]
        elif interview.status == SessionStatus.ACTIVE:
            actions = ["pause", "end"]
            if phase == "answering":
                actions += ["save", "submit", "skip"]
            elif current:
                if counts.presented < counts.requested:
                    actions.append("advance_main")
                if (
                    current.parent_question_id is None
                    and current.status not in (TurnStatus.SKIPPED, TurnStatus.UNANSWERED)
                    and current.followup_decision == "none"
                    and counts.followups_reserved < 3
                ):
                    actions.append("followup")
                if current.followup_decision == "ready":
                    actions.append("advance_followup")
                if counts.resolved == counts.requested:
                    actions.append("complete")
    if interview.contract_version != VERSION or interview.status in (
        SessionStatus.FINALIZING,
        SessionStatus.COMPLETED,
        SessionStatus.ABANDONED,
        SessionStatus.FAILED,
    ):
        actions = ["review"]
    if (
        not expired
        and interview.status in (SessionStatus.ACTIVE, SessionStatus.PAUSED)
        and current
        and current.parent_question_id is None
    ):
        answer = data.answers.get(current.id)
        evaluation = data.evaluations.get(answer.id) if answer else None
        if evaluation and evaluation.status == EvaluationStatus.FAILED and evaluation.version < 2:
            actions.append("retry_evaluation")
    provider = (
        InterviewProvider.model_validate(interview.provider_descriptor)
        if interview.provider_descriptor
        else InterviewProvider(
            name=interview.provider,
            version="legacy",
            model=interview.model,
            kind="simulation" if interview.provider == "fictional_fixture" else "legacy",
            disclosure="Historical example; see its original provenance.",
        )
    )
    title = (interview.selection_context or {}).get("target_title")
    notices = [
        "Practice feedback does not validate competence or predict hiring outcomes.",
        "Timing may include time away when you did not explicitly pause.",
    ]
    if current and current.selection_trace:
        trace_notices = current.selection_trace.get("notices")
        if isinstance(trace_notices, list):
            notices.extend(n for n in trace_notices if isinstance(n, str))
        choices = current.selection_trace.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            notices.extend(str(r) for r in choices[0].get("reasons", []) if isinstance(r, str))
    return InterviewSessionView(
        id=interview.id,
        revision=interview.revision,
        contract_version=interview.contract_version,
        status=interview.status.value,
        phase=phase,
        configuration=InterviewConfiguration.model_validate(interview.configuration)
        if interview.configuration
        else None,
        provider=provider,
        target_title=title if isinstance(title, str) else None,
        started_at=interview.started_at,
        deadline_at=interview.deadline_at,
        ended_at=interview.ended_at,
        completed_at=interview.completed_at,
        end_reason=interview.end_reason,
        expired=expired,
        server_time=now,
        current_turn=turn_view(data, current) if current else None,
        followup_decision=current.followup_decision if current else "none",
        progress=counts,
        allowed_actions=actions,
        notices=notices,
    )


async def read(session: AsyncSession, owner: UUID, identifier: UUID) -> InterviewSessionView:
    return view(await load(session, await owned(session, owner, identifier)), utc_now())


async def history(
    session: AsyncSession, owner: UUID, offset: int, limit: int, status: SessionStatus | None
) -> InterviewHistory:
    predicates = [InterviewSession.owner_id == owner]
    if status:
        predicates.append(InterviewSession.status == status)
    total = (
        await session.scalar(select(func.count()).select_from(InterviewSession).where(*predicates))
        or 0
    )
    rows = (
        await session.scalars(
            select(InterviewSession)
            .where(*predicates)
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    items = []
    for row in rows:
        item = view(await load(session, row), utc_now())
        items.append(item.model_copy(update={"current_turn": None}))
    return InterviewHistory(items=items, total=total, offset=offset, limit=limit)


async def options(
    session: AsyncSession, owner: UUID, provider: AIProvider, target_id: UUID | None
) -> InterviewOptions:
    await validate_target(session, owner, target_id)
    inventory = []
    for type_ in InterviewType:
        versions = await pool(
            session,
            owner,
            InterviewConfiguration(
                interview_type=type_, question_count=2 if type_ == InterviewType.FULL_STACK else 1
            ),
        )
        for difficulty in ("auto", "easy", "medium", "hard"):
            categories = [
                v.category or ""
                for v in versions
                if difficulty == "auto" or v.difficulty == difficulty
            ]
            max_count = max(
                (
                    n
                    for n in range(1, 11)
                    if (type_ != InterviewType.FULL_STACK or n >= 2)
                    and feasible(type_, categories, n)
                ),
                default=0,
            )
            inventory.append(
                InterviewInventory(
                    interview_type=type_,
                    label=LABELS[type_],
                    difficulty=difficulty,
                    available_count=len(categories),
                    max_questions=max_count,
                    min_questions=2 if type_ == InterviewType.FULL_STACK else 1,
                )
            )
    targets = (
        await session.scalars(
            select(TargetJob)
            .where(TargetJob.owner_id == owner)
            .order_by(TargetJob.title)
            .limit(100)
        )
    ).all()
    return InterviewOptions(
        inventory=inventory,
        provider=descriptor(provider),
        targets=[InterviewTarget(id=t.id, title=t.title) for t in targets],
        notices=[
            "Counts reflect published typed questions; specialized coverage is limited.",
            "Main question count excludes up to three optional follow-ups.",
            "Answers are stored privately. Account history has no automatic deletion; "
            "demo data expires with its workspace.",
        ],
    )


async def review(session: AsyncSession, owner: UUID, identifier: UUID) -> InterviewReview:
    interview = await owned(session, owner, identifier)
    if interview.contract_version == VERSION and interview.status not in (
        SessionStatus.FINALIZING,
        SessionStatus.COMPLETED,
        SessionStatus.ABANDONED,
        SessionStatus.FAILED,
    ):
        conflict()
    data = await load(session, interview)
    turns = []
    submitted = evaluated = 0
    for turn in data.turns:
        answer = data.answers.get(turn.id)
        result = data.evaluations.get(answer.id) if answer else None
        expected, rubric = (
            await concepts(session, turn.question_version_id)
            if turn.question_version_id
            else ([], [])
        )
        content = data.followups.get(turn.followup_content_id) if turn.followup_content_id else None
        if turn.parent_question_id is None and answer and answer.status == AnswerStatus.SUBMITTED:
            submitted += 1
            evaluated += bool(result and result.status == EvaluationStatus.COMPLETED)
        turns.append(
            InterviewReviewTurn(
                turn=turn_view(data, turn),
                expected_concepts=expected,
                rubric=rubric,
                rationale=content.rationale if content else None,
                evaluation=InterviewEvaluationView(
                    id=result.id,
                    version=result.version,
                    status=result.status.value,
                    kind=result.kind.value,
                    score=result.score,
                    score_scale_max=result.score_scale_max,
                    feedback=result.feedback,
                    error_code=result.error_code,
                    provider=result.provider,
                    model=result.model,
                    prompt_version=result.prompt_version,
                )
                if result
                else None,
            )
        )
    return InterviewReview(
        session=view(data, utc_now()),
        review_status="provisional" if interview.status == SessionStatus.FINALIZING else "final",
        evaluation_coverage="none"
        if evaluated == 0
        else "complete"
        if evaluated == submitted
        else "partial",
        submitted_main=submitted,
        evaluated_main=evaluated,
        unasked_main=max(0, interview.main_question_limit - progress(data).presented),
        turns=turns,
        notices=[
            "No overall readiness score is calculated. Skips, unanswered drafts "
            "and unavailable evaluations are distinct from zero.",
            "Follow-up answers are unscored practice because no reviewed scoring rubric exists.",
        ],
    )
