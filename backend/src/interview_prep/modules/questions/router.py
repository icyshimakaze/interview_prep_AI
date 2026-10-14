from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.demo.workspace_router import require_demo_mutation
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.identity.schemas import EmptyRequest
from interview_prep.modules.questions import mutations, queries
from interview_prep.modules.questions.schemas import (
    AttemptHistory,
    BankDetail,
    BankFacets,
    BankFilters,
    BankPage,
    BookmarkState,
    PracticeInput,
    PracticeView,
)

Session = Annotated[AsyncSession, Depends(get_session)]


def bank_router(mode: str) -> APIRouter:
    router = APIRouter(
        prefix=f"/api/v1/{mode}/questions",
        tags=[f"{mode}-questions"],
        responses={code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422)},
    )
    identity = require_account if mode == "account" else require_demo
    mutation_dependencies = [Depends(require_demo_mutation)] if mode == "demo" else []

    @router.get("", response_model=BankPage)
    async def list_bank(
        user: Annotated[User, Depends(identity)],
        session: Session,
        filters: Annotated[BankFilters, Query()],
    ) -> BankPage:
        return await queries.list_questions(session, user.id, filters)

    @router.get("/facets", response_model=BankFacets)
    async def get_facets(user: Annotated[User, Depends(identity)], session: Session) -> BankFacets:
        return await queries.facets(session, user.id)

    @router.get("/{question_id}", response_model=BankDetail)
    async def read_question(
        question_id: UUID, user: Annotated[User, Depends(identity)], session: Session
    ) -> BankDetail:
        return await queries.detail(session, user.id, question_id)

    @router.put(
        "/{question_id}/bookmark", response_model=BookmarkState, dependencies=mutation_dependencies
    )
    async def save_bookmark(
        question_id: UUID,
        body: EmptyRequest,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> BookmarkState:
        return await mutations.set_bookmark(session, user.id, question_id, True)

    @router.delete(
        "/{question_id}/bookmark", response_model=BookmarkState, dependencies=mutation_dependencies
    )
    async def delete_bookmark(
        question_id: UUID, user: Annotated[User, Depends(identity)], session: Session
    ) -> BookmarkState:
        return await mutations.set_bookmark(session, user.id, question_id, False)

    @router.post(
        "/{question_id}/attempts", response_model=PracticeView, dependencies=mutation_dependencies
    )
    async def submit_answer(
        question_id: UUID,
        body: PracticeInput,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> PracticeView:
        return await mutations.submit_practice(session, user, question_id, body)

    @router.get("/{question_id}/attempts", response_model=AttemptHistory)
    async def attempt_history(
        question_id: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
    ) -> AttemptHistory:
        return await queries.history_page(session, user.id, question_id, offset, limit)

    @router.delete(
        "/{question_id}/attempts/{attempt_id}", status_code=204, dependencies=mutation_dependencies
    )
    async def erase_answer(
        question_id: UUID,
        attempt_id: UUID,
        user: Annotated[User, Depends(identity)],
        session: Session,
    ) -> Response:
        await mutations.remove_practice(session, user.id, question_id, attempt_id)
        return Response(status_code=204)

    return router


account_router = bank_router("account")
demo_router = bank_router("demo")
