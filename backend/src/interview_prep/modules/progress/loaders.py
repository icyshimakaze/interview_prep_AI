"""Bounded metadata reads. Every private relation is scoped to its resolved owner."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationStatus,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
)
from interview_prep.modules.progress.facts import ResultFact
from interview_prep.modules.progress.schemas import Activity
from interview_prep.modules.projects.defense_models import DefenseAnswer, DefenseRun
from interview_prep.modules.projects.models import (
    ProjectAnalysis,
    ProjectQuestion,
    ProjectRepository,
)
from interview_prep.modules.questions.models import (
    PublicationStatus,
    Question,
    QuestionType,
    QuestionVersion,
)
from interview_prep.modules.roadmaps.engine import DefenseSignal

WINDOW = 100


@dataclass
class History:
    results: list[ResultFact] = field(default_factory=list)
    recent: list[Activity] = field(default_factory=list)
    defense: list[DefenseSignal] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    interviews: int = 0


async def assessments(session: AsyncSession, owner: UUID, data: History) -> None:
    latest = (
        select(AssessmentAttempt.id)
        .where(
            AssessmentAttempt.owner_id == owner,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
        )
        .order_by(AssessmentAttempt.completed_at.desc(), AssessmentAttempt.id)
        .limit(WINDOW)
    )
    count = (
        await session.scalar(
            select(func.count())
            .select_from(AssessmentAttempt)
            .where(
                AssessmentAttempt.owner_id == owner,
                AssessmentAttempt.status == AttemptStatus.COMPLETED,
            )
        )
        or 0
    )
    if count > WINDOW:
        data.notices.append("Assessment analytics cover the latest 100 completed attempts.")
    rows = (
        await session.execute(
            select(QuestionAttempt, AssessmentAttempt, QuestionVersion, Question.canonical_concept)
            .join(AssessmentAttempt, AssessmentAttempt.id == QuestionAttempt.assessment_attempt_id)
            .join(
                AssessmentQuestion, AssessmentQuestion.id == QuestionAttempt.assessment_question_id
            )
            .join(QuestionVersion, QuestionVersion.id == AssessmentQuestion.question_version_id)
            .join(Question, Question.id == QuestionVersion.question_id)
            .where(
                QuestionAttempt.owner_id == owner,
                AssessmentAttempt.owner_id == owner,
                AssessmentQuestion.owner_id == owner,
                AssessmentAttempt.id.in_(latest),
                (Question.owner_id == owner) | Question.owner_id.is_(None),
            )
            .order_by(AssessmentAttempt.completed_at, QuestionAttempt.id)
            .limit(1201)
        )
    ).all()
    if len(rows) > 1200:
        data.notices.append("Assessment answer details were truncated at 1200 records.")
    for answer, attempt, version, concept in rows[:1200]:
        if attempt.completed_at is None:
            continue
        objective = (
            answer.status == AnswerStatus.SUBMITTED
            and answer.submitted_at is not None
            and answer.result_kind == "deterministic"
            and bool(answer.grading_version)
            and answer.max_score == 1
            and answer.is_correct is not None
            and answer.score == (1 if answer.is_correct else 0)
            and version.provenance_reviewed
            and version.status != PublicationStatus.DRAFT
            and version.question_type
            in {
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.MULTIPLE_SELECT,
                QuestionType.SHORT_ANSWER,
            }
        )
        metadata = answer.evaluation_metadata or {}
        payload = metadata.get("evaluation")
        configured_model = metadata.get("model")
        data.results.append(
            ResultFact(
                id=f"assessment:{answer.id}",
                session_id=str(attempt.id),
                at=attempt.completed_at,
                channel="assessment",
                category=version.category or "Uncategorized",
                concept=concept,
                objective_correct=answer.is_correct if objective else None,
                kind=answer.result_kind or "ungraded",
                payload=payload if isinstance(payload, dict) else None,
                provider=str(metadata.get("provider") or ""),
                model=configured_model if isinstance(configured_model, str) else None,
                provider_version=str(metadata.get("provider_version") or ""),
                rubric_version=str(metadata.get("rubric_version") or ""),
                grading_version=answer.grading_version or "",
                scale=answer.max_score,
                score=answer.score,
                completed=answer.status == AnswerStatus.SUBMITTED
                and answer.submitted_at is not None,
            )
        )
    recent = (
        await session.execute(
            select(AssessmentAttempt, Assessment.title)
            .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
            .where(AssessmentAttempt.owner_id == owner, Assessment.owner_id == owner)
            .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id)
            .limit(10)
        )
    ).all()
    data.recent.extend(
        Activity(
            id=str(a.id),
            channel="assessment",
            title=title,
            status=a.status.value,
            at=a.completed_at or a.started_at,
        )
        for a, title in recent
    )


async def interviews(session: AsyncSession, owner: UUID, data: History) -> None:
    latest = (
        select(InterviewSession.id)
        .where(
            InterviewSession.owner_id == owner,
            InterviewSession.status == SessionStatus.COMPLETED,
        )
        .order_by(InterviewSession.completed_at.desc(), InterviewSession.id)
        .limit(WINDOW)
    )
    data.interviews = (
        await session.scalar(
            select(func.count())
            .select_from(InterviewSession)
            .where(
                InterviewSession.owner_id == owner,
                InterviewSession.status == SessionStatus.COMPLETED,
            )
        )
        or 0
    )
    if data.interviews > WINDOW:
        data.notices.append("Interview analytics cover the latest 100 completed sessions.")
    # Rank first. Failed newest versions cannot expose an older successful rating.
    ranked = (
        select(
            AnswerEvaluation.id,
            func.row_number()
            .over(
                partition_by=AnswerEvaluation.interview_answer_id,
                order_by=(AnswerEvaluation.version.desc(), AnswerEvaluation.id),
            )
            .label("rank"),
        )
        .where(AnswerEvaluation.owner_id == owner)
        .subquery()
    )
    rows = (
        await session.execute(
            select(
                AnswerEvaluation,
                InterviewAnswer,
                InterviewQuestion,
                InterviewSession,
                QuestionVersion,
            )
            .join(InterviewAnswer, InterviewAnswer.id == AnswerEvaluation.interview_answer_id)
            .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.interview_question_id)
            .join(InterviewSession, InterviewSession.id == InterviewQuestion.session_id)
            .outerjoin(QuestionVersion, QuestionVersion.id == InterviewQuestion.question_version_id)
            .outerjoin(Question, Question.id == QuestionVersion.question_id)
            .where(
                AnswerEvaluation.owner_id == owner,
                InterviewAnswer.owner_id == owner,
                InterviewQuestion.owner_id == owner,
                InterviewSession.owner_id == owner,
                InterviewSession.id.in_(latest),
                (Question.owner_id == owner) | Question.owner_id.is_(None),
                AnswerEvaluation.id.in_(select(ranked.c.id).where(ranked.c.rank == 1)),
            )
            .order_by(InterviewSession.completed_at.desc(), InterviewQuestion.sequence)
            .limit(1301)
        )
    ).all()
    if len(rows) > 1300:
        data.notices.append("Interview evaluation details were truncated at 1300 records.")
    for evaluation, answer, question, interview, version in rows[:1300]:
        if interview.completed_at is None:
            continue
        data.results.append(
            ResultFact(
                id=f"interview:{evaluation.id}",
                session_id=str(interview.id),
                at=interview.completed_at,
                channel="interview",
                category=(version.category if version else None) or "Uncategorized",
                concept="",
                kind=evaluation.kind.value,
                provider=evaluation.provider or "",
                model=evaluation.model,
                provider_version=evaluation.evaluator_version,
                rubric_version=evaluation.rubric_version,
                scale=evaluation.score_scale_max,
                score=evaluation.score,
                payload=evaluation.result_payload,
                completed=evaluation.status == EvaluationStatus.COMPLETED
                and answer.status == AnswerStatus.SUBMITTED
                and answer.submitted_at is not None
                and question.parent_question_id is None,
            )
        )
    recent = (
        await session.scalars(
            select(InterviewSession)
            .where(
                InterviewSession.owner_id == owner,
            )
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id)
            .limit(10)
        )
    ).all()
    data.recent.extend(
        Activity(
            id=str(s.id),
            channel="interview",
            title="Interview practice",
            status=s.status.value,
            at=s.completed_at or s.created_at,
        )
        for s in recent
    )


async def defenses(session: AsyncSession, owner: UUID, data: History) -> None:
    ranked = (
        select(
            DefenseRun.id,
            func.row_number()
            .over(
                partition_by=DefenseRun.analysis_id,
                order_by=(DefenseRun.created_at.desc(), DefenseRun.id),
            )
            .label("rank"),
        )
        .where(DefenseRun.owner_id == owner)
        .subquery()
    )
    rows = (
        await session.execute(
            select(DefenseAnswer, ProjectRepository, QuestionVersion.title)
            .join(DefenseRun, DefenseRun.id == DefenseAnswer.run_id)
            .join(ProjectAnalysis, ProjectAnalysis.id == DefenseRun.analysis_id)
            .join(ProjectRepository, ProjectRepository.id == ProjectAnalysis.repository_id)
            .join(ProjectQuestion, ProjectQuestion.id == DefenseAnswer.question_id)
            .join(QuestionVersion, QuestionVersion.id == ProjectQuestion.question_version_id)
            .where(
                DefenseAnswer.owner_id == owner,
                DefenseRun.owner_id == owner,
                ProjectAnalysis.owner_id == owner,
                ProjectRepository.owner_id == owner,
                ProjectQuestion.owner_id == owner,
                DefenseRun.id.in_(select(ranked.c.id).where(ranked.c.rank == 1)),
            )
            .order_by(ProjectRepository.id, DefenseAnswer.position)
            .limit(51)
        )
    ).all()
    if len(rows) > 50:
        data.notices.append("Defense context was truncated at 50 answers.")
    for answer, project, title in rows[:50]:
        data.defense.append(
            DefenseSignal(
                str(project.id),
                project.name,
                str(answer.question_id),
                title[4:],
                answer.status,
                str(answer.id),
            )
        )
    recent = (
        await session.execute(
            select(DefenseRun, ProjectRepository.name)
            .join(ProjectAnalysis, ProjectAnalysis.id == DefenseRun.analysis_id)
            .join(ProjectRepository, ProjectRepository.id == ProjectAnalysis.repository_id)
            .where(
                DefenseRun.owner_id == owner,
                ProjectAnalysis.owner_id == owner,
                ProjectRepository.owner_id == owner,
            )
            .order_by(DefenseRun.created_at.desc(), DefenseRun.id)
            .limit(10)
        )
    ).all()
    data.recent.extend(
        Activity(
            id=str(s.id),
            channel="project_defense",
            title=name,
            status=s.status,
            at=s.completed_at or s.created_at,
        )
        for s, name in recent
    )


async def history(session: AsyncSession, owner: UUID) -> History:
    data = History()
    # AsyncSession is deliberately sequential: it cannot serve concurrent queries.
    await assessments(session, owner, data)
    await interviews(session, owner, data)
    await defenses(session, owner, data)
    return data
