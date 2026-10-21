from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.demo.router import (
    COOKIE_NAME,
    CSRF_COOKIE_NAME,
    require_demo_credentials,
    settings_from_request,
)
from interview_prep.modules.demo.service import resolve_workspace, verify_csrf
from interview_prep.modules.identity.dependencies import require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.identity.queries import dashboard, owned_resume, owned_target
from interview_prep.modules.identity.schemas import (
    DashboardView,
    EmptyRequest,
    ResumeView,
    RoadmapItemView,
    TargetView,
)
from interview_prep.modules.roadmaps.models import (
    Roadmap,
    RoadmapItem,
)
from interview_prep.modules.roadmaps.schemas import ChangeItem
from interview_prep.modules.roadmaps.service import change, lock_owner

router = APIRouter(
    prefix="/api/v1/demo",
    tags=["demo"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
Demo = Annotated[User, Depends(require_demo)]
Session = Annotated[AsyncSession, Depends(get_session)]


async def require_demo_mutation(request: Request, session: Session, user: Demo) -> None:
    settings = settings_from_request(request)
    if request.headers.get("origin") not in settings.allowed_origins:
        raise HTTPException(status_code=403)
    _, credential = await resolve_workspace(
        session, request.cookies.get(COOKIE_NAME), datetime.now(UTC)
    )
    verify_csrf(credential, request.headers.get("x-csrf-token"))


@router.get("/dashboard", response_model=DashboardView)
async def demo_dashboard(user: Demo, session: Session) -> DashboardView:
    return await dashboard(session, user)


@router.get("/resumes/{resource_id}", response_model=ResumeView)
async def demo_resume(resource_id: UUID, user: Demo, session: Session) -> ResumeView:
    return await owned_resume(session, user.id, resource_id)


@router.get("/targets/{resource_id}", response_model=TargetView)
async def demo_target(resource_id: UUID, user: Demo, session: Session) -> TargetView:
    return await owned_target(session, user.id, resource_id)


@router.patch(
    "/roadmap-items/{resource_id}/complete",
    response_model=RoadmapItemView,
    dependencies=[Depends(require_demo_mutation)],
)
async def complete_demo_task(
    resource_id: UUID, body: EmptyRequest, user: Demo, session: Session
) -> RoadmapItemView:
    await lock_owner(session, user.id)
    item = await session.scalar(
        select(RoadmapItem).where(
            RoadmapItem.id == resource_id,
            RoadmapItem.owner_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404)
    plan = await session.scalar(
        select(Roadmap).where(
            Roadmap.id == item.roadmap_id,
            Roadmap.owner_id == user.id,
        )
    )
    if plan is None:
        raise HTTPException(status_code=404)
    await change(session, user, item.id, ChangeItem(revision=plan.revision, action="complete"))
    await session.refresh(item)
    return RoadmapItemView.model_validate(item)


@router.delete("/session", status_code=204, dependencies=[Depends(require_demo_mutation)])
async def exit_demo(user: Demo, session: Session, response: Response) -> None:
    await session.execute(delete(User).where(User.id == user.id))
    await session.commit()
    response.delete_cookie(COOKIE_NAME, path="/api/v1/demo")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


@router.post("/reset", status_code=204)
async def reset_demo(
    body: EmptyRequest, request: Request, session: Session, response: Response
) -> None:
    """Clear expired credentials; deleting a live workspace still requires its CSRF token."""
    require_demo_credentials(request)
    if request.headers.get("origin") not in settings_from_request(request).allowed_origins:
        raise HTTPException(status_code=403)
    try:
        workspace, credential = await resolve_workspace(
            session, request.cookies.get(COOKIE_NAME), datetime.now(UTC)
        )
    except HTTPException as error:
        if error.status_code != 401:
            raise
    else:
        verify_csrf(credential, request.headers.get("x-csrf-token"))
        await session.execute(delete(User).where(User.id == workspace.id))
        await session.commit()
    response.delete_cookie(COOKIE_NAME, path="/api/v1/demo")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
