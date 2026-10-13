"Bounded explicit reads; every private query includes the resolved owner."

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.assessments.models import Assessment, AssessmentAttempt, QuestionAttempt
from interview_prep.modules.context.models import (
    Resume,
    ResumeSkillEvidence,
    ResumeVersion,
    ReviewStatus,
    TargetJob,
    TargetJobVersion,
)
from interview_prep.modules.identity.models import PrincipalKind, Profile, User
from interview_prep.modules.identity.profiles import profile_view
from interview_prep.modules.identity.schemas import (
    AssessmentView,
    DashboardView,
    InterviewView,
    ProgressView,
    ResumeView,
    RoadmapItemView,
    TargetView,
)
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from interview_prep.modules.roadmaps.models import ProgressEvent, RoadmapItem


async def owned_resume(session: AsyncSession, owner: UUID, resource_id: UUID) -> ResumeView:
    resume = await session.scalar(
        select(Resume).where(Resume.id == resource_id, Resume.owner_id == owner)
    )
    if resume is None:
        raise HTTPException(status_code=404)
    evidence = (
        await session.scalars(
            select(ResumeSkillEvidence)
            .join(ResumeVersion, ResumeVersion.id == ResumeSkillEvidence.resume_version_id)
            .where(
                ResumeVersion.resume_id == resource_id,
                ResumeVersion.owner_id == owner,
                ResumeSkillEvidence.owner_id == owner,
                ResumeSkillEvidence.review_status != ReviewStatus.REJECTED,
            )
            .limit(20)
        )
    ).all()
    return ResumeView(
        id=resume.id,
        label=resume.label,
        evidence=[item.user_correction or item.source_excerpt or item.claim for item in evidence],
    )


async def owned_target(session: AsyncSession, owner: UUID, resource_id: UUID) -> TargetView:
    latest_version = (
        select(func.max(TargetJobVersion.version))
        .where(TargetJobVersion.target_job_id == resource_id, TargetJobVersion.owner_id == owner)
        .scalar_subquery()
        .correlate(None)
    )
    row = (
        await session.execute(
            select(TargetJob, TargetJobVersion.description)
            .outerjoin(
                TargetJobVersion,
                (TargetJobVersion.target_job_id == TargetJob.id)
                & (TargetJobVersion.owner_id == owner)
                & (TargetJobVersion.version == latest_version),
            )
            .where(TargetJob.id == resource_id, TargetJob.owner_id == owner)
            .execution_options(populate_existing=True)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404)
    target, description = row
    return TargetView(
        id=target.id,
        title=target.title,
        organization=target.organization,
        description=description,
        source_url=target.source_url,
        notes=target.notes,
        priority=target.priority,
        status=target.status,
        revision=target.revision,
    )


async def dashboard(session: AsyncSession, user: User) -> DashboardView:
    owner = user.id
    profile = await session.scalar(select(Profile).where(Profile.owner_id == owner))
    target_ids = (
        await session.scalars(
            select(TargetJob.id)
            .where(TargetJob.owner_id == owner)
            .order_by(TargetJob.created_at.desc())
            .limit(10)
        )
    ).all()
    resume_ids = (
        await session.scalars(
            select(Resume.id)
            .where(Resume.owner_id == owner)
            .order_by(Resume.created_at.desc())
            .limit(10)
        )
    ).all()
    assessments: list[AssessmentView] = []
    rows = (
        await session.execute(
            select(AssessmentAttempt, Assessment.title)
            .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
            .where(AssessmentAttempt.owner_id == owner, Assessment.owner_id == owner)
            .order_by(AssessmentAttempt.started_at.desc())
            .limit(20)
        )
    ).all()
    for attempt, title in rows:
        answers = (
            await session.scalars(
                select(QuestionAttempt).where(
                    QuestionAttempt.owner_id == owner,
                    QuestionAttempt.assessment_attempt_id == attempt.id,
                )
            )
        ).all()
        kinds = {answer.result_kind for answer in answers if answer.result_kind}
        assessments.append(
            AssessmentView(
                id=attempt.id,
                title=title,
                completed_at=attempt.completed_at,
                answered=sum(a.submitted_at is not None for a in answers),
                correct=sum(a.is_correct is True for a in answers),
                result_kind=next(iter(kinds)) if len(kinds) == 1 else "ungraded",
            )
        )
    interviews: list[InterviewView] = []
    sessions = (
        await session.scalars(
            select(InterviewSession)
            .where(InterviewSession.owner_id == owner)
            .order_by(InterviewSession.created_at.desc())
            .limit(20)
        )
    ).all()
    for interview in sessions:
        evaluations = (
            await session.scalars(
                select(AnswerEvaluation)
                .join(InterviewAnswer, InterviewAnswer.id == AnswerEvaluation.interview_answer_id)
                .join(
                    InterviewQuestion, InterviewQuestion.id == InterviewAnswer.interview_question_id
                )
                .where(
                    AnswerEvaluation.owner_id == owner,
                    InterviewAnswer.owner_id == owner,
                    InterviewQuestion.owner_id == owner,
                    InterviewQuestion.session_id == interview.id,
                )
                .order_by(AnswerEvaluation.version.desc())
                .limit(20)
            )
        ).all()
        kinds = {str(e.kind) for e in evaluations}
        interviews.append(
            InterviewView(
                id=interview.id,
                completed_at=interview.completed_at,
                status=interview.status,
                feedback=[e.feedback for e in evaluations if e.feedback],
                result_kind=next(iter(kinds)) if len(kinds) == 1 else "ungraded",
            )
        )
    items = (
        await session.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.owner_id == owner)
            .order_by(RoadmapItem.position)
            .limit(50)
        )
    ).all()
    events = (
        await session.scalars(
            select(ProgressEvent)
            .where(ProgressEvent.owner_id == owner)
            .order_by(ProgressEvent.occurred_at.desc())
            .limit(30)
        )
    ).all()
    is_demo = user.kind == PrincipalKind.DEMO
    return DashboardView(
        mode="demo" if is_demo else "account",
        data_label="Fictional demo candidate · simulated history"
        if is_demo
        else "Your preparation workspace",
        expires_at=user.expires_at,
        profile=await profile_view(session, profile) if profile else None,
        targets=[await owned_target(session, owner, resource_id) for resource_id in target_ids],
        resumes=[await owned_resume(session, owner, resource_id) for resource_id in resume_ids],
        assessments=assessments,
        interviews=interviews,
        roadmap_items=[RoadmapItemView.model_validate(item) for item in items],
        progress=[ProgressView.model_validate(event) for event in events],
    )
