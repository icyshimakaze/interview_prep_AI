from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.core.quotas import reserve
from interview_prep.db.session import get_session
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.projects import defense, service
from interview_prep.modules.projects.example import example_archive
from interview_prep.modules.projects.ingestion import ProjectImporter, github_archive, read_zip
from interview_prep.modules.projects.schemas import (
    DefenseCommand,
    DefenseHistory,
    DefenseView,
    GithubInput,
    ProjectDetail,
    ProjectList,
    StartDefense,
)

Session = Annotated[AsyncSession, Depends(get_session)]


def project_router(mode: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/v1/{mode}/projects",
        tags=[f"{mode}-projects"],
        responses={c: {"model": ErrorResponse} for c in (401, 403, 404, 409, 413, 422, 503)},
    )
    identity = require_account if mode == "account" else require_demo
    mutations = [Depends(require_demo_mutation)] if mode == "demo" else []

    @router.get("", response_model=ProjectList)
    async def listing(user: Annotated[User, Depends(identity)], session: Session) -> ProjectList:
        return await service.list_projects(session, user.id)

    @router.post("/github", response_model=ProjectDetail, dependencies=mutations)
    async def github(
        body: GithubInput,
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ProjectDetail:
        importer: ProjectImporter = request.app.state.project_importer
        await reserve(
            request.app.state.session_factory, request.app.state.settings, user.id, "import"
        )
        async with importer.slot():
            data, owner, repository, sha = await github_archive(importer.http, body.url)
            parsed = await importer.parse(data)
            return await service.save_snapshot(
                session, user.id, data, parsed, owner, repository, sha
            )

    @router.post("/zip", response_model=ProjectDetail, dependencies=mutations)
    async def upload(
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ProjectDetail:
        importer: ProjectImporter = request.app.state.project_importer
        await reserve(
            request.app.state.session_factory, request.app.state.settings, user.id, "import"
        )
        async with importer.slot():
            data = await read_zip(request)
            return await service.save_snapshot(session, user.id, data, await importer.parse(data))

    @router.post("/example", response_model=ProjectDetail, dependencies=mutations)
    async def example(
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ProjectDetail:
        importer: ProjectImporter = request.app.state.project_importer
        await reserve(
            request.app.state.session_factory, request.app.state.settings, user.id, "import"
        )
        async with importer.slot():
            data = example_archive()
            return await service.save_snapshot(
                session,
                user.id,
                data,
                await importer.parse(data),
                example=True,
            )

    @router.get("/defense/{identifier}", response_model=DefenseView)
    async def read_run(
        identifier: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> DefenseView:
        return await defense.view(session, user.id, identifier)

    @router.post("/defense/{identifier}", response_model=DefenseView, dependencies=mutations)
    async def command(
        identifier: UUID,
        body: DefenseCommand,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> DefenseView:
        return await defense.command(session, user.id, identifier, body)

    @router.get("/{identifier}", response_model=ProjectDetail)
    async def read(
        identifier: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> ProjectDetail:
        return await service.detail(session, user.id, identifier)

    @router.delete("/{identifier}", status_code=204, dependencies=mutations)
    async def remove(
        identifier: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> Response:
        await service.remove(session, user.id, identifier)
        return Response(status_code=204)

    @router.get("/{identifier}/defense", response_model=DefenseHistory)
    async def history(
        identifier: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> DefenseHistory:
        return await defense.history(session, user.id, identifier)

    @router.post("/{identifier}/defense", response_model=DefenseView, dependencies=mutations)
    async def start(
        identifier: UUID,
        body: StartDefense,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> DefenseView:
        return await defense.start(session, user.id, identifier, body)

    return router


account_router = project_router("account")
demo_router = project_router("demo")
