from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.config import Settings
from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.demo.schemas import CreateDemoRequest, DemoWorkspaceResponse
from interview_prep.modules.demo.seeding import initialize_demo
from interview_prep.modules.demo.service import create_workspace, resolve_workspace, verify_csrf

COOKIE_NAME = "interview_prep_demo"
CSRF_COOKIE_NAME = "interview_prep_csrf"
router = APIRouter(prefix="/api/v1/demo", tags=["demo"], responses={401: {"model": ErrorResponse}})


def settings_from_request(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def require_demo_credentials(request: Request) -> None:
    # Never reinterpret an account credential as a guest/demo credential.
    if "authorization" in request.headers:
        raise HTTPException(status_code=403)


@router.post(
    "/sessions",
    response_model=DemoWorkspaceResponse,
    responses={403: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def create_demo(
    body: CreateDemoRequest,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(settings_from_request)],
) -> DemoWorkspaceResponse:
    require_demo_credentials(request)
    if request.headers.get("origin") not in settings.allowed_origins:
        raise HTTPException(status_code=403)
    now = datetime.now(UTC)
    existing_token = request.cookies.get(COOKIE_NAME)
    if existing_token is not None:
        workspace, credential = await resolve_workspace(session, existing_token, now)
        verify_csrf(credential, request.headers.get("x-csrf-token"))
        await initialize_demo(session, workspace.id, now)
        await session.commit()
        return DemoWorkspaceResponse.model_validate(workspace)

    # No input fields or external content are accepted during foundation bootstrap.
    address = request.client.host if request.client else "unknown"
    workspace, token, csrf_token = await create_workspace(session, settings, address, now)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.demo_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/api/v1/demo",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=settings.demo_ttl_seconds,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return DemoWorkspaceResponse.model_validate(workspace)


@router.get("/workspace", response_model=DemoWorkspaceResponse)
async def get_workspace(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> DemoWorkspaceResponse:
    require_demo_credentials(request)
    workspace, _ = await resolve_workspace(
        session, request.cookies.get(COOKIE_NAME), datetime.now(UTC)
    )
    return DemoWorkspaceResponse.model_validate(workspace)
