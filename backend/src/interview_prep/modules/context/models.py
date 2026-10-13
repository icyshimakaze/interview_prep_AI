from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import OwnedRecord, Record, enum_column, owned_args, owned_fk


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class EvidenceCategory(StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    TOOL = "tool"
    PROJECT = "project"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    OTHER = "other"


class EvidenceOrigin(StrEnum):
    RESUME = "resume"
    USER = "user"


class RequirementPriority(StrEnum):
    ESSENTIAL = "essential"
    DESIRABLE = "desirable"


class TargetPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TargetStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    ARCHIVED = "archived"


class Skill(Record):
    "Reviewed global vocabulary; a mention is never evidence of competence."

    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("slug"),
        CheckConstraint("length(trim(name)) > 0", name="name"),
    )
    slug: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(150))
    aliases: Mapped[list["SkillAlias"]] = relationship(viewonly=True, lazy="raise")


class SkillAlias(Record):
    __tablename__ = "skill_aliases"
    __table_args__ = (UniqueConstraint("alias"),)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(150))


class TargetJob(OwnedRecord):
    __tablename__ = "job_targets"
    __table_args__ = owned_args(
        __tablename__,
        CheckConstraint("length(trim(title)) > 0", name="title"),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("notes IS NULL OR length(notes) <= 5000", name="notes_length"),
        CheckConstraint(
            "source_url IS NULL OR length(source_url) <= 2000", name="source_url_length"
        ),
    )
    title: Mapped[str] = mapped_column(String(200))
    organization: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(2000))
    notes: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[TargetPriority] = mapped_column(
        enum_column(TargetPriority, "target_priority"),
        default=TargetPriority.NORMAL,
        server_default="normal",
    )
    status: Mapped[TargetStatus] = mapped_column(
        enum_column(TargetStatus, "target_status"),
        default=TargetStatus.SAVED,
        server_default="saved",
    )
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    versions: Mapped[list["TargetJobVersion"]] = relationship(viewonly=True, lazy="raise")


class TargetJobVersion(OwnedRecord):
    __tablename__ = "job_target_versions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("target_job_id", "job_targets"),
        UniqueConstraint("owner_id", "target_job_id", "version"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("length(description) BETWEEN 1 AND 30000", name="description_length"),
    )
    target_job_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list["JobSkillRequirement"]] = relationship(viewonly=True, lazy="raise")


class JobSkillRequirement(OwnedRecord):
    __tablename__ = "job_skill_requirements"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("target_job_version_id", "job_target_versions"),
        UniqueConstraint("owner_id", "target_job_version_id", "skill_id"),
        CheckConstraint("length(trim(source_excerpt)) > 0", name="source_excerpt"),
        CheckConstraint("source_start >= 0 AND source_end > source_start", name="source_span"),
    )
    target_job_version_id: Mapped[UUID] = mapped_column(index=True)
    skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), index=True
    )
    source_excerpt: Mapped[str] = mapped_column(String(2000))
    source_start: Mapped[int] = mapped_column(Integer)
    source_end: Mapped[int] = mapped_column(Integer)
    priority: Mapped[RequirementPriority] = mapped_column(
        enum_column(RequirementPriority, "requirement_priority")
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus, "requirement_review")
    )


class Resume(OwnedRecord):
    __tablename__ = "resumes"
    __table_args__ = owned_args(
        __tablename__,
        CheckConstraint("length(trim(label)) > 0", name="label"),
        CheckConstraint("revision > 0", name="revision"),
    )
    label: Mapped[str] = mapped_column(String(200))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    versions: Mapped[list["ResumeVersion"]] = relationship(viewonly=True, lazy="raise")


class ResumeVersion(OwnedRecord):
    __tablename__ = "resume_versions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("resume_id", "resumes"),
        UniqueConstraint("owner_id", "resume_id", "version"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="content_digest"),
        CheckConstraint("byte_count BETWEEN 1 AND 5242880", name="upload_size"),
        CheckConstraint("page_count IS NULL OR page_count BETWEEN 1 AND 20", name="page_count"),
        CheckConstraint("upload_expires_at > created_at", name="upload_expiry"),
    )
    resume_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer)
    content_sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(100))
    byte_count: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    storage_key: Mapped[str | None] = mapped_column(String(500))
    upload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    upload_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extraction_version: Mapped[str | None] = mapped_column(String(100))
    extraction_note: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[ProcessingStatus] = mapped_column(enum_column(ProcessingStatus, "resume_status"))
    evidence: Mapped[list["ResumeSkillEvidence"]] = relationship(viewonly=True, lazy="raise")


class ResumeSkillEvidence(OwnedRecord):
    __tablename__ = "resume_skill_evidence"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("resume_version_id", "resume_versions"),
        CheckConstraint(
            "(origin = 'resume' AND source_start IS NOT NULL AND source_end IS NOT NULL "
            "AND source_start >= 0 AND source_end > source_start AND source_excerpt IS NOT NULL "
            "AND length(trim(source_excerpt)) > 0) OR "
            "(origin = 'user' AND source_start IS NULL AND source_end IS NULL "
            "AND source_excerpt IS NULL AND source_page IS NULL)",
            name="source_span",
        ),
        CheckConstraint("source_page IS NULL OR source_page BETWEEN 1 AND 20", name="source_page"),
        CheckConstraint("length(trim(claim)) > 0", name="claim_and_excerpt"),
    )
    resume_version_id: Mapped[UUID] = mapped_column(index=True)
    skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), index=True
    )
    claim: Mapped[str] = mapped_column(String(2000))
    category: Mapped[EvidenceCategory] = mapped_column(
        enum_column(EvidenceCategory, "evidence_category"),
        default=EvidenceCategory.OTHER,
        server_default="other",
    )
    origin: Mapped[EvidenceOrigin] = mapped_column(
        enum_column(EvidenceOrigin, "evidence_origin"),
        default=EvidenceOrigin.RESUME,
        server_default="resume",
    )
    source_excerpt: Mapped[str | None] = mapped_column(String(2000))
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_start: Mapped[int | None] = mapped_column(Integer)
    source_end: Mapped[int | None] = mapped_column(Integer)
    user_correction: Mapped[str | None] = mapped_column(String(2000))
    review_status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus, "evidence_review")
    )
