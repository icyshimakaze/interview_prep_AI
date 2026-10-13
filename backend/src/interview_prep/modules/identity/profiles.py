from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.identity.models import Profile, ProfileInterest, User
from interview_prep.modules.identity.schemas import ProfileInput, ProfileView


async def profile_view(session: AsyncSession, profile: Profile) -> ProfileView:
    labels = (
        await session.scalars(
            select(ProfileInterest.label)
            .where(
                ProfileInterest.owner_id == profile.owner_id,
                ProfileInterest.profile_id == profile.id,
            )
            .order_by(ProfileInterest.position)
        )
    ).all()
    return ProfileView(
        id=profile.id,
        display_name=profile.display_name,
        target_role=profile.target_role,
        experience_band=profile.experience_band,
        timezone=profile.timezone,
        weekly_minutes=profile.weekly_minutes,
        revision=profile.revision,
        education=profile.education,
        graduation_year=profile.graduation_year,
        interests=list(labels),
        interview_date=profile.target_date,
    )


async def read_profile(session: AsyncSession, owner: UUID) -> ProfileView | None:
    profile = await session.scalar(select(Profile).where(Profile.owner_id == owner))
    return await profile_view(session, profile) if profile else None


async def save_profile(session: AsyncSession, owner: UUID, body: ProfileInput) -> ProfileView:
    # Owner lock serializes create/update/delete; profile identity prevents ABA edits
    # after deletion and re-creation at the same revision number.
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    profile = await session.scalar(select(Profile).where(Profile.owner_id == owner))
    if profile is None:
        if body.expected_revision is not None or body.expected_id is not None:
            raise HTTPException(status_code=409)
        profile = Profile(owner_id=owner, revision=1)
        session.add(profile)
    elif body.expected_revision != profile.revision or body.expected_id != profile.id:
        raise HTTPException(status_code=409)
    else:
        profile.revision += 1
    profile.display_name = body.display_name
    profile.target_role = body.target_role
    profile.experience_band = body.experience_band
    profile.timezone = body.timezone
    profile.weekly_minutes = body.weekly_minutes
    profile.target_date = body.interview_date
    profile.education = body.education
    profile.graduation_year = body.graduation_year
    await session.flush()
    await session.execute(
        delete(ProfileInterest).where(
            ProfileInterest.owner_id == owner, ProfileInterest.profile_id == profile.id
        )
    )
    session.add_all(
        ProfileInterest(owner_id=owner, profile_id=profile.id, label=label, position=position)
        for position, label in enumerate(body.interests)
    )
    await session.commit()
    return await profile_view(session, profile)


async def delete_profile(
    session: AsyncSession, owner: UUID, expected_id: UUID, expected_revision: int
) -> None:
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    profile = await session.scalar(select(Profile).where(Profile.owner_id == owner))
    if profile is None:
        raise HTTPException(status_code=404)
    if profile.id != expected_id or profile.revision != expected_revision:
        raise HTTPException(status_code=409)
    await session.delete(profile)
    await session.commit()
