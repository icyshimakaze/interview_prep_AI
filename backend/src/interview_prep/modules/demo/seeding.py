"""Small fictional candidate, isolated per expiring visitor; no inference calls."""

import hashlib
from datetime import datetime, timedelta
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentStatus,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.context.models import (
    JobSkillRequirement,
    ProcessingStatus,
    RequirementPriority,
    Resume,
    ResumeSkillEvidence,
    ResumeVersion,
    ReviewStatus,
    TargetJob,
    TargetJobVersion,
)
from interview_prep.modules.identity.models import ExperienceBand, Profile, User
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationDimension,
    EvaluationKind,
    EvaluationStatus,
    InterviewAnswer,
    InterviewMode,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.questions.models import (
    Difficulty,
    PublicationStatus,
    Question,
    QuestionRubricCriterion,
    QuestionType,
    QuestionVersion,
    QuestionVisibility,
    ShortAnswerKey,
)
from interview_prep.modules.roadmaps.models import (
    ProgressEvent,
    ProgressEventType,
    Roadmap,
    RoadmapItem,
    RoadmapStatus,
    TaskStatus,
)

DEMO_VERSION = "fictional-candidate-v1"


async def initialize_demo(session: AsyncSession, owner: UUID, now: datetime) -> None:
    # The principal lock serializes first initialization and retries. No global
    # shared candidate is used, and account principals are never seeded.
    user = await session.scalar(select(User).where(User.id == owner).with_for_update())
    if user is None or user.kind != "demo":
        raise ValueError("Fictional seed requires a demo principal")
    if await session.scalar(select(Profile.id).where(Profile.owner_id == owner)) is not None:
        return

    def identifier(name: str) -> UUID:
        return uuid5(owner, DEMO_VERSION + "/" + name)

    session.add(
        Profile(
            id=identifier("profile"),
            owner_id=owner,
            display_name="Aarav Rao (fictional)",
            target_role="Junior Backend Engineer",
            experience_band=ExperienceBand.ENTRY,
            timezone="Asia/Kolkata",
            weekly_minutes=240,
        )
    )
    target = TargetJob(
        id=identifier("target"),
        owner_id=owner,
        title="Junior Backend Engineer",
        organization="Example Harbour Labs (fictional)",
    )
    resume = Resume(
        id=identifier("resume"), owner_id=owner, label="Aarav's sample resume · fictional"
    )
    session.add_all([target, resume])
    await session.flush()
    job_text = (
        "Fictional role: build Python APIs, use PostgreSQL, explain data structures, "
        "and write tests. No actual employer or vacancy."
    )
    resume_text = "Fictional project: built a small library catalogue API with Python and SQL."
    target_version = TargetJobVersion(
        id=identifier("target/1"),
        owner_id=owner,
        target_job_id=target.id,
        version=1,
        description=job_text,
    )
    resume_version = ResumeVersion(
        id=identifier("resume/1"),
        owner_id=owner,
        resume_id=resume.id,
        version=1,
        content_sha256=hashlib.sha256(resume_text.encode()).hexdigest(),
        media_type="text/plain",
        byte_count=len(resume_text),
        upload_expires_at=now + timedelta(hours=24),
        upload_deleted_at=now,
        extraction_version="fictional-text-v1",
        status=ProcessingStatus.READY,
    )
    session.add_all([target_version, resume_version])
    await session.flush()
    session.add(
        ResumeSkillEvidence(
            owner_id=owner,
            resume_version_id=resume_version.id,
            claim="Built a sample API (fictional claim, not verified competence)",
            source_excerpt=resume_text,
            source_start=0,
            source_end=len(resume_text),
            review_status=ReviewStatus.CONFIRMED,
        )
    )
    session.add(
        JobSkillRequirement(
            owner_id=owner,
            target_job_version_id=target_version.id,
            source_excerpt=job_text,
            source_start=0,
            source_end=len(job_text),
            priority=RequirementPriority.ESSENTIAL,
            review_status=ReviewStatus.CONFIRMED,
        )
    )

    prompts = [
        (
            "Hash lookup",
            "What is the average time complexity of a hash-table lookup "
            "with well-distributed keys?",
            "O(1)",
        ),
        (
            "Array scan",
            "What is the time complexity of scanning every element once in an array of n elements?",
            "O(n)",
        ),
        (
            "API ownership",
            "Explain how a server should prevent a user from reading "
            "another user's private resume.",
            None,
        ),
    ]
    versions: list[QuestionVersion] = []
    criterion: QuestionRubricCriterion | None = None
    for index, (title, prompt, answer) in enumerate(prompts):
        question = Question(
            id=identifier(f"question/{index}"),
            owner_id=owner,
            visibility=QuestionVisibility.PRIVATE,
            canonical_concept=f"demo/{owner}/{index}",
        )
        session.add(question)
        await session.flush()
        version = QuestionVersion(
            id=identifier(f"question/{index}/1"),
            question_id=question.id,
            version=1,
            title=title,
            prompt=prompt,
            question_type=QuestionType.SHORT_ANSWER if answer else QuestionType.WRITTEN,
            difficulty=Difficulty.EASY,
            status=PublicationStatus.DRAFT,
            source_file="fictional-candidate-v1",
            source_license="CC0-1.0",
            provenance_reviewed=True,
            rubric_version="demo-rubric-v1",
        )
        session.add(version)
        await session.flush()
        if answer:
            session.add(
                ShortAnswerKey(
                    question_version_id=version.id,
                    normalized_answer=answer,
                    normalization_version="literal-v1",
                )
            )
        else:
            criterion = QuestionRubricCriterion(
                question_version_id=version.id,
                code="ownership",
                description="Explain server-resolved owner scoping",
                weight=1,
                anchor_0="No ownership check",
                anchor_1="Mentions login only",
                anchor_2="Mentions checking owner",
                anchor_3="Scopes every query on server",
                anchor_4="Scopes queries and tests foreign IDs",
            )
            session.add(criterion)
        await session.flush()
        version.status = PublicationStatus.PUBLISHED
        versions.append(version)
    await session.flush()

    assessment = Assessment(
        id=identifier("assessment"),
        owner_id=owner,
        title="Foundations diagnostic · simulated example",
        target_job_version_id=target_version.id,
        resume_version_id=resume_version.id,
        status=AssessmentStatus.READY,
        context_version=DEMO_VERSION,
        policy_version="demo-blueprint-v1",
    )
    session.add(assessment)
    await session.flush()
    allocations: list[AssessmentQuestion] = []
    for index, version in enumerate(versions[:2]):
        allocation = AssessmentQuestion(
            id=identifier(f"allocation/{index}"),
            owner_id=owner,
            assessment_id=assessment.id,
            question_version_id=version.id,
            position=index + 1,
        )
        session.add(allocation)
        allocations.append(allocation)
    await session.flush()
    for index in range(2):
        completed = now - timedelta(days=6 - index * 3)
        attempt = AssessmentAttempt(
            id=identifier(f"attempt/{index}"),
            owner_id=owner,
            assessment_id=assessment.id,
            attempt_number=index + 1,
            submission_key=identifier(f"attempt-key/{index}"),
            status=AttemptStatus.COMPLETED,
            started_at=completed - timedelta(minutes=10),
            completed_at=completed,
        )
        session.add(attempt)
        await session.flush()
        for position, allocation in enumerate(allocations):
            correct = index == 1 or position == 0
            session.add(
                QuestionAttempt(
                    owner_id=owner,
                    assessment_id=assessment.id,
                    assessment_attempt_id=attempt.id,
                    assessment_question_id=allocation.id,
                    status=AnswerStatus.SUBMITTED,
                    answer_text="O(1)" if position == 0 else "O(n)" if correct else "O(n^2)",
                    submitted_at=completed,
                    submission_key=identifier(f"answer-key/{index}/{position}"),
                    is_correct=correct,
                    result_kind="simulation",
                    grading_version="fictional-result-v1",
                )
            )
        session.add(
            ProgressEvent(
                owner_id=owner,
                event_type=ProgressEventType.ASSESSMENT_COMPLETED,
                result_kind=EvaluationKind.SIMULATION,
                assessment_attempt_id=attempt.id,
                deduplication_key=identifier(f"progress/assessment/{index}"),
                occurred_at=completed,
            )
        )

    completed = now - timedelta(days=2)
    interview = InterviewSession(
        id=identifier("interview"),
        owner_id=owner,
        mode=InterviewMode.MOCK_INTERVIEW,
        status=SessionStatus.COMPLETED,
        context_version=DEMO_VERSION,
        policy_version="demo-interview-v1",
        provider="fictional_fixture",
        main_question_limit=1,
        started_at=completed - timedelta(minutes=15),
        completed_at=completed,
    )
    session.add(interview)
    await session.flush()
    turn = InterviewQuestion(
        id=identifier("turn"),
        owner_id=owner,
        session_id=interview.id,
        question_version_id=versions[2].id,
        sequence=1,
        status=TurnStatus.EVALUATED,
    )
    session.add(turn)
    await session.flush()
    interview_answer = InterviewAnswer(
        id=identifier("interview-answer"),
        owner_id=owner,
        interview_question_id=turn.id,
        answer_text=(
            "Resolve the signed-in user on the server, then filter every resume query "
            "by that owner. Test foreign resume IDs too."
        ),
        status=AnswerStatus.SUBMITTED,
        submission_key=identifier("interview-key"),
        submitted_at=completed,
    )
    session.add(interview_answer)
    await session.flush()
    evaluation = AnswerEvaluation(
        owner_id=owner,
        interview_answer_id=interview_answer.id,
        version=1,
        kind=EvaluationKind.SIMULATION,
        status=EvaluationStatus.PENDING,
        evaluator_version="fictional-feedback-v1",
        rubric_version="demo-rubric-v1",
        feedback=(
            "Simulated feedback: a clear explanation of server-side ownership. "
            "In a real interview, discuss missing credentials and revocation too."
        ),
    )
    session.add(evaluation)
    await session.flush()
    if criterion is None:
        raise ValueError("Missing fictional rubric")
    session.add(
        EvaluationDimension(
            owner_id=owner,
            evaluation_id=evaluation.id,
            criterion_id=criterion.id,
            score=4,
            not_evaluable=False,
            feedback="Fictional rubric example; no AI evaluation occurred.",
        )
    )
    await session.flush()
    evaluation.status = EvaluationStatus.COMPLETED
    session.add(
        ProgressEvent(
            owner_id=owner,
            event_type=ProgressEventType.INTERVIEW_COMPLETED,
            result_kind=EvaluationKind.SIMULATION,
            interview_session_id=interview.id,
            deduplication_key=identifier("progress/interview"),
            occurred_at=completed,
        )
    )

    roadmap = Roadmap(
        id=identifier("roadmap"),
        owner_id=owner,
        target_job_version_id=target_version.id,
        title="Backend foundations · fictional plan",
        status=RoadmapStatus.ACTIVE,
        policy_version="demo-roadmap-v1",
        context_version=DEMO_VERSION,
        weekly_minutes=240,
        timezone="Asia/Kolkata",
        starts_on=(now - timedelta(days=7)).date(),
    )
    session.add(roadmap)
    await session.flush()
    for index, title in enumerate(
        [
            "Review hash tables and array complexity",
            "Practice SQL joins with a small sample dataset",
            "Explain API authorization and write isolation tests",
        ]
    ):
        item = RoadmapItem(
            id=identifier(f"task/{index}"),
            owner_id=owner,
            roadmap_id=roadmap.id,
            title=title,
            position=index + 1,
            estimated_minutes=45,
            scheduled_on=(now + timedelta(days=index)).date(),
            status=TaskStatus.COMPLETED if index == 0 else TaskStatus.PLANNED,
            completed_at=now - timedelta(days=1) if index == 0 else None,
        )
        session.add(item)
        await session.flush()
        if item.completed_at:
            session.add(
                ProgressEvent(
                    owner_id=owner,
                    event_type=ProgressEventType.ROADMAP_ITEM_COMPLETED,
                    result_kind=EvaluationKind.SIMULATION,
                    roadmap_item_id=item.id,
                    deduplication_key=identifier("progress/task/0"),
                    occurred_at=item.completed_at,
                )
            )
    await session.flush()
