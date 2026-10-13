from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.context import targets
from interview_prep.modules.context.models import TargetStatus
from interview_prep.modules.context.schemas import TargetInput, TargetList, TargetUpdate
from interview_prep.modules.identity.dependencies import require_account
from interview_prep.modules.identity.models import User
from interview_prep.modules.identity.schemas import TargetView

router = APIRouter(
    prefix="/api/v1/account/targets",
    tags=["target-jobs"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
Account = Annotated[User, Depends(require_account)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=TargetList)
async def get_targets(
    user: Account,
    session: Session,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    status: TargetStatus | None = None,
) -> TargetList:
    return await targets.list_targets(session, user.id, offset, limit, status)


@router.post("", response_model=TargetView, status_code=201)
async def create_target(body: TargetInput, user: Account, session: Session) -> TargetView:
    return await targets.create_target(session, user.id, body)


@router.put("/{resource_id}", response_model=TargetView)
async def update_target(
    resource_id: UUID, body: TargetUpdate, user: Account, session: Session
) -> TargetView:
    return await targets.update_target(session, user.id, resource_id, body)


@router.delete("/{resource_id}", status_code=204)
async def delete_target(
    resource_id: UUID,
    user: Account,
    session: Session,
    expected_revision: Annotated[int, Query(ge=1)],
) -> Response:
    await targets.delete_target(session, user.id, resource_id, expected_revision)
    return Response(status_code=204)
