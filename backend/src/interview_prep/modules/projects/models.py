from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import OwnedRecord, enum_column, owned_args, owned_fk
from interview_prep.modules.context.models import ProcessingStatus


class ProjectOrigin(StrEnum):
    GITHUB = "github"
    ZIP = "zip"


class ProjectRepository(OwnedRecord):
    __tablename__ = "project_repositories"
    __table_args__ = owned_args(
        __tablename__,
        CheckConstraint("length(trim(name)) > 0", name="name"),
        CheckConstraint(
            "(origin = 'github' AND github_owner IS NOT NULL AND github_repository IS NOT NULL "
            "AND github_owner ~ '^[A-Za-z0-9-]{1,39}$' "
            "AND github_repository ~ '^[A-Za-z0-9_.-]{1,100}$') OR "
            "(origin = 'zip' AND github_owner IS NULL AND github_repository IS NULL)",
            name="input_origin",
        ),
    )
    name: Mapped[str] = mapped_column(String(200))
    origin: Mapped[ProjectOrigin] = mapped_column(enum_column(ProjectOrigin, "project_origin"))
    github_owner: Mapped[str | None] = mapped_column(String(39))
    github_repository: Mapped[str | None] = mapped_column(String(100))
    analyses: Mapped[list["ProjectAnalysis"]] = relationship(viewonly=True, lazy="raise")


class ProjectAnalysis(OwnedRecord):
    "One immutable input snapshot and its versioned static-analysis result."

    __tablename__ = "project_analyses"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("repository_id", "project_repositories"),
        UniqueConstraint("owner_id", "repository_id", "archive_sha256", "analysis_version"),
        CheckConstraint("archive_sha256 ~ '^[0-9a-f]{64}$'", name="archive_digest"),
        CheckConstraint(
            "commit_sha IS NULL OR commit_sha ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'", name="commit_sha"
        ),
        CheckConstraint("archive_bytes BETWEEN 1 AND 10485760", name="archive_size"),
        CheckConstraint("upload_expires_at > created_at", name="upload_expiry"),
        CheckConstraint(
            "summary IS NULL OR octet_length(summary::text) <= 16384", name="summary_size"
        ),
    )
    repository_id: Mapped[UUID] = mapped_column(index=True)
    archive_sha256: Mapped[str] = mapped_column(String(64))
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    archive_bytes: Mapped[int] = mapped_column(Integer)
    archive_storage_key: Mapped[str | None] = mapped_column(String(500))
    upload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    upload_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    analysis_version: Mapped[str] = mapped_column(String(100))
    status: Mapped[ProcessingStatus] = mapped_column(
        enum_column(ProcessingStatus, "project_analysis_status")
    )
    error_code: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    files: Mapped[list["SourceFile"]] = relationship(viewonly=True, lazy="raise")
    facts: Mapped[list["ProjectFact"]] = relationship(viewonly=True, lazy="raise")
    questions: Mapped[list["ProjectQuestion"]] = relationship(viewonly=True, lazy="raise")


class SourceFile(OwnedRecord):
    __tablename__ = "project_source_files"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("analysis_id", "project_analyses"),
        UniqueConstraint("owner_id", "id", "analysis_id"),
        UniqueConstraint("analysis_id", "path"),
        CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="content_digest"),
        CheckConstraint("byte_count BETWEEN 0 AND 262144 AND line_count >= 0", name="file_budget"),
        CheckConstraint(
            "length(path) > 0 AND path NOT LIKE '/%' "
            "AND path !~ '(^|/)\\.\\.(/|$)' AND path !~ '[:\\\\]'",
            name="relative_path",
        ),
        CheckConstraint(
            "retained_text IS NULL OR octet_length(retained_text) <= 262144", name="text_budget"
        ),
    )
    analysis_id: Mapped[UUID] = mapped_column(index=True)
    path: Mapped[str] = mapped_column(String(500))
    content_sha256: Mapped[str] = mapped_column(String(64))
    byte_count: Mapped[int] = mapped_column(Integer)
    line_count: Mapped[int] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(100))
    retained_text: Mapped[str | None] = mapped_column(Text)


class ProjectFact(OwnedRecord):
    __tablename__ = "project_facts"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("analysis_id", "project_analyses"),
        ForeignKeyConstraint(
            ["owner_id", "source_file_id", "analysis_id"],
            [
                "project_source_files.owner_id",
                "project_source_files.id",
                "project_source_files.analysis_id",
            ],
            ondelete="CASCADE",
        ),
        CheckConstraint("line_start > 0 AND line_end >= line_start", name="line_range"),
        CheckConstraint("length(trim(description)) > 0", name="description"),
    )
    analysis_id: Mapped[UUID] = mapped_column(index=True)
    source_file_id: Mapped[UUID] = mapped_column(index=True)
    fact_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(2000))
    line_start: Mapped[int] = mapped_column(Integer)
    line_end: Mapped[int] = mapped_column(Integer)
    is_inference: Mapped[bool] = mapped_column(default=False, server_default="false")


class ProjectQuestion(OwnedRecord):
    __tablename__ = "project_questions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("analysis_id", "project_analyses"),
        UniqueConstraint("owner_id", "id", "analysis_id"),
        UniqueConstraint("analysis_id", "question_version_id"),
        CheckConstraint(
            "context IS NULL OR octet_length(context::text) <= 4096", name="context_size"
        ),
    )
    analysis_id: Mapped[UUID] = mapped_column(index=True)
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    generation_method: Mapped[str] = mapped_column(String(100))
    generator_version: Mapped[str] = mapped_column(String(100))
    context: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    citations: Mapped[list["ProjectQuestionCitation"]] = relationship(viewonly=True, lazy="raise")


class ProjectQuestionCitation(OwnedRecord):
    __tablename__ = "project_question_citations"
    __table_args__ = owned_args(
        __tablename__,
        ForeignKeyConstraint(
            ["owner_id", "project_question_id", "analysis_id"],
            ["project_questions.owner_id", "project_questions.id", "project_questions.analysis_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["owner_id", "source_file_id", "analysis_id"],
            [
                "project_source_files.owner_id",
                "project_source_files.id",
                "project_source_files.analysis_id",
            ],
            ondelete="CASCADE",
        ),
        UniqueConstraint("project_question_id", "source_file_id", "line_start", "line_end"),
        CheckConstraint("line_start > 0 AND line_end >= line_start", name="line_range"),
    )
    analysis_id: Mapped[UUID] = mapped_column(index=True)
    project_question_id: Mapped[UUID] = mapped_column(index=True)
    source_file_id: Mapped[UUID] = mapped_column(index=True)
    line_start: Mapped[int] = mapped_column(Integer)
    line_end: Mapped[int] = mapped_column(Integer)
