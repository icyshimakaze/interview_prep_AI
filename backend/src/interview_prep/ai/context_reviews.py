"""Opt-in suggestions from owned saved context, without replacing local policies."""

import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.ai.analyses import saved
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.schemas import (
    JobAnalysis,
    JobInput,
    ProjectInput,
    ProjectQuestions,
    ProviderResult,
    Roadmap,
    RoadmapInput,
)
from interview_prep.core.config import Settings
from interview_prep.modules.context.models import TargetJobVersion
from interview_prep.modules.projects import service as projects
from interview_prep.modules.projects.models import ProjectFact, SourceFile
from interview_prep.modules.roadmaps import service as plans
from interview_prep.modules.roadmaps.models import Roadmap as SavedPlan


async def job_review(
    session: AsyncSession,
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    identifier: UUID,
    provider: AIProvider,
) -> ProviderResult[JobAnalysis]:
    version = await session.scalar(
        select(TargetJobVersion)
        .where(
            TargetJobVersion.owner_id == owner,
            TargetJobVersion.target_job_id == identifier,
        )
        .order_by(TargetJobVersion.version.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(404)
    content = JobInput(text=version.description)
    source = version.id
    await session.rollback()
    return await saved(
        factory,
        settings,
        owner,
        provider,
        content,
        JobAnalysis,
        lambda: provider.analyze_job_description(content),
        target_version_id=source,
    )


async def roadmap_review(
    session: AsyncSession,
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    identifier: UUID,
    provider: AIProvider,
) -> ProviderResult[Roadmap]:
    plan = await session.scalar(
        select(SavedPlan).where(
            SavedPlan.owner_id == owner,
            SavedPlan.id == identifier,
        )
    )
    if plan is None:
        raise HTTPException(404)
    view = await plans.plan_view(session, owner, plan)
    # Existing reasons combine eligible assessment results, resume evidence and
    # job requirements. Send those summaries, never IDs, raw answers or biography.
    topics: dict[str, dict[str, str | None]] = {}
    for item in view.items:
        if item.status not in {"completed", "skipped"} and len(item.topic) <= 100:
            topics.setdefault(
                item.topic.casefold(),
                {
                    "topic": item.topic,
                    "reason": item.reason,
                    "objective": item.objective,
                },
            )
    selected = list(topics.values())[:6]
    if not selected:
        raise HTTPException(422, detail="ai_no_review_context")
    content = RoadmapInput(
        topics=[str(item["topic"]) for item in selected],
        weekly_minutes=min(plan.weekly_minutes, 600),
        context=json.dumps(selected, ensure_ascii=False),
    )
    revision = plan.revision
    await session.rollback()
    return await saved(
        factory,
        settings,
        owner,
        provider,
        content,
        Roadmap,
        lambda: provider.recommend_roadmap(content),
        roadmap_id=identifier,
        source_revision=revision,
    )


async def project_questions(
    session: AsyncSession,
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    owner: UUID,
    identifier: UUID,
    provider: AIProvider,
) -> ProviderResult[ProjectQuestions]:
    _, analysis = await projects.owned(session, owner, identifier)
    rows = (
        await session.execute(
            select(ProjectFact, SourceFile.path)
            .join(
                SourceFile,
                SourceFile.id == ProjectFact.source_file_id,
            )
            .where(
                ProjectFact.owner_id == owner,
                ProjectFact.analysis_id == analysis.id,
                SourceFile.owner_id == owner,
                SourceFile.analysis_id == analysis.id,
            )
            .order_by(SourceFile.path, ProjectFact.line_start, ProjectFact.id)
            .limit(30)
        )
    ).all()
    lines = [
        f"{'Inferred' if fact.is_inference else 'Observed'} {fact.fact_type} "
        f"at {path}:{fact.line_start}: {fact.description}"
        for fact, path in rows
    ]
    if not lines:
        raise HTTPException(422, detail="ai_no_review_context")
    content = ProjectInput(text="\n".join(lines)[:50000], question_count=6)
    source = analysis.id
    await session.rollback()
    return await saved(
        factory,
        settings,
        owner,
        provider,
        content,
        ProjectQuestions,
        lambda: provider.generate_project_questions(content),
        project_analysis_id=source,
    )
