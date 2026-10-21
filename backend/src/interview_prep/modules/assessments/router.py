import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.assessments import queries, service
from interview_prep.modules.assessments.evaluation import EvaluationProvider, MockAIProvider
from interview_prep.modules.assessments.schemas import (
    AttemptPage,
    AttemptView,
    Options,
    ResponseInput,
    RevisionInput,
    StartInput,
)
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User

Session = Annotated[AsyncSession, Depends(get_session)]


def evaluation_provider(request: Request) -> EvaluationProvider:
    provider: EvaluationProvider = request.app.state.evaluation_provider
    return provider


def demo_evaluation_provider() -> EvaluationProvider:
    return MockAIProvider()


def assessment_router(mode: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/v1/{mode}/assessments",
        tags=[f"{mode}-assessments"],
        responses={code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 503)},
    )
    identity = require_account if mode == "account" else require_demo
    mutations = [Depends(require_demo_mutation)] if mode == "demo" else []
    provider_dependency = evaluation_provider if mode == "account" else demo_evaluation_provider

    @router.get("/options", response_model=Options)
    async def configuration_options(
        user: Annotated[User, Depends(identity)],
        session: Session,
        provider: Annotated[EvaluationProvider, Depends(provider_dependency)],
    ) -> Options:
        available = await queries.options(session, user.id)
        available.conceptual_provider = provider.name
        available.conceptual_kind = provider.kind
        return available

    @router.get("", response_model=AttemptPage)
    async def history(
        user: Annotated[User, Depends(identity)],
        session: Session,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
    ) -> AttemptPage:
        return await queries.history(session, user.id, offset, limit)

    @router.post("", response_model=AttemptView, dependencies=mutations)
    async def start(
        body: StartInput, user: Annotated[User, Depends(identity)], session: Session
    ) -> AttemptView:
        return await service.start(session, user.id, body)

    @router.get("/{identifier}", response_model=AttemptView)
    async def read(
        identifier: UUID, user: Annotated[User, Depends(identity)], session: Session
    ) -> AttemptView:
        return await queries.read(session, user.id, identifier)

    @router.put(
        "/{identifier}/questions/{question_id}", response_model=AttemptView, dependencies=mutations
    )
    async def save(
        identifier: UUID,
        question_id: UUID,
        body: ResponseInput,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> AttemptView:
        return await service.save(session, user.id, identifier, question_id, body)

    @router.post("/{identifier}/submit", response_model=AttemptView, dependencies=mutations)
    async def submit(
        identifier: UUID,
        body: RevisionInput,
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
        provider: Annotated[EvaluationProvider, Depends(provider_dependency)],
    ) -> AttemptView:
        if provider.kind == "model_assisted":
            slots: asyncio.Semaphore = request.app.state.assessment_slots
            if slots.locked():
                raise HTTPException(503)
            async with slots:
                return await service.submit(session, user.id, identifier, body.revision, provider)
        return await service.submit(session, user.id, identifier, body.revision, provider)

    @router.post("/{identifier}/abandon", response_model=AttemptView, dependencies=mutations)
    async def abandon(
        identifier: UUID,
        body: RevisionInput,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> AttemptView:
        return await service.abandon(session, user.id, identifier, body.revision)

    return router


account_router = assessment_router("account")
demo_router = assessment_router("demo")
