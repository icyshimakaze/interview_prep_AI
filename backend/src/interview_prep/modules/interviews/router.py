from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai.factory import create_provider
from interview_prep.ai.provider import AIProvider
from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import PrincipalKind, User
from interview_prep.modules.interviews import commands, queries
from interview_prep.modules.interviews.models import SessionStatus
from interview_prep.modules.interviews.schemas import (
    AdvanceInterview,
    ConfigureInterview,
    CreateInterview,
    EndInterview,
    InterviewCommandResponse,
    InterviewHistory,
    InterviewMutation,
    InterviewOptions,
    InterviewReview,
    InterviewSessionView,
    InterviewText,
    PauseInterview,
    RetryInterviewEvaluation,
)
from interview_prep.modules.interviews.worker import InterviewRunner

Session = Annotated[AsyncSession, Depends(get_session)]


def selected_provider(request: Request, user: User) -> AIProvider:
    runner: InterviewRunner = request.app.state.interview_runner
    return create_provider(runner.settings, runner.http, demo=user.kind == PrincipalKind.DEMO)


def interview_router(mode: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/v1/{mode}/interviews",
        tags=[f"{mode}-interviews"],
        responses={c: {"model": ErrorResponse} for c in (401, 403, 404, 409, 422, 503)},
    )
    identity = require_account if mode == "account" else require_demo
    mutations = [Depends(require_demo_mutation)] if mode == "demo" else []

    @router.get("/options", response_model=InterviewOptions)
    async def options(
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
        target_id: UUID | None = None,
    ) -> InterviewOptions:
        return await queries.options(session, user.id, selected_provider(request, user), target_id)

    @router.get("", response_model=InterviewHistory)
    async def history(
        user: Annotated[User, Depends(identity)],
        session: Session,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
        status: SessionStatus | None = None,
    ) -> InterviewHistory:
        return await queries.history(session, user.id, offset, limit, status)

    @router.post(
        "", response_model=InterviewCommandResponse, status_code=201, dependencies=mutations
    )
    async def create(
        body: CreateInterview,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        result, response.status_code = await commands.create(
            session, user, body, selected_provider(request, user)
        )
        return result

    @router.get("/{identifier}", response_model=InterviewSessionView)
    async def read(
        identifier: UUID,
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewSessionView:
        result = await queries.read(session, user.id, identifier)
        request.app.state.interview_runner.wake.set()
        return result

    @router.get("/{identifier}/review", response_model=InterviewReview)
    async def review(
        identifier: UUID,
        request: Request,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewReview:
        result = await queries.review(session, user.id, identifier)
        request.app.state.interview_runner.wake.set()
        return result

    async def execute(
        identifier: UUID,
        action: str,
        body: InterviewMutation,
        request: Request,
        response: Response,
        user: User,
        session: AsyncSession,
        turn: UUID | None = None,
    ) -> InterviewCommandResponse:
        result, response.status_code = await commands.mutate(
            session, user, identifier, action, body, selected_provider(request, user), turn
        )
        runner: InterviewRunner = request.app.state.interview_runner
        runner.wake.set()
        return result

    @router.put(
        "/{identifier}/configuration",
        response_model=InterviewCommandResponse,
        dependencies=mutations,
    )
    async def configure(
        identifier: UUID,
        body: ConfigureInterview,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "configure", body, request, response, user, session)

    @router.post(
        "/{identifier}/start", response_model=InterviewCommandResponse, dependencies=mutations
    )
    async def start(
        identifier: UUID,
        body: InterviewMutation,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "start", body, request, response, user, session)

    @router.put(
        "/{identifier}/turns/{turn_id}/draft",
        response_model=InterviewCommandResponse,
        dependencies=mutations,
    )
    async def save(
        identifier: UUID,
        turn_id: UUID,
        body: InterviewText,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "save", body, request, response, user, session, turn_id)

    @router.post(
        "/{identifier}/turns/{turn_id}/submit",
        response_model=InterviewCommandResponse,
        status_code=202,
        dependencies=mutations,
    )
    async def submit(
        identifier: UUID,
        turn_id: UUID,
        body: InterviewText,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "submit", body, request, response, user, session, turn_id)

    @router.post(
        "/{identifier}/turns/{turn_id}/skip",
        response_model=InterviewCommandResponse,
        dependencies=mutations,
    )
    async def skip(
        identifier: UUID,
        turn_id: UUID,
        body: InterviewText,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "skip", body, request, response, user, session, turn_id)

    @router.post(
        "/{identifier}/turns/{turn_id}/followup",
        response_model=InterviewCommandResponse,
        status_code=202,
        dependencies=mutations,
    )
    async def followup(
        identifier: UUID,
        turn_id: UUID,
        body: InterviewMutation,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(
            identifier, "followup", body, request, response, user, session, turn_id
        )

    @router.post(
        "/{identifier}/turns/{turn_id}/evaluation/retry",
        response_model=InterviewCommandResponse,
        status_code=202,
        dependencies=mutations,
    )
    async def retry(
        identifier: UUID,
        turn_id: UUID,
        body: RetryInterviewEvaluation,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "retry", body, request, response, user, session, turn_id)

    @router.post(
        "/{identifier}/advance", response_model=InterviewCommandResponse, dependencies=mutations
    )
    async def advance(
        identifier: UUID,
        body: AdvanceInterview,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "advance", body, request, response, user, session)

    @router.post(
        "/{identifier}/pause", response_model=InterviewCommandResponse, dependencies=mutations
    )
    async def pause(
        identifier: UUID,
        body: PauseInterview,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "pause", body, request, response, user, session)

    @router.post(
        "/{identifier}/resume", response_model=InterviewCommandResponse, dependencies=mutations
    )
    async def resume(
        identifier: UUID,
        body: InterviewMutation,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "resume", body, request, response, user, session)

    @router.post(
        "/{identifier}/complete",
        response_model=InterviewCommandResponse,
        status_code=202,
        dependencies=mutations,
    )
    async def complete(
        identifier: UUID,
        body: InterviewMutation,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "complete", body, request, response, user, session)

    @router.post(
        "/{identifier}/end",
        response_model=InterviewCommandResponse,
        status_code=202,
        dependencies=mutations,
    )
    async def end(
        identifier: UUID,
        body: EndInterview,
        request: Request,
        response: Response,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> InterviewCommandResponse:
        return await execute(identifier, "end", body, request, response, user, session)

    return router


account_router = interview_router("account")
demo_router = interview_router("demo")
