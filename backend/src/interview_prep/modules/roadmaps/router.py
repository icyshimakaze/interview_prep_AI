from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.progress.schemas import ProgressAnalytics
from interview_prep.modules.progress.service import analytics
from interview_prep.modules.roadmaps import service
from interview_prep.modules.roadmaps.schemas import ChangeItem, GenerateRoadmap, RoadmapWorkspace

Session = Annotated[AsyncSession, Depends(get_session)]


def planning_router(mode: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/v1/{mode}",
        tags=[f"{mode}-planning"],
        responses={c: {"model": ErrorResponse} for c in (401, 403, 404, 409, 422)},
    )
    identity = require_account if mode == "account" else require_demo
    mutations = [Depends(require_demo_mutation)] if mode == "demo" else []

    @router.get("/roadmap", response_model=RoadmapWorkspace)
    async def read(user: Annotated[User, Depends(identity)], session: Session) -> RoadmapWorkspace:
        return await service.workspace(session, user)

    @router.post("/roadmap/generate", response_model=RoadmapWorkspace, dependencies=mutations)
    async def generate(
        body: GenerateRoadmap,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> RoadmapWorkspace:
        return await service.generate(session, user, body)

    @router.post(
        "/roadmap/items/{identifier}", response_model=RoadmapWorkspace, dependencies=mutations
    )
    async def change(
        identifier: UUID,
        body: ChangeItem,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> RoadmapWorkspace:
        return await service.change(session, user, identifier, body)

    @router.get("/progress", response_model=ProgressAnalytics)
    async def progress(
        user: Annotated[User, Depends(identity)], session: Session
    ) -> ProgressAnalytics:
        return await analytics(session, user)

    return router


account_router = planning_router("account")
demo_router = planning_router("demo")
