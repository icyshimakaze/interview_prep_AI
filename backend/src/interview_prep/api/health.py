from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session

router = APIRouter(tags=["health"])
SCHEMA_REVISION = "0002_relational_model"


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"
    service: Literal["interview-prep-api"] = "interview-prep-api"


class ReadinessResponse(HealthResponse):
    database: Literal["connected"] = "connected"
    schema_revision: str = SCHEMA_REVISION


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Process liveness; database readiness is a separate endpoint."""
    return HealthResponse()


@router.get(
    "/api/v1/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ErrorResponse}},
)
async def ready(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> ReadinessResponse:
    try:
        await session.execute(text("SELECT 1"))
        revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != SCHEMA_REVISION:
            raise ValueError("Schema mismatch")
    except Exception:
        # Never expose connection strings, driver errors, or credentials.
        from fastapi import HTTPException

        raise HTTPException(status_code=503) from None
    return ReadinessResponse()
