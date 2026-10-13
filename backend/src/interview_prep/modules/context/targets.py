from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.context.models import TargetJob, TargetJobVersion, TargetStatus
from interview_prep.modules.context.schemas import TargetInput, TargetList, TargetUpdate
from interview_prep.modules.identity.models import User
from interview_prep.modules.identity.queries import owned_target
from interview_prep.modules.identity.schemas import TargetView

MAX_TARGETS = 100


async def list_targets(
    session: AsyncSession, owner: UUID, offset: int, limit: int, status: TargetStatus | None
) -> TargetList:
    criteria = [TargetJob.owner_id == owner]
    if status is not None:
        criteria.append(TargetJob.status == status)
    total = await session.scalar(select(func.count()).select_from(TargetJob).where(*criteria)) or 0
    ids = (
        await session.scalars(
            select(TargetJob.id)
            .where(*criteria)
            .order_by(TargetJob.created_at.desc(), TargetJob.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return TargetList(
        items=[await owned_target(session, owner, id) for id in ids],
        total=total,
        offset=offset,
        limit=limit,
    )


def set_metadata(target: TargetJob, body: TargetInput) -> None:
    target.title = body.title
    target.organization = body.organization
    target.source_url = body.source_url
    target.notes = body.notes
    target.priority = body.priority
    target.status = body.status


async def create_target(session: AsyncSession, owner: UUID, body: TargetInput) -> TargetView:
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    count = (
        await session.scalar(
            select(func.count()).select_from(TargetJob).where(TargetJob.owner_id == owner)
        )
        or 0
    )
    if count >= MAX_TARGETS:
        raise HTTPException(status_code=409, detail="target_limit")
    target = TargetJob(owner_id=owner)
    set_metadata(target, body)
    session.add(target)
    await session.flush()
    session.add(
        TargetJobVersion(
            owner_id=owner, target_job_id=target.id, version=1, description=body.description
        )
    )
    await session.flush()
    result = await owned_target(session, owner, target.id)
    await session.commit()
    return result


async def locked_target(session: AsyncSession, owner: UUID, id: UUID, revision: int) -> TargetJob:
    target = await session.scalar(
        select(TargetJob).where(TargetJob.owner_id == owner, TargetJob.id == id).with_for_update()
    )
    if target is None:
        raise HTTPException(status_code=404)
    if target.revision != revision:
        raise HTTPException(status_code=409)
    return target


async def update_target(
    session: AsyncSession, owner: UUID, id: UUID, body: TargetUpdate
) -> TargetView:
    target = await locked_target(session, owner, id, body.expected_revision)
    latest = await session.scalar(
        select(TargetJobVersion)
        .where(TargetJobVersion.owner_id == owner, TargetJobVersion.target_job_id == id)
        .order_by(TargetJobVersion.version.desc())
        .limit(1)
    )
    set_metadata(target, body)
    target.revision += 1
    if latest is None or latest.description != body.description:
        session.add(
            TargetJobVersion(
                owner_id=owner,
                target_job_id=id,
                version=latest.version + 1 if latest else 1,
                description=body.description,
            )
        )
    await session.flush()
    result = await owned_target(session, owner, id)
    await session.commit()
    return result


async def delete_target(session: AsyncSession, owner: UUID, id: UUID, revision: int) -> None:
    target = await locked_target(session, owner, id, revision)
    await session.delete(target)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if getattr(error.orig, "sqlstate", None) == "23503":
            raise HTTPException(status_code=409, detail="target_in_use") from None
        raise
