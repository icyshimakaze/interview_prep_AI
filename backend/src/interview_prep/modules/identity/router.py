from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.identity.dependencies import require_account, verified_identity
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, Profile, User
from interview_prep.modules.identity.queries import dashboard, owned_resume, owned_target
from interview_prep.modules.identity.schemas import (
    DashboardView,
    EmptyRequest,
    ProfileInput,
    ProfileView,
    ResumeView,
    SessionView,
    TargetView,
)
from interview_prep.modules.identity.verification import VerifiedIdentity

router = APIRouter(
    prefix="/api/v1/account",
    tags=["account"],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
Account = Annotated[User, Depends(require_account)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("/session", response_model=SessionView)
async def bootstrap_account(
    body: EmptyRequest,
    identity: Annotated[VerifiedIdentity, Depends(verified_identity)],
    session: Session,
) -> SessionView:
    await session.execute(
        insert(User)
        .values(kind=PrincipalKind.ACCOUNT, issuer=identity.issuer, subject=identity.subject)
        .on_conflict_do_nothing(index_elements=[User.issuer, User.subject])
    )
    user = await session.scalar(
        select(User).where(User.issuer == identity.issuer, User.subject == identity.subject)
    )
    if user is None or user.status != PrincipalStatus.ACTIVE or user.kind != PrincipalKind.ACCOUNT:
        raise HTTPException(status_code=403)
    await session.commit()
    return SessionView()


@router.get("/dashboard", response_model=DashboardView)
async def account_dashboard(user: Account, session: Session) -> DashboardView:
    return await dashboard(session, user)


@router.get("/resumes/{resource_id}", response_model=ResumeView)
async def get_resume(resource_id: UUID, user: Account, session: Session) -> ResumeView:
    return await owned_resume(session, user.id, resource_id)


@router.get("/targets/{resource_id}", response_model=TargetView)
async def get_target(resource_id: UUID, user: Account, session: Session) -> TargetView:
    return await owned_target(session, user.id, resource_id)


@router.put("/profile", response_model=ProfileView, responses={409: {"model": ErrorResponse}})
async def save_profile(body: ProfileInput, user: Account, session: Session) -> ProfileView:
    # Serializes first creation as well as updates from two browser tabs.
    await session.scalar(select(User).where(User.id == user.id).with_for_update())
    profile = await session.scalar(select(Profile).where(Profile.owner_id == user.id))
    if profile is None:
        if body.expected_revision is not None:
            raise HTTPException(status_code=409)
        profile = Profile(owner_id=user.id, revision=1)
        session.add(profile)
    elif body.expected_revision != profile.revision:
        raise HTTPException(status_code=409)
    else:
        profile.revision += 1
    profile.display_name = body.display_name
    profile.target_role = body.target_role.strip()
    profile.experience_band = body.experience_band
    profile.timezone = body.timezone
    profile.weekly_minutes = body.weekly_minutes
    await session.commit()
    await session.refresh(profile)
    return ProfileView.model_validate(profile)
