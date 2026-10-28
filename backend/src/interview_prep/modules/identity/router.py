from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.identity import profiles
from interview_prep.modules.identity.accounts import bootstrap_account as bootstrap_principal
from interview_prep.modules.identity.dependencies import require_account, verified_identity
from interview_prep.modules.identity.models import PrincipalKind, PrincipalStatus, User
from interview_prep.modules.identity.queries import dashboard, owned_target
from interview_prep.modules.identity.schemas import (
    DashboardView,
    EmptyRequest,
    ProfileInput,
    ProfileView,
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
    request: Request,
    body: EmptyRequest,
    identity: Annotated[VerifiedIdentity, Depends(verified_identity)],
    session: Session,
) -> SessionView:
    user = await bootstrap_principal(
        session, identity, bindings=request.app.state.settings.auth_provider == "better_auth"
    )
    if user is None or user.status != PrincipalStatus.ACTIVE or user.kind != PrincipalKind.ACCOUNT:
        raise HTTPException(status_code=403)
    await session.commit()
    return SessionView()


@router.get("/dashboard", response_model=DashboardView)
async def account_dashboard(user: Account, session: Session) -> DashboardView:
    return await dashboard(session, user)


@router.get("/targets/{resource_id}", response_model=TargetView)
async def get_target(resource_id: UUID, user: Account, session: Session) -> TargetView:
    return await owned_target(session, user.id, resource_id)


@router.put("/profile", response_model=ProfileView, responses={409: {"model": ErrorResponse}})
async def save_profile(body: ProfileInput, user: Account, session: Session) -> ProfileView:
    return await profiles.save_profile(session, user.id, body)


@router.get("/profile", response_model=ProfileView | None)
async def get_profile(user: Account, session: Session) -> ProfileView | None:
    return await profiles.read_profile(session, user.id)


@router.delete(
    "/profile",
    status_code=204,
    responses={409: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def remove_profile(
    user: Account,
    session: Session,
    expected_id: UUID,
    expected_revision: Annotated[int, Query(ge=1)],
) -> Response:
    await profiles.delete_profile(session, user.id, expected_id, expected_revision)
    return Response(status_code=204)
