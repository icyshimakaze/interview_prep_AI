"""Explicit sharing consent and authenticated ownership before analysis dispatch."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai import analyses, context_reviews
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.schemas import (
    AnswerEvaluation,
    JobAnalysis,
    ProjectQuestions,
    ProviderResult,
    ResumeAnalysis,
    Roadmap,
)
from interview_prep.core.errors import ErrorResponse
from interview_prep.db.session import get_session
from interview_prep.modules.identity.dependencies import require_account
from interview_prep.modules.identity.models import User

router = APIRouter(
    prefix="/api/v1/account/ai",
    tags=["account-ai"],
    responses={code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 429, 503)},
)
Account = Annotated[User, Depends(require_account)]
Session = Annotated[AsyncSession, Depends(get_session)]


class AnalysisConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent: Literal[True]
    provider_version: str = Field(min_length=1, max_length=100)


class AnalysisOptions(BaseModel):
    name: str
    version: str
    kind: Literal["simulation", "model_assisted"]
    disclosure: str


@router.get("/options", response_model=AnalysisOptions)
async def options(request: Request, user: Account) -> AnalysisOptions:
    provider: AIProvider = request.app.state.ai_provider
    destination = (
        "xKiro and its downstream model provider"
        if provider.name == "XkiroProvider"
        else "OpenAI"
        if provider.name == "OpenAIProvider"
        else "the configured Ollama server"
    )
    return AnalysisOptions(
        name=provider.name,
        version=provider.version,
        kind=provider.kind,
        disclosure=(
            "Deterministic mock simulation; no external AI call."
            if provider.kind == "simulation"
            else f"Requesting review sends retained resume claims/excerpts, or the selected saved "
            f"Project Defense question, answer and rubric, to {destination}. "
            "Job reviews share the saved description. Roadmap reviews share up to six task "
            "topics and evidence-based reasons. Project questions share bounded static facts "
            "and file references; no raw archive is sent. "
            "Third-party retention policies apply. Remove sensitive details first."
        ),
    )


def configured(request: Request, body: AnalysisConsent) -> AIProvider:
    provider: AIProvider = request.app.state.ai_provider
    if provider.version != body.provider_version:
        raise HTTPException(409, detail="ai_provider_changed")
    return provider


@router.post("/targets/{identifier}", response_model=ProviderResult[JobAnalysis])
async def target_review(
    identifier: UUID,
    body: AnalysisConsent,
    request: Request,
    user: Account,
    session: Session,
) -> ProviderResult[JobAnalysis]:
    return await context_reviews.job_review(
        session,
        request.app.state.session_factory,
        request.app.state.settings,
        user.id,
        identifier,
        configured(request, body),
    )


@router.post("/roadmaps/{identifier}", response_model=ProviderResult[Roadmap])
async def roadmap_review(
    identifier: UUID,
    body: AnalysisConsent,
    request: Request,
    user: Account,
    session: Session,
) -> ProviderResult[Roadmap]:
    return await context_reviews.roadmap_review(
        session,
        request.app.state.session_factory,
        request.app.state.settings,
        user.id,
        identifier,
        configured(request, body),
    )


@router.post("/projects/{identifier}", response_model=ProviderResult[ProjectQuestions])
async def project_questions(
    identifier: UUID,
    body: AnalysisConsent,
    request: Request,
    user: Account,
    session: Session,
) -> ProviderResult[ProjectQuestions]:
    return await context_reviews.project_questions(
        session,
        request.app.state.session_factory,
        request.app.state.settings,
        user.id,
        identifier,
        configured(request, body),
    )


@router.post("/resumes/{identifier}", response_model=ProviderResult[ResumeAnalysis])
async def resume_review(
    identifier: UUID,
    body: AnalysisConsent,
    request: Request,
    user: Account,
    session: Session,
) -> ProviderResult[ResumeAnalysis]:
    return await analyses.resume_analysis(
        session,
        request.app.state.session_factory,
        request.app.state.settings,
        user.id,
        identifier,
        configured(request, body),
    )


@router.post("/defense/{identifier}/{position}", response_model=ProviderResult[AnswerEvaluation])
async def defense_review(
    identifier: UUID,
    position: Annotated[int, Path(ge=1, le=10)],
    body: AnalysisConsent,
    request: Request,
    user: Account,
    session: Session,
) -> ProviderResult[AnswerEvaluation]:
    return await analyses.defense_feedback(
        session,
        request.app.state.session_factory,
        request.app.state.settings,
        user.id,
        identifier,
        position,
        configured(request, body),
    )
