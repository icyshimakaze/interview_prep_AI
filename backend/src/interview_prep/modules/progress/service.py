from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.identity.models import PrincipalKind, User
from interview_prep.modules.progress.engine import (
    assessment_chart_available,
    assessment_summary,
    evidence_summaries,
    interview_summary,
    missed_concepts,
)
from interview_prep.modules.progress.loaders import history
from interview_prep.modules.progress.schemas import Completion, EvidenceSummary, ProgressAnalytics
from interview_prep.modules.roadmaps.models import (
    ProgressEvent,
    ProgressEventType,
    Roadmap,
    RoadmapItem,
    RoadmapStatus,
    TaskStatus,
)
from interview_prep.modules.skills.service import skill_matrix


async def analytics(session: AsyncSession, user: User) -> ProgressAnalytics:
    data = await history(session, user.id)
    matrix = await skill_matrix(session, user, None)
    assessments, categories = assessment_summary(data.results)
    series, excluded = interview_summary(data.results)
    strengths, validation = evidence_summaries(matrix.rows)
    if data.defense:
        submitted = sum(s.status == "submitted" for s in data.defense)
        skipped = sum(s.status == "skipped" for s in data.defense)
        validation.append(
            EvidenceSummary(
                topic="Project Defense explanations",
                description=f"{submitted} submitted answers "
                "in the latest session per project; "
                f"{skipped} "
                "skipped. These are unscored practice and require independent review.",
                source_count=0,
            )
        )
    current = await session.scalar(
        select(Roadmap.id)
        .where(
            Roadmap.owner_id == user.id,
            Roadmap.status == RoadmapStatus.ACTIVE,
        )
        .order_by(Roadmap.created_at.desc(), Roadmap.id)
        .limit(1)
    )
    rows = (
        await session.execute(
            select(
                RoadmapItem.roadmap_id,
                RoadmapItem.status,
                func.count(),
            )
            .where(RoadmapItem.owner_id == user.id)
            .group_by(RoadmapItem.roadmap_id, RoadmapItem.status)
        )
    ).all()
    completion = Completion()
    for plan_id, status, count in rows:
        if plan_id == current:
            completion.current_total += count
            completion.current_completed += count if status == TaskStatus.COMPLETED else 0
        else:
            completion.historical_items += count
            completion.historical_completed += count if status == TaskStatus.COMPLETED else 0
    completion.completion_events = (
        await session.scalar(
            select(func.count())
            .select_from(
                ProgressEvent,
            )
            .where(
                ProgressEvent.owner_id == user.id,
                ProgressEvent.event_type == ProgressEventType.ROADMAP_ITEM_COMPLETED,
            )
        )
        or 0
    )
    notes = [
        "Accuracy counts submitted deterministic grades on reviewed objective questions in "
        "completed "
        "assessments. Written, skipped, ungraded and simulated answers are excluded from "
        "its denominator.",
        "Category percentages describe recorded question responses, not category mastery. "
        "Question mix and difficulty may differ between sessions.",
        "Interview means use only the newest evaluation per answer, a known 0–4 structured rubric, "
        "and identical provider/model/version/profile/assessed dimensions. Model ratings "
        "are not validation.",
        "Simulated, failed, pending, legacy-unscaled and unscored follow-up evaluations "
        "are excluded "
        "from interview numeric trends and model-suggested gaps.",
        "Charts require at least three comparable sessions on three distinct UTC dates. "
        "Smaller histories use tables without implying a trend.",
        "Repeated gaps require observations in at least two distinct sessions. Objective concepts "
        "and model-suggested missing concepts are labelled separately; simulations never "
        "create gaps.",
        "Strengths reuse the skill-evidence policy: eligible reviewed objective results in "
        "their tested "
        "scope. Resume claims, model feedback, task completion and defense practice never "
        "validate skills.",
        "Historical task rows are retained across generations. Reopening changes current "
        "task status "
        "but preserves completion events; recompletion adds another event.",
    ]
    notes.extend(data.notices)
    notes.extend(matrix.notices)
    return ProgressAnalytics(
        mode="demo" if user.kind == PrincipalKind.DEMO else "account",
        generated_at=datetime.now(UTC),
        assessments=assessments,
        categories=categories,
        assessment_chart_available=assessment_chart_available(assessments),
        interview_series=series,
        excluded_interview_evaluations=excluded,
        frequently_missed=missed_concepts(data.results),
        roadmap=completion,
        recent_sessions=sorted(data.recent, key=lambda r: (r.at, r.channel, r.id), reverse=True)[
            :15
        ],
        validated_strengths=strengths,
        requires_validation=validation,
        notices=notes,
    )
