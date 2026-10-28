from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.core.errors import ErrorResponse
from interview_prep.db.readiness import SCHEMA_REVISION as SCHEMA_REVISION
from interview_prep.db.readiness import verify_schema
from interview_prep.db.session import get_session

router = APIRouter(tags=["health"])


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
        revision = await verify_schema(
            session, require_auth=request.app.state.settings.auth_provider == "better_auth"
        )
    except Exception:
        # Never expose connection strings, driver errors, or credentials.
        from fastapi import HTTPException

        raise HTTPException(status_code=503) from None
    return ReadinessResponse(schema_revision=revision)
