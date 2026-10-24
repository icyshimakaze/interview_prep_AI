import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai.analysis_models import AIAnalysis
from interview_prep.modules.context.models import (
    EvidenceCategory,
    EvidenceOrigin,
    ProcessingStatus,
    Resume,
    ResumeSkillEvidence,
    ResumeVersion,
    ReviewStatus,
)
from interview_prep.modules.identity.models import PrincipalStatus, User
from interview_prep.modules.resumes.extraction import EXTRACTION_VERSION, MAX_EVIDENCE
from interview_prep.modules.resumes.schemas import (
    EvidenceInput,
    EvidenceView,
    ResumeDetail,
    ResumeList,
)
from interview_prep.modules.resumes.upload import ParsedPdf

MAX_RESUMES = 5


async def get_resume(session: AsyncSession, owner: UUID, id: UUID) -> ResumeDetail:
    resume = await session.scalar(select(Resume).where(Resume.owner_id == owner, Resume.id == id))
    if resume is None:
        raise HTTPException(404)
    version = await session.scalar(
        select(ResumeVersion)
        .where(
            ResumeVersion.owner_id == owner,
            ResumeVersion.resume_id == id,
        )
        .order_by(ResumeVersion.version.desc())
        .limit(1)
    )
    evidence = (
        (
            await session.scalars(
                select(ResumeSkillEvidence)
                .where(
                    ResumeSkillEvidence.owner_id == owner,
                    ResumeSkillEvidence.resume_version_id == version.id,
                )
                .order_by(ResumeSkillEvidence.created_at, ResumeSkillEvidence.id)
                .limit(MAX_EVIDENCE)
            )
        ).all()
        if version
        else []
    )
    return ResumeDetail(
        id=resume.id,
        label=resume.label,
        revision=resume.revision,
        page_count=version.page_count if version else None,
        extraction_note=version.extraction_note if version else None,
        evidence=[EvidenceView.model_validate(item) for item in evidence],
        is_sample=version is not None and version.extraction_version == "fictional-text-v1",
    )


async def list_resumes(session: AsyncSession, owner: UUID) -> ResumeList:
    ids = (
        await session.scalars(
            select(Resume.id)
            .where(Resume.owner_id == owner)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
            .limit(MAX_RESUMES)
        )
    ).all()
    return ResumeList(items=[await get_resume(session, owner, id) for id in ids])


async def save_upload(
    session: AsyncSession, owner: UUID, label: str, data: bytes, parsed: ParsedPdf
) -> ResumeDetail:
    user = await session.scalar(
        select(User)
        .where(User.id == owner)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        user is None
        or user.status != PrincipalStatus.ACTIVE
        or (user.expires_at is not None and user.expires_at <= datetime.now(UTC))
    ):
        raise HTTPException(401)
    count = await session.scalar(
        select(func.count()).select_from(Resume).where(Resume.owner_id == owner)
    )
    if count is not None and count >= MAX_RESUMES:
        raise HTTPException(409, detail="resume_limit")
    resume = Resume(owner_id=owner, label=label)
    session.add(resume)
    await session.flush()
    now = datetime.now(UTC)
    version = ResumeVersion(
        owner_id=owner,
        resume_id=resume.id,
        version=1,
        content_sha256=hashlib.sha256(data).hexdigest(),
        media_type="application/pdf",
        byte_count=len(data),
        page_count=parsed.page_count,
        storage_key=None,
        upload_expires_at=now + timedelta(hours=1),
        upload_deleted_at=now,
        extraction_version=EXTRACTION_VERSION,
        extraction_note=parsed.extraction_note,
        status=ProcessingStatus.READY,
    )
    session.add(version)
    await session.flush()
    session.add_all(
        [
            ResumeSkillEvidence(
                owner_id=owner,
                resume_version_id=version.id,
                category=EvidenceCategory(item.category),
                origin=EvidenceOrigin.RESUME,
                claim=item.claim,
                source_excerpt=item.source_excerpt,
                source_page=item.source_page,
                source_start=item.source_start,
                source_end=item.source_end,
                review_status=ReviewStatus.PROPOSED,
            )
            for item in parsed.evidence
        ]
    )
    await session.commit()
    return await get_resume(session, owner, resume.id)


async def lock_resume(session: AsyncSession, owner: UUID, id: UUID, revision: int) -> Resume:
    resume = await session.scalar(
        select(Resume)
        .where(Resume.owner_id == owner, Resume.id == id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if resume is None:
        raise HTTPException(404)
    if resume.revision != revision:
        raise HTTPException(409)
    return resume


async def owned_evidence(
    session: AsyncSession, owner: UUID, resume_id: UUID, evidence_id: UUID
) -> ResumeSkillEvidence:
    evidence = await session.scalar(
        select(ResumeSkillEvidence)
        .join(
            ResumeVersion,
            ResumeSkillEvidence.resume_version_id == ResumeVersion.id,
        )
        .where(
            ResumeSkillEvidence.id == evidence_id,
            ResumeSkillEvidence.owner_id == owner,
            ResumeVersion.owner_id == owner,
            ResumeVersion.resume_id == resume_id,
        )
    )
    if evidence is None:
        raise HTTPException(404)
    return evidence


async def save_evidence(
    session: AsyncSession,
    owner: UUID,
    id: UUID,
    body: EvidenceInput,
    evidence_id: UUID | None = None,
) -> ResumeDetail:
    resume = await lock_resume(session, owner, id, body.expected_revision)
    if evidence_id is None:
        version = await session.scalar(
            select(ResumeVersion)
            .where(
                ResumeVersion.owner_id == owner,
                ResumeVersion.resume_id == id,
            )
            .order_by(ResumeVersion.version.desc())
            .limit(1)
        )
        if version is None:
            raise HTTPException(409, detail="resume_no_version")
        count = await session.scalar(
            select(func.count())
            .select_from(ResumeSkillEvidence)
            .where(
                ResumeSkillEvidence.owner_id == owner,
                ResumeSkillEvidence.resume_version_id == version.id,
            )
        )
        if count is not None and count >= MAX_EVIDENCE:
            raise HTTPException(409, detail="evidence_limit")
        evidence = ResumeSkillEvidence(
            owner_id=owner,
            resume_version_id=version.id,
            origin=EvidenceOrigin.USER,
            claim=body.claim,
        )
        session.add(evidence)
    else:
        evidence = await owned_evidence(session, owner, id, evidence_id)
        evidence.user_correction = body.claim if body.claim != evidence.claim else None
    evidence.category = body.category
    evidence.review_status = body.review_status
    resume.revision += 1
    await session.execute(
        delete(AIAnalysis).where(AIAnalysis.owner_id == owner, AIAnalysis.resume_id == id)
    )
    await session.commit()
    return await get_resume(session, owner, id)


async def delete_evidence(
    session: AsyncSession, owner: UUID, id: UUID, evidence_id: UUID, revision: int
) -> ResumeDetail:
    resume = await lock_resume(session, owner, id, revision)
    evidence = await owned_evidence(session, owner, id, evidence_id)
    await session.delete(evidence)
    resume.revision += 1
    await session.execute(
        delete(AIAnalysis).where(AIAnalysis.owner_id == owner, AIAnalysis.resume_id == id)
    )
    await session.commit()
    return await get_resume(session, owner, id)


async def delete_resume(session: AsyncSession, owner: UUID, id: UUID, revision: int) -> None:
    resume = await lock_resume(session, owner, id, revision)
    await session.delete(resume)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if getattr(error.orig, "sqlstate", None) == "23503":
            raise HTTPException(409, detail="resume_in_use") from None
        raise
