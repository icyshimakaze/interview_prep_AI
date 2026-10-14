from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.identity.dependencies import require_account, require_demo
from interview_prep.modules.identity.models import User
from interview_prep.modules.skills.schemas import SkillMatrix
from interview_prep.modules.skills.service import skill_matrix

router = APIRouter(
    tags=["skill-evidence"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/api/v1/account/skill-evidence", response_model=SkillMatrix)
async def account_skill_matrix(
    user: Annotated[User, Depends(require_account)],
    session: Session,
    target_id: UUID | None = None,
) -> SkillMatrix:
    return await skill_matrix(session, user, target_id)


@router.get("/api/v1/demo/skill-evidence", response_model=SkillMatrix)
async def demo_skill_matrix(
    user: Annotated[User, Depends(require_demo)],
    session: Session,
    target_id: UUID | None = None,
) -> SkillMatrix:
    return await skill_matrix(session, user, target_id)
