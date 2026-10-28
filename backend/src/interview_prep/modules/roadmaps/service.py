import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.context.models import TargetJob, TargetJobVersion, TargetStatus
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, Profile, User
from interview_prep.modules.interviews.models import EvaluationKind
from interview_prep.modules.progress.loaders import history
from interview_prep.modules.roadmaps.engine import recommend, schedule
from interview_prep.modules.roadmaps.models import (
    ProgressEvent,
    ProgressEventType,
    Roadmap,
    RoadmapItem,
    RoadmapStatus,
    TaskStatus,
)
from interview_prep.modules.roadmaps.schemas import (
    VERSION,
    ChangeItem,
    GenerateRoadmap,
    PlanItem,
    PlanTarget,
    PlanView,
    Recommendation,
    RoadmapWorkspace,
)
from interview_prep.modules.skills.service import skill_matrix


async def lock_owner(session: AsyncSession, owner: UUID) -> None:
    user = await session.scalar(
        select(User)
        .where(User.id == owner)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        not user
        or user.status != PrincipalStatus.ACTIVE
        or (user.expires_at and user.expires_at <= datetime.now(UTC))
    ):
        raise HTTPException(401)


async def plan_view(session: AsyncSession, owner: UUID, plan: Roadmap) -> PlanView:
    items = (
        await session.scalars(
            select(RoadmapItem)
            .where(
                RoadmapItem.owner_id == owner,
                RoadmapItem.roadmap_id == plan.id,
            )
            .order_by(RoadmapItem.position)
            .limit(100)
        )
    ).all()
    snapshot = plan.input_snapshot or {}
    target_id = snapshot.get("target_id")
    priority = snapshot.get("target_priority")
    notices = snapshot.get("notices")
    output = []
    for item in items:
        meta = Recommendation.model_validate(item.recommendation) if item.recommendation else None
        output.append(
            PlanItem(
                id=item.id,
                topic=meta.topic if meta else item.title,
                reason=meta.reason
                if meta
                else "Historical task; no personalized rationale was saved.",
                priority=meta.priority if meta else None,
                objective=meta.objective if meta else None,
                activity=meta.activity if meta else None,
                estimated_minutes=item.estimated_minutes,
                scheduled_on=item.scheduled_on,
                status=item.status.value,
                completed_at=item.completed_at,
            )
        )
    return PlanView(
        id=plan.id,
        revision=plan.revision,
        title=plan.title,
        status=plan.status.value,
        policy_version=plan.policy_version,
        created_at=plan.created_at,
        weekly_minutes=plan.weekly_minutes,
        interview_date=plan.target_date,
        starts_on=plan.starts_on,
        target_id=UUID(target_id) if isinstance(target_id, str) else None,
        target_priority=priority if isinstance(priority, str) else None,
        notices=[n for n in notices if isinstance(n, str)]
        if isinstance(notices, list)
        else ["Historical plan retained without inventing its recommendation inputs."],
        items=output,
    )


async def workspace(session: AsyncSession, user: User) -> RoadmapWorkspace:
    plans = (
        await session.scalars(
            select(Roadmap)
            .where(Roadmap.owner_id == user.id)
            .order_by(Roadmap.created_at.desc(), Roadmap.id)
            .limit(51)
        )
    ).all()
    current = next((p for p in plans if p.status == RoadmapStatus.ACTIVE), None)
    targets = (
        await session.scalars(
            select(TargetJob)
            .where(
                TargetJob.owner_id == user.id,
                TargetJob.status != TargetStatus.ARCHIVED,
            )
            .order_by(TargetJob.title, TargetJob.id)
            .limit(100)
        )
    ).all()
    targets = sorted(
        targets,
        key=lambda t: (("high", "normal", "low").index(t.priority.value), t.title.casefold(), t.id),
    )
    profile = await session.scalar(select(Profile).where(Profile.owner_id == user.id))
    return RoadmapWorkspace(
        mode="demo" if user.kind == PrincipalKind.DEMO else "account",
        current=await plan_view(session, user.id, current) if current else None,
        history=[await plan_view(session, user.id, p) for p in plans if p is not current],
        targets=[PlanTarget(id=t.id, title=t.title, priority=t.priority.value) for t in targets],
        weekly_minutes=profile.weekly_minutes if profile else 240,
        interview_date=profile.target_date if profile else None,
        notices=[
            "Regeneration preserves earlier tasks and completion events. "
            "Reopen a completed historical task to make that activity eligible again.",
            "Weekly time is a planning budget. Effort estimates are editorial, not "
            "measured durations.",
        ],
    )


async def generate(
    session: AsyncSession,
    user: User,
    body: GenerateRoadmap,
) -> RoadmapWorkspace:
    await lock_owner(session, user.id)
    digest = hashlib.sha256(body.model_dump_json(exclude={"command_key"}).encode()).hexdigest()
    existing = await session.scalar(
        select(Roadmap).where(
            Roadmap.owner_id == user.id,
            Roadmap.generation_key == body.command_key,
        )
    )
    if existing:
        if (existing.input_snapshot or {}).get("request_digest") != digest:
            raise HTTPException(409, detail="roadmap_conflict")
        return await workspace(session, user)
    current = await session.scalar(
        select(Roadmap)
        .where(
            Roadmap.owner_id == user.id,
            Roadmap.status == RoadmapStatus.ACTIVE,
        )
        .order_by(Roadmap.created_at.desc(), Roadmap.id)
        .limit(1)
        .with_for_update()
    )
    if (body.expected_id, body.expected_revision) != (
        (current.id, current.revision) if current else (None, None)
    ):
        raise HTTPException(409, detail="roadmap_conflict")
    count = (
        await session.scalar(
            select(func.count())
            .select_from(Roadmap)
            .where(
                Roadmap.owner_id == user.id,
                Roadmap.generation_key.is_not(None),
            )
        )
        or 0
    )
    if count >= 50:
        raise HTTPException(409, detail="roadmap_limit")
    target = None
    version = None
    if body.target_id:
        target = await session.scalar(
            select(TargetJob).where(
                TargetJob.id == body.target_id,
                TargetJob.owner_id == user.id,
                TargetJob.status != TargetStatus.ARCHIVED,
            )
        )
        if target is None:
            raise HTTPException(404)
        version = await session.scalar(
            select(TargetJobVersion)
            .where(
                TargetJobVersion.owner_id == user.id,
                TargetJobVersion.target_job_id == target.id,
            )
            .order_by(TargetJobVersion.version.desc())
            .limit(1)
        )
    profile = await session.scalar(select(Profile).where(Profile.owner_id == user.id))
    timezone = profile.timezone if profile else "UTC"
    local_time = await session.scalar(
        text(
            "SELECT timezone(name, CAST(:at AS timestamptz)) "
            "FROM pg_timezone_names WHERE name = :zone"
        ),
        {"at": datetime.now(UTC), "zone": timezone},
    )
    if not isinstance(local_time, datetime):
        raise HTTPException(422, detail="roadmap_timezone")
    today = local_time.date()
    if body.interview_date and body.interview_date < today:
        raise HTTPException(422, detail="roadmap_date")
    matrix = await skill_matrix(session, user, body.target_id)
    observations = await history(session, user.id)
    old_items = (
        await session.scalars(
            select(RoadmapItem)
            .where(
                RoadmapItem.owner_id == user.id,
                RoadmapItem.status == TaskStatus.COMPLETED,
                RoadmapItem.recommendation.is_not(None),
            )
            .limit(601)
        )
    ).all()
    completed = {Recommendation.model_validate(i.recommendation).key for i in old_items}
    proposals = recommend(
        matrix.rows,
        observations.defense,
        target_priority=target.priority.value if target else None,
        has_target=target is not None,
        interview_count=observations.interviews,
    )
    scheduled, notices = schedule(
        proposals, completed, body.weekly_minutes, today, body.interview_date
    )
    notices.extend(observations.notices)
    notices.extend(matrix.notices)
    if current:
        current.status = RoadmapStatus.ARCHIVED
        current.revision += 1
        await session.flush()
    plan = Roadmap(
        owner_id=user.id,
        generation_key=body.command_key,
        target_job_version_id=version.id if version else None,
        title=f"Preparation: {target.title}"[:200] if target else "Personal preparation plan",
        status=RoadmapStatus.ACTIVE,
        policy_version=VERSION,
        context_version=matrix.policy_version,
        weekly_minutes=body.weekly_minutes,
        timezone=timezone,
        starts_on=today,
        target_date=body.interview_date,
        revision=1,
        input_snapshot={
            "request_digest": digest,
            "target_id": str(target.id) if target else None,
            "target_priority": target.priority.value if target else None,
            "profile_revision": profile.revision if profile else None,
            "skill_rows": len(matrix.rows),
            "completed_interviews": observations.interviews,
            "defense_answers": len(observations.defense),
            "notices": notices,
        },
    )
    session.add(plan)
    await session.flush()
    session.add_all(
        [
            RoadmapItem(
                owner_id=user.id,
                roadmap_id=plan.id,
                title=s.recommendation.topic,
                position=i,
                estimated_minutes=s.minutes,
                scheduled_on=s.scheduled_on,
                status=TaskStatus.PLANNED,
                recommendation=s.recommendation.model_dump(mode="json"),
            )
            for i, s in enumerate(scheduled, 1)
        ]
    )
    await session.commit()
    return await workspace(session, user)


async def change(
    session: AsyncSession,
    user: User,
    identifier: UUID,
    body: ChangeItem,
) -> RoadmapWorkspace:
    await lock_owner(session, user.id)
    item = await session.scalar(
        select(RoadmapItem)
        .where(
            RoadmapItem.owner_id == user.id,
            RoadmapItem.id == identifier,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if item is None:
        raise HTTPException(404)
    plan = await session.scalar(
        select(Roadmap)
        .where(
            Roadmap.owner_id == user.id,
            Roadmap.id == item.roadmap_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if plan is None:
        raise HTTPException(404)
    if plan.revision != body.revision:
        raise HTTPException(409, detail="roadmap_conflict")
    desired = TaskStatus.COMPLETED if body.action == "complete" else TaskStatus.PLANNED
    if item.status != desired:
        item.status = desired
        item.completed_at = datetime.now(UTC) if desired == TaskStatus.COMPLETED else None
        plan.revision += 1
        await session.flush()
        if item.completed_at:
            session.add(
                ProgressEvent(
                    owner_id=user.id,
                    event_type=ProgressEventType.ROADMAP_ITEM_COMPLETED,
                    result_kind=EvaluationKind.SIMULATION
                    if user.kind == PrincipalKind.DEMO
                    else None,
                    roadmap_item_id=item.id,
                    deduplication_key=uuid4(),
                    occurred_at=item.completed_at,
                    details={
                        "policy": VERSION,
                        "meaning": "Recorded task completion, not competence",
                    },
                )
            )
    await session.commit()
    return await workspace(session, user)
