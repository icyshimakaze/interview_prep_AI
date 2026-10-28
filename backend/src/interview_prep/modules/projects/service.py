import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.context.models import ProcessingStatus
from interview_prep.modules.identity.models import PrincipalStatus, User
from interview_prep.modules.projects.models import (
    ProjectAnalysis,
    ProjectFact,
    ProjectOrigin,
    ProjectQuestion,
    ProjectQuestionCitation,
    ProjectRepository,
    SourceFile,
)
from interview_prep.modules.projects.questions import questions
from interview_prep.modules.projects.schemas import (
    VERSION,
    AnalysisSummary,
    DefensePrompt,
    FileFact,
    ProjectDetail,
    ProjectList,
    ProjectSummary,
    StaticAnalysis,
    StaticFact,
)
from interview_prep.modules.questions.models import (
    PublicationStatus,
    Question,
    QuestionType,
    QuestionVersion,
    QuestionVisibility,
)


async def lock_owner(session: AsyncSession, owner: UUID) -> None:
    user = await session.scalar(
        select(User)
        .where(User.id == owner)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        not user
        or user.status != PrincipalStatus.ACTIVE
        or user.expires_at
        and user.expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(401)


async def owned(
    session: AsyncSession, owner: UUID, identifier: UUID
) -> tuple[ProjectRepository, ProjectAnalysis]:
    row = (
        await session.execute(
            select(ProjectRepository, ProjectAnalysis)
            .join(ProjectAnalysis, ProjectAnalysis.repository_id == ProjectRepository.id)
            .where(
                ProjectRepository.owner_id == owner,
                ProjectRepository.id == identifier,
                ProjectAnalysis.owner_id == owner,
                ProjectAnalysis.analysis_version == VERSION,
                ProjectAnalysis.status == ProcessingStatus.READY,
            )
        )
    ).first()
    if row is None:
        raise HTTPException(404)
    return row[0], row[1]


def summary(repository: ProjectRepository, analysis: ProjectAnalysis) -> ProjectSummary:
    return ProjectSummary(
        id=repository.id,
        analysis_id=analysis.id,
        name=repository.name,
        origin=repository.origin.value,
        github_url=f"https://github.com/{repository.github_owner}/{repository.github_repository}"
        if repository.origin == ProjectOrigin.GITHUB
        else None,
        commit_sha=analysis.commit_sha,
        created_at=analysis.created_at,
        analysis_version=analysis.analysis_version,
        example=(analysis.summary or {}).get("example") is True,
    )


async def list_projects(session: AsyncSession, owner: UUID) -> ProjectList:
    rows = (
        await session.execute(
            select(ProjectRepository, ProjectAnalysis)
            .join(ProjectAnalysis, ProjectAnalysis.repository_id == ProjectRepository.id)
            .where(
                ProjectRepository.owner_id == owner,
                ProjectAnalysis.owner_id == owner,
                ProjectAnalysis.analysis_version == VERSION,
            )
            .order_by(ProjectAnalysis.created_at.desc(), ProjectAnalysis.id)
            .limit(5)
        )
    ).all()
    return ProjectList(items=[summary(r, a) for r, a in rows])


async def prompts(session: AsyncSession, owner: UUID, analysis: UUID) -> list[DefensePrompt]:
    rows = (
        await session.execute(
            select(ProjectQuestion, QuestionVersion, SourceFile, ProjectQuestionCitation)
            .join(QuestionVersion, QuestionVersion.id == ProjectQuestion.question_version_id)
            .join(
                ProjectQuestionCitation,
                ProjectQuestionCitation.project_question_id == ProjectQuestion.id,
            )
            .join(SourceFile, SourceFile.id == ProjectQuestionCitation.source_file_id)
            .where(
                ProjectQuestion.owner_id == owner,
                ProjectQuestion.analysis_id == analysis,
                ProjectQuestionCitation.owner_id == owner,
                SourceFile.owner_id == owner,
            )
            .order_by(QuestionVersion.title)
        )
    ).all()
    results = []
    for question, version, source, citation in rows:
        # The exact static clue used by the template is frozen in private source metadata.
        evidence = question.context or {}
        results.append(
            DefensePrompt(
                id=question.id,
                focus=version.title[4:],
                prompt=version.prompt or "",
                path=source.path,
                line=citation.line_start,
                evidence=str(evidence.get("description", "Static source clue")),
                inferred=evidence.get("inferred") is True,
            )
        )
    return results


async def detail(session: AsyncSession, owner: UUID, identifier: UUID) -> ProjectDetail:
    repository, analysis = await owned(session, owner, identifier)
    files = list(
        (
            await session.scalars(
                select(SourceFile)
                .where(SourceFile.owner_id == owner, SourceFile.analysis_id == analysis.id)
                .order_by(SourceFile.path)
            )
        ).all()
    )
    paths = {f.id: f.path for f in files}
    facts = (
        await session.scalars(
            select(ProjectFact)
            .join(SourceFile, SourceFile.id == ProjectFact.source_file_id)
            .where(ProjectFact.owner_id == owner, ProjectFact.analysis_id == analysis.id)
            .order_by(
                SourceFile.path,
                ProjectFact.line_start,
                ProjectFact.fact_type,
                ProjectFact.description,
            )
        )
    ).all()
    return ProjectDetail(
        **summary(repository, analysis).model_dump(),
        summary=AnalysisSummary.model_validate((analysis.summary or {}).get("report")),
        files=[
            FileFact(
                path=f.path,
                sha256=f.content_sha256,
                byte_count=f.byte_count,
                line_count=f.line_count,
                language=f.language,
            )
            for f in files
        ],
        facts=[
            StaticFact.model_validate(
                dict(
                    path=paths[f.source_file_id],
                    kind=f.fact_type,
                    description=f.description,
                    line=f.line_start,
                    inferred=f.is_inference,
                )
            )
            for f in facts
        ],
        questions=await prompts(session, owner, analysis.id),
    )


async def save_snapshot(
    session: AsyncSession,
    owner: UUID,
    data: bytes,
    parsed: StaticAnalysis,
    github_owner: str | None = None,
    repository_name: str | None = None,
    commit: str | None = None,
    example: bool = False,
) -> ProjectDetail:
    await lock_owner(session, owner)
    digest = hashlib.sha256(data).hexdigest()
    existing = await session.scalar(
        select(ProjectAnalysis)
        .join(ProjectRepository, ProjectRepository.id == ProjectAnalysis.repository_id)
        .where(
            ProjectRepository.github_owner == github_owner,
            ProjectRepository.github_repository == (repository_name if github_owner else None),
            ProjectAnalysis.commit_sha == commit,
            ProjectAnalysis.summary["example"].as_boolean() == example,
            ProjectAnalysis.owner_id == owner,
            ProjectAnalysis.archive_sha256 == digest,
            ProjectAnalysis.analysis_version == VERSION,
        )
    )
    if existing:
        return await detail(session, owner, existing.repository_id)
    count = await session.scalar(
        select(func.count())
        .select_from(ProjectRepository)
        .where(ProjectRepository.owner_id == owner)
    )
    if count and count >= 5:
        raise HTTPException(409, detail="project_limit")
    repo = ProjectRepository(
        owner_id=owner,
        name=repository_name
        or ("Illustrative task tracker" if example else "Uploaded source project"),
        origin=ProjectOrigin.GITHUB if github_owner else ProjectOrigin.ZIP,
        github_owner=github_owner,
        github_repository=repository_name if github_owner else None,
    )
    session.add(repo)
    await session.flush()
    now = datetime.now(UTC)
    analysis = ProjectAnalysis(
        owner_id=owner,
        repository_id=repo.id,
        archive_sha256=digest,
        archive_bytes=len(data),
        commit_sha=commit,
        archive_storage_key=None,
        upload_expires_at=now + timedelta(hours=1),
        upload_deleted_at=now,
        analysis_version=VERSION,
        status=ProcessingStatus.READY,
        summary={"report": parsed.summary.model_dump(mode="json"), "example": example},
    )
    session.add(analysis)
    await session.flush()
    files: dict[str, SourceFile] = {}
    for source in parsed.files:
        row = SourceFile(
            owner_id=owner,
            analysis_id=analysis.id,
            path=source.path,
            content_sha256=source.sha256,
            byte_count=source.byte_count,
            line_count=source.line_count,
            language=source.language,
            retained_text=None,
        )
        session.add(row)
        files[source.path] = row
    await session.flush()
    session.add_all(
        [
            ProjectFact(
                owner_id=owner,
                analysis_id=analysis.id,
                source_file_id=files[f.path].id,
                fact_type=f.kind,
                description=f.description,
                line_start=f.line,
                line_end=f.line,
                is_inference=f.inferred,
            )
            for f in parsed.facts
        ]
    )
    for position, prompt in enumerate(questions(parsed), 1):
        question = Question(
            owner_id=owner,
            visibility=QuestionVisibility.PRIVATE,
            canonical_concept=f"project-defense:{analysis.id}:{position}",
        )
        session.add(question)
        await session.flush()
        version = QuestionVersion(
            question_id=question.id,
            version=1,
            title=f"{position:02}. {prompt.focus}",
            prompt=prompt.text,
            question_type=QuestionType.WRITTEN,
            status=PublicationStatus.DRAFT,
            provenance_reviewed=False,
            source_file=prompt.fact.path,
        )
        session.add(version)
        await session.flush()
        generated = ProjectQuestion(
            owner_id=owner,
            analysis_id=analysis.id,
            question_version_id=version.id,
            generation_method="deterministic",
            generator_version="project-prompts-v1",
            context={"description": prompt.fact.description, "inferred": prompt.fact.inferred},
        )
        session.add(generated)
        await session.flush()
        session.add(
            ProjectQuestionCitation(
                owner_id=owner,
                project_question_id=generated.id,
                analysis_id=analysis.id,
                source_file_id=files[prompt.fact.path].id,
                line_start=prompt.fact.line,
                line_end=prompt.fact.line,
            )
        )
    await session.commit()
    return await detail(session, owner, repo.id)


async def remove(session: AsyncSession, owner: UUID, identifier: UUID) -> None:
    await lock_owner(session, owner)
    repository, analysis = await owned(session, owner, identifier)
    question_ids = (
        await session.scalars(
            select(QuestionVersion.question_id)
            .join(ProjectQuestion, ProjectQuestion.question_version_id == QuestionVersion.id)
            .where(ProjectQuestion.owner_id == owner, ProjectQuestion.analysis_id == analysis.id)
        )
    ).all()
    await session.delete(repository)
    await session.flush()
    await session.execute(
        delete(Question).where(Question.owner_id == owner, Question.id.in_(question_ids))
    )
    await session.commit()
