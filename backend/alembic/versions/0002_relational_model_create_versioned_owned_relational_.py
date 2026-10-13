"""Create versioned owned relational domain model

Revision ID: 0002_relational_model
Revises: 0001_demo_foundation
"""

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_relational_model"
down_revision: str | Sequence[str] | None = "0001_demo_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Reviewed explicit schema; no runtime ORM imports.
    op.create_table(
        "principals",
        sa.Column(
            "kind",
            sa.Enum(
                "account", "demo", name="principal_kind", native_enum=False, create_constraint=False
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "suspended",
                "deleting",
                name="principal_status",
                native_enum=False,
                create_constraint=False,
            ),
            server_default="active",
            nullable=False,
        ),
        sa.Column("issuer", sa.String(length=500), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_generation", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "(kind = 'account' AND issuer IS NOT NULL AND subject IS NOT NULL "
                "AND expires_at IS NULL) OR (kind = 'demo' AND issuer IS NULL AND "
                "subject IS NULL AND expires_at IS NOT NULL AND expires_at > creat"
                "ed_at)"
            ),
            name=op.f("ck_principals_identity_kind"),
        ),
        sa.CheckConstraint(
            "kind IN ('account', 'demo')", name=op.f("ck_principals_principal_kind")
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'deleting')",
            name=op.f("ck_principals_principal_status"),
        ),
        sa.CheckConstraint(
            "deletion_generation >= 0", name=op.f("ck_principals_deletion_generation")
        ),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_principals_timestamp_order")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_principals")),
        sa.UniqueConstraint("issuer", "subject", name=op.f("uq_principals_issuer_subject")),
    )
    op.create_index(op.f("ix_principals_expires_at"), "principals", ["expires_at"], unique=False)
    op.create_table(
        "skills",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_skills_name")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
        sa.UniqueConstraint("slug", name=op.f("uq_skills_slug")),
    )
    op.create_table(
        "candidate_profiles",
        sa.Column("target_role", sa.String(length=200), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=True),
        sa.Column(
            "experience_band",
            sa.Enum(
                "student",
                "entry",
                "mid",
                "senior",
                name="experience_band",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "experience_band IN ('student', 'entry', 'mid', 'senior')",
            name=op.f("ck_candidate_profiles_experience_band"),
        ),
        sa.CheckConstraint(
            "length(trim(target_role)) > 0", name=op.f("ck_candidate_profiles_target_role")
        ),
        sa.CheckConstraint(
            "length(trim(timezone)) > 0", name=op.f("ck_candidate_profiles_timezone")
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_candidate_profiles_revision")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_candidate_profiles_timestamp_order")
        ),
        sa.CheckConstraint(
            "weekly_minutes BETWEEN 15 AND 10080", name=op.f("ck_candidate_profiles_study_budget")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_candidate_profiles_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_profiles")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_candidate_profiles_owner_id_id")),
        sa.UniqueConstraint("owner_id", name=op.f("uq_candidate_profiles_owner_id")),
    )
    op.create_index(
        "ix_candidate_profiles_owner_created",
        "candidate_profiles",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "job_targets",
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name=op.f("ck_job_targets_title")),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_job_targets_timestamp_order")),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_job_targets_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_targets")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_job_targets_owner_id_id")),
    )
    op.create_index(
        "ix_job_targets_owner_created", "job_targets", ["owner_id", "created_at"], unique=False
    )
    op.create_table(
        "project_repositories",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "origin",
            sa.Enum(
                "github", "zip", name="project_origin", native_enum=False, create_constraint=False
            ),
            nullable=False,
        ),
        sa.Column("github_owner", sa.String(length=39), nullable=True),
        sa.Column("github_repository", sa.String(length=100), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "(origin = 'github' AND github_owner IS NOT NULL AND github_reposi"
                "tory IS NOT NULL AND github_owner ~ '^[A-Za-z0-9-]{1,39}$' AND gi"
                "thub_repository ~ '^[A-Za-z0-9_.-]{1,100}$') OR (origin = 'zip' A"
                "ND github_owner IS NULL AND github_repository IS NULL)"
            ),
            name=op.f("ck_project_repositories_input_origin"),
        ),
        sa.CheckConstraint(
            "origin IN ('github', 'zip')", name=op.f("ck_project_repositories_project_origin")
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_project_repositories_name")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_repositories_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_repositories_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_repositories")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_project_repositories_owner_id_id")),
    )
    op.create_index(
        "ix_project_repositories_owner_created",
        "project_repositories",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "questions",
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "global",
                "private",
                name="question_visibility",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("canonical_concept", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "(visibility = 'global' AND owner_id IS NULL) OR (visibility = 'pr"
                "ivate' AND owner_id IS NOT NULL)"
            ),
            name=op.f("ck_questions_visibility_owner"),
        ),
        sa.CheckConstraint(
            "visibility IN ('global', 'private')", name=op.f("ck_questions_question_visibility")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_questions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_questions_owner_id_id")),
    )
    op.create_index(
        op.f("ix_questions_canonical_concept"), "questions", ["canonical_concept"], unique=False
    )
    op.create_index(op.f("ix_questions_owner_id"), "questions", ["owner_id"], unique=False)
    op.create_table(
        "resumes",
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(label)) > 0", name=op.f("ck_resumes_label")),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_resumes_timestamp_order")),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_resumes_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resumes")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_resumes_owner_id_id")),
    )
    op.create_index("ix_resumes_owner_created", "resumes", ["owner_id", "created_at"], unique=False)
    op.create_table(
        "skill_aliases",
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("alias", sa.String(length=150), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_skill_aliases_skill_id_skills"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_aliases")),
        sa.UniqueConstraint("alias", name=op.f("uq_skill_aliases_alias")),
    )
    op.create_index(op.f("ix_skill_aliases_skill_id"), "skill_aliases", ["skill_id"], unique=False)
    op.create_table(
        "job_target_versions",
        sa.Column("target_job_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(description) BETWEEN 1 AND 30000",
            name=op.f("ck_job_target_versions_description_length"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_job_target_versions_timestamp_order")
        ),
        sa.CheckConstraint("version > 0", name=op.f("ck_job_target_versions_version")),
        sa.ForeignKeyConstraint(
            ["owner_id", "target_job_id"],
            ["job_targets.owner_id", "job_targets.id"],
            name=op.f("fk_job_target_versions_owner_id_job_targets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_job_target_versions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_target_versions")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_job_target_versions_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "target_job_id",
            "version",
            name=op.f("uq_job_target_versions_owner_id_target_job_id_version"),
        ),
    )
    op.create_index(
        "ix_job_target_versions_owner_created",
        "job_target_versions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_target_versions_target_job_id"),
        "job_target_versions",
        ["target_job_id"],
        unique=False,
    )
    op.create_table(
        "project_analyses",
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("archive_sha256", sa.String(length=64), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("archive_bytes", sa.Integer(), nullable=False),
        sa.Column("archive_storage_key", sa.String(length=500), nullable=True),
        sa.Column("upload_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("upload_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analysis_version", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "ready",
                "failed",
                name="project_analysis_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "archive_sha256 ~ '^[0-9a-f]{64}$'", name=op.f("ck_project_analyses_archive_digest")
        ),
        sa.CheckConstraint(
            "commit_sha IS NULL OR commit_sha ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'",
            name=op.f("ck_project_analyses_commit_sha"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed')",
            name=op.f("ck_project_analyses_project_analysis_status"),
        ),
        sa.CheckConstraint(
            "archive_bytes BETWEEN 1 AND 10485760", name=op.f("ck_project_analyses_archive_size")
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_analyses_timestamp_order")
        ),
        sa.CheckConstraint(
            "upload_expires_at > created_at", name=op.f("ck_project_analyses_upload_expiry")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "repository_id"],
            ["project_repositories.owner_id", "project_repositories.id"],
            name=op.f("fk_project_analyses_owner_id_project_repositories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_analyses_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_analyses")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_project_analyses_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "repository_id",
            "archive_sha256",
            "analysis_version",
            name=op.f("uq_project_analyses_owner_id_repository_id_archive_sha256_analysis_version"),
        ),
    )
    op.create_index(
        "ix_project_analyses_owner_created",
        "project_analyses",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_analyses_repository_id"),
        "project_analyses",
        ["repository_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_analyses_upload_expires_at"),
        "project_analyses",
        ["upload_expires_at"],
        unique=False,
    )
    op.create_table(
        "question_versions",
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column(
            "question_type",
            sa.Enum(
                "multiple_choice",
                "short_answer",
                "written",
                "design",
                "behavioral",
                name="question_type",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "difficulty",
            sa.Enum(
                "easy",
                "medium",
                "hard",
                name="question_difficulty",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "published",
                "retired",
                name="publication_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=20), server_default="en", nullable=False),
        sa.Column("source_file", sa.String(length=500), nullable=True),
        sa.Column("source_commit", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.String(length=2000), nullable=True),
        sa.Column("source_license", sa.String(length=200), nullable=True),
        sa.Column("original_topic", sa.String(length=150), nullable=True),
        sa.Column("provenance_reviewed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("rubric_version", sa.String(length=100), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name=op.f("ck_question_versions_question_difficulty"),
        ),
        sa.CheckConstraint(
            (
                "question_type IN ('multiple_choice', 'short_answer', 'written', '"
                "design', 'behavioral')"
            ),
            name=op.f("ck_question_versions_question_type"),
        ),
        sa.CheckConstraint(
            (
                "status <> 'published' OR (prompt IS NOT NULL AND question_type IS"
                " NOT NULL AND difficulty IS NOT NULL AND provenance_reviewed AND "
                "source_license IS NOT NULL)"
            ),
            name=op.f("ck_question_versions_published_content"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'retired')",
            name=op.f("ck_question_versions_publication_status"),
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name=op.f("ck_question_versions_title")),
        sa.CheckConstraint(
            "prompt IS NULL OR length(prompt) BETWEEN 1 AND 30000",
            name=op.f("ck_question_versions_prompt_length"),
        ),
        sa.CheckConstraint("version > 0", name=op.f("ck_question_versions_version")),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name=op.f("fk_question_versions_question_id_questions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_versions")),
        sa.UniqueConstraint(
            "question_id", "version", name=op.f("uq_question_versions_question_id_version")
        ),
    )
    op.create_index(
        op.f("ix_question_versions_question_id"), "question_versions", ["question_id"], unique=False
    )
    op.create_index(
        op.f("ix_question_versions_status"), "question_versions", ["status"], unique=False
    )
    op.create_table(
        "resume_versions",
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("byte_count", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("upload_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("upload_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extraction_version", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "ready",
                "failed",
                name="resume_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'", name=op.f("ck_resume_versions_content_digest")
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed')",
            name=op.f("ck_resume_versions_resume_status"),
        ),
        sa.CheckConstraint(
            "byte_count BETWEEN 1 AND 5242880", name=op.f("ck_resume_versions_upload_size")
        ),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count BETWEEN 1 AND 20",
            name=op.f("ck_resume_versions_page_count"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_resume_versions_timestamp_order")
        ),
        sa.CheckConstraint(
            "upload_expires_at > created_at", name=op.f("ck_resume_versions_upload_expiry")
        ),
        sa.CheckConstraint("version > 0", name=op.f("ck_resume_versions_version")),
        sa.ForeignKeyConstraint(
            ["owner_id", "resume_id"],
            ["resumes.owner_id", "resumes.id"],
            name=op.f("fk_resume_versions_owner_id_resumes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_resume_versions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resume_versions")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_resume_versions_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "resume_id",
            "version",
            name=op.f("uq_resume_versions_owner_id_resume_id_version"),
        ),
    )
    op.create_index(
        "ix_resume_versions_owner_created",
        "resume_versions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resume_versions_resume_id"), "resume_versions", ["resume_id"], unique=False
    )
    op.create_index(
        op.f("ix_resume_versions_upload_expires_at"),
        "resume_versions",
        ["upload_expires_at"],
        unique=False,
    )
    op.create_table(
        "assessments",
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_job_version_id", sa.Uuid(), nullable=True),
        sa.Column("resume_version_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "ready",
                "archived",
                name="assessment_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("context_version", sa.String(length=100), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'ready', 'archived')",
            name=op.f("ck_assessments_assessment_status"),
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_assessments_revision")),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_assessments_timestamp_order")),
        sa.ForeignKeyConstraint(
            ["owner_id", "resume_version_id"],
            ["resume_versions.owner_id", "resume_versions.id"],
            name=op.f("fk_assessments_owner_id_resume_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "target_job_version_id"],
            ["job_target_versions.owner_id", "job_target_versions.id"],
            name=op.f("fk_assessments_owner_id_job_target_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_assessments_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessments")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_assessments_owner_id_id")),
    )
    op.create_index(
        "ix_assessments_owner_created", "assessments", ["owner_id", "created_at"], unique=False
    )
    op.create_index(
        "ix_assessments_owner_status", "assessments", ["owner_id", "status"], unique=False
    )
    op.create_index(
        op.f("ix_assessments_resume_version_id"), "assessments", ["resume_version_id"], unique=False
    )
    op.create_index(
        op.f("ix_assessments_target_job_version_id"),
        "assessments",
        ["target_job_version_id"],
        unique=False,
    )
    op.create_table(
        "bookmarks",
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.String(length=2000), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_bookmarks_timestamp_order")),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_bookmarks_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_bookmarks_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookmarks")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_bookmarks_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "question_version_id",
            name=op.f("uq_bookmarks_owner_id_question_version_id"),
        ),
    )
    op.create_index(
        "ix_bookmarks_owner_created", "bookmarks", ["owner_id", "created_at"], unique=False
    )
    op.create_index(
        op.f("ix_bookmarks_question_version_id"), "bookmarks", ["question_version_id"], unique=False
    )
    op.create_table(
        "interview_sessions",
        sa.Column(
            "mode",
            sa.Enum(
                "mock_interview",
                "project_defense",
                name="interview_mode",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "active",
                "paused",
                "finalizing",
                "completed",
                "abandoned",
                "failed",
                name="interview_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("target_job_version_id", sa.Uuid(), nullable=True),
        sa.Column("resume_version_id", sa.Uuid(), nullable=True),
        sa.Column("project_analysis_id", sa.Uuid(), nullable=True),
        sa.Column("context_version", sa.String(length=100), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("main_question_limit", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name=op.f("ck_interview_sessions_completed_timestamp"),
        ),
        sa.CheckConstraint(
            "mode <> 'project_defense' OR project_analysis_id IS NOT NULL",
            name=op.f("ck_interview_sessions_project_context"),
        ),
        sa.CheckConstraint(
            "mode IN ('mock_interview', 'project_defense')",
            name=op.f("ck_interview_sessions_interview_mode"),
        ),
        sa.CheckConstraint(
            (
                "status IN ('draft', 'active', 'paused', 'finalizing', 'completed'"
                ", 'abandoned', 'failed')"
            ),
            name=op.f("ck_interview_sessions_interview_status"),
        ),
        sa.CheckConstraint(
            "main_question_limit BETWEEN 1 AND 10",
            name=op.f("ck_interview_sessions_question_limit"),
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_interview_sessions_revision")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_interview_sessions_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_analysis_id"],
            ["project_analyses.owner_id", "project_analyses.id"],
            name=op.f("fk_interview_sessions_owner_id_project_analyses"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "resume_version_id"],
            ["resume_versions.owner_id", "resume_versions.id"],
            name=op.f("fk_interview_sessions_owner_id_resume_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "target_job_version_id"],
            ["job_target_versions.owner_id", "job_target_versions.id"],
            name=op.f("fk_interview_sessions_owner_id_job_target_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_interview_sessions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_sessions")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_interview_sessions_owner_id_id")),
    )
    op.create_index(
        "ix_interview_sessions_owner_created",
        "interview_sessions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_interview_sessions_owner_status",
        "interview_sessions",
        ["owner_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_sessions_project_analysis_id"),
        "interview_sessions",
        ["project_analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_sessions_resume_version_id"),
        "interview_sessions",
        ["resume_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_sessions_target_job_version_id"),
        "interview_sessions",
        ["target_job_version_id"],
        unique=False,
    )
    op.create_table(
        "job_skill_requirements",
        sa.Column("target_job_version_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=True),
        sa.Column("source_excerpt", sa.String(length=2000), nullable=False),
        sa.Column("source_start", sa.Integer(), nullable=False),
        sa.Column("source_end", sa.Integer(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum(
                "essential",
                "desirable",
                name="requirement_priority",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "review_status",
            sa.Enum(
                "proposed",
                "confirmed",
                "rejected",
                name="requirement_review",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "priority IN ('essential', 'desirable')",
            name=op.f("ck_job_skill_requirements_requirement_priority"),
        ),
        sa.CheckConstraint(
            "review_status IN ('proposed', 'confirmed', 'rejected')",
            name=op.f("ck_job_skill_requirements_requirement_review"),
        ),
        sa.CheckConstraint(
            "length(trim(source_excerpt)) > 0",
            name=op.f("ck_job_skill_requirements_source_excerpt"),
        ),
        sa.CheckConstraint(
            "source_start >= 0 AND source_end > source_start",
            name=op.f("ck_job_skill_requirements_source_span"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_job_skill_requirements_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "target_job_version_id"],
            ["job_target_versions.owner_id", "job_target_versions.id"],
            name=op.f("fk_job_skill_requirements_owner_id_job_target_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_job_skill_requirements_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_job_skill_requirements_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_skill_requirements")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_job_skill_requirements_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "target_job_version_id",
            "skill_id",
            name=op.f("uq_job_skill_requirements_owner_id_target_job_version_id_skill_id"),
        ),
    )
    op.create_index(
        "ix_job_skill_requirements_owner_created",
        "job_skill_requirements",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_skill_requirements_skill_id"),
        "job_skill_requirements",
        ["skill_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_skill_requirements_target_job_version_id"),
        "job_skill_requirements",
        ["target_job_version_id"],
        unique=False,
    )
    op.create_table(
        "project_questions",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("generation_method", sa.String(length=100), nullable=False),
        sa.Column("generator_version", sa.String(length=100), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_questions_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "analysis_id"],
            ["project_analyses.owner_id", "project_analyses.id"],
            name=op.f("fk_project_questions_owner_id_project_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_questions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_project_questions_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_questions")),
        sa.UniqueConstraint(
            "analysis_id",
            "question_version_id",
            name=op.f("uq_project_questions_analysis_id_question_version_id"),
        ),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "analysis_id",
            name=op.f("uq_project_questions_owner_id_id_analysis_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_project_questions_owner_id_id")),
    )
    op.create_index(
        op.f("ix_project_questions_analysis_id"), "project_questions", ["analysis_id"], unique=False
    )
    op.create_index(
        "ix_project_questions_owner_created",
        "project_questions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_questions_question_version_id"),
        "project_questions",
        ["question_version_id"],
        unique=False,
    )
    op.create_table(
        "project_source_files",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_count", sa.Integer(), nullable=False),
        sa.Column("line_count", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=100), nullable=True),
        sa.Column("retained_text", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'", name=op.f("ck_project_source_files_content_digest")
        ),
        sa.CheckConstraint(
            (
                "length(path) > 0 AND path NOT LIKE '/%' AND path !~ '(^|/)\\.\\.(/|"
                "$)' AND path !~ '[:\\\\]'"
            ),
            name=op.f("ck_project_source_files_relative_path"),
        ),
        sa.CheckConstraint(
            "byte_count BETWEEN 0 AND 262144 AND line_count >= 0",
            name=op.f("ck_project_source_files_file_budget"),
        ),
        sa.CheckConstraint(
            "retained_text IS NULL OR octet_length(retained_text) <= 262144",
            name=op.f("ck_project_source_files_text_budget"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_source_files_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "analysis_id"],
            ["project_analyses.owner_id", "project_analyses.id"],
            name=op.f("fk_project_source_files_owner_id_project_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_source_files_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_source_files")),
        sa.UniqueConstraint(
            "analysis_id", "path", name=op.f("uq_project_source_files_analysis_id_path")
        ),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "analysis_id",
            name=op.f("uq_project_source_files_owner_id_id_analysis_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_project_source_files_owner_id_id")),
    )
    op.create_index(
        op.f("ix_project_source_files_analysis_id"),
        "project_source_files",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_source_files_owner_created",
        "project_source_files",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "question_options",
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=4000), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(text)) > 0", name=op.f("ck_question_options_option_text")),
        sa.CheckConstraint("position > 0", name=op.f("ck_question_options_position")),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_question_options_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_options")),
        sa.UniqueConstraint(
            "question_version_id", "id", name=op.f("uq_question_options_question_version_id_id")
        ),
        sa.UniqueConstraint(
            "question_version_id",
            "position",
            name=op.f("uq_question_options_question_version_id_position"),
        ),
    )
    op.create_index(
        op.f("ix_question_options_question_version_id"),
        "question_options",
        ["question_version_id"],
        unique=False,
    )
    op.create_table(
        "question_rubric_criteria",
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("weight", sa.Numeric(precision=6, scale=5, asdecimal=False), nullable=False),
        sa.Column("anchor_0", sa.String(length=2000), nullable=False),
        sa.Column("anchor_1", sa.String(length=2000), nullable=False),
        sa.Column("anchor_2", sa.String(length=2000), nullable=False),
        sa.Column("anchor_3", sa.String(length=2000), nullable=False),
        sa.Column("anchor_4", sa.String(length=2000), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "weight > 0 AND weight <= 1", name=op.f("ck_question_rubric_criteria_weight")
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_question_rubric_criteria_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_rubric_criteria")),
        sa.UniqueConstraint(
            "question_version_id",
            "code",
            name=op.f("uq_question_rubric_criteria_question_version_id_code"),
        ),
        sa.UniqueConstraint(
            "question_version_id",
            "id",
            name=op.f("uq_question_rubric_criteria_question_version_id_id"),
        ),
    )
    op.create_index(
        op.f("ix_question_rubric_criteria_question_version_id"),
        "question_rubric_criteria",
        ["question_version_id"],
        unique=False,
    )
    op.create_table(
        "question_skills",
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_question_skills_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_question_skills_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_skills")),
        sa.UniqueConstraint(
            "question_version_id",
            "skill_id",
            name=op.f("uq_question_skills_question_version_id_skill_id"),
        ),
    )
    op.create_index(
        op.f("ix_question_skills_question_version_id"),
        "question_skills",
        ["question_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_skills_skill_id"), "question_skills", ["skill_id"], unique=False
    )
    op.create_table(
        "resume_skill_evidence",
        sa.Column("resume_version_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=True),
        sa.Column("claim", sa.String(length=2000), nullable=False),
        sa.Column("source_excerpt", sa.String(length=2000), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_start", sa.Integer(), nullable=False),
        sa.Column("source_end", sa.Integer(), nullable=False),
        sa.Column("user_correction", sa.String(length=2000), nullable=True),
        sa.Column(
            "review_status",
            sa.Enum(
                "proposed",
                "confirmed",
                "rejected",
                name="evidence_review",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "review_status IN ('proposed', 'confirmed', 'rejected')",
            name=op.f("ck_resume_skill_evidence_evidence_review"),
        ),
        sa.CheckConstraint(
            "length(trim(claim)) > 0 AND length(trim(source_excerpt)) > 0",
            name=op.f("ck_resume_skill_evidence_claim_and_excerpt"),
        ),
        sa.CheckConstraint(
            "source_page IS NULL OR source_page BETWEEN 1 AND 20",
            name=op.f("ck_resume_skill_evidence_source_page"),
        ),
        sa.CheckConstraint(
            "source_start >= 0 AND source_end > source_start",
            name=op.f("ck_resume_skill_evidence_source_span"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_resume_skill_evidence_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "resume_version_id"],
            ["resume_versions.owner_id", "resume_versions.id"],
            name=op.f("fk_resume_skill_evidence_owner_id_resume_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_resume_skill_evidence_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_resume_skill_evidence_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resume_skill_evidence")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_resume_skill_evidence_owner_id_id")),
    )
    op.create_index(
        "ix_resume_skill_evidence_owner_created",
        "resume_skill_evidence",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resume_skill_evidence_resume_version_id"),
        "resume_skill_evidence",
        ["resume_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resume_skill_evidence_skill_id"),
        "resume_skill_evidence",
        ["skill_id"],
        unique=False,
    )
    op.create_table(
        "roadmaps",
        sa.Column("target_job_version_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "proposed",
                "active",
                "archived",
                name="roadmap_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("context_version", sa.String(length=100), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('proposed', 'active', 'archived')", name=op.f("ck_roadmaps_roadmap_status")
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_roadmaps_revision")),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_roadmaps_timestamp_order")),
        sa.CheckConstraint(
            "weekly_minutes BETWEEN 15 AND 10080", name=op.f("ck_roadmaps_study_budget")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "target_job_version_id"],
            ["job_target_versions.owner_id", "job_target_versions.id"],
            name=op.f("fk_roadmaps_owner_id_job_target_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_roadmaps_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roadmaps")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_roadmaps_owner_id_id")),
    )
    op.create_index(
        "ix_roadmaps_owner_created", "roadmaps", ["owner_id", "created_at"], unique=False
    )
    op.create_index("ix_roadmaps_owner_status", "roadmaps", ["owner_id", "status"], unique=False)
    op.create_index(
        op.f("ix_roadmaps_target_job_version_id"),
        "roadmaps",
        ["target_job_version_id"],
        unique=False,
    )
    op.create_table(
        "short_answer_keys",
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("normalized_answer", sa.String(length=2000), nullable=False),
        sa.Column("normalization_version", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(normalized_answer)) > 0", name=op.f("ck_short_answer_keys_answer_text")
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_short_answer_keys_question_version_id_question_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_short_answer_keys")),
        sa.UniqueConstraint(
            "question_version_id",
            "normalized_answer",
            name=op.f("uq_short_answer_keys_question_version_id_normalized_answer"),
        ),
    )
    op.create_index(
        op.f("ix_short_answer_keys_question_version_id"),
        "short_answer_keys",
        ["question_version_id"],
        unique=False,
    )
    op.create_table(
        "assessment_attempts",
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("submission_key", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress",
                "completed",
                "abandoned",
                name="attempt_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name=op.f("ck_assessment_attempts_completed_timestamp"),
        ),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'abandoned')",
            name=op.f("ck_assessment_attempts_attempt_status"),
        ),
        sa.CheckConstraint(
            "attempt_number > 0 AND revision > 0",
            name=op.f("ck_assessment_attempts_positive_versions"),
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name=op.f("ck_assessment_attempts_completion_time"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_assessment_attempts_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_id"],
            ["assessments.owner_id", "assessments.id"],
            name=op.f("fk_assessment_attempts_owner_id_assessments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_assessment_attempts_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_attempts")),
        sa.UniqueConstraint(
            "owner_id",
            "assessment_id",
            "attempt_number",
            name=op.f("uq_assessment_attempts_owner_id_assessment_id_attempt_number"),
        ),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "assessment_id",
            name=op.f("uq_assessment_attempts_owner_id_id_assessment_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_assessment_attempts_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id",
            "submission_key",
            name=op.f("uq_assessment_attempts_owner_id_submission_key"),
        ),
    )
    op.create_index(
        op.f("ix_assessment_attempts_assessment_id"),
        "assessment_attempts",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_attempts_owner_created",
        "assessment_attempts",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_attempts_owner_status",
        "assessment_attempts",
        ["owner_id", "status", "started_at"],
        unique=False,
    )
    op.create_table(
        "assessment_questions",
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("option_order_version", sa.String(length=100), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "position BETWEEN 1 AND 12", name=op.f("ck_assessment_questions_position")
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_assessment_questions_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_id"],
            ["assessments.owner_id", "assessments.id"],
            name=op.f("fk_assessment_questions_owner_id_assessments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_assessment_questions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_assessment_questions_question_version_id_question_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_questions")),
        sa.UniqueConstraint(
            "assessment_id", "position", name=op.f("uq_assessment_questions_assessment_id_position")
        ),
        sa.UniqueConstraint(
            "assessment_id",
            "question_version_id",
            name=op.f("uq_assessment_questions_assessment_id_question_version_id"),
        ),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "assessment_id",
            name=op.f("uq_assessment_questions_owner_id_id_assessment_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_assessment_questions_owner_id_id")),
    )
    op.create_index(
        op.f("ix_assessment_questions_assessment_id"),
        "assessment_questions",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_questions_owner_created",
        "assessment_questions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_questions_question_version_id"),
        "assessment_questions",
        ["question_version_id"],
        unique=False,
    )
    op.create_table(
        "interview_questions",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("project_question_id", sa.Uuid(), nullable=True),
        sa.Column("parent_question_id", sa.Uuid(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "awaiting_answer",
                "submitted",
                "evaluating",
                "evaluated",
                "evaluation_failed",
                "skipped",
                name="turn_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "status IN ('awaiting_answer', 'submitted', 'evaluating', 'evaluat"
                "ed', 'evaluation_failed', 'skipped')"
            ),
            name=op.f("ck_interview_questions_turn_status"),
        ),
        sa.CheckConstraint(
            "parent_question_id IS NULL OR parent_question_id <> id",
            name=op.f("ck_interview_questions_not_self_followup"),
        ),
        sa.CheckConstraint("sequence > 0", name=op.f("ck_interview_questions_sequence")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_interview_questions_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "parent_question_id", "session_id"],
            [
                "interview_questions.owner_id",
                "interview_questions.id",
                "interview_questions.session_id",
            ],
            name=op.f("fk_interview_questions_owner_id_interview_questions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_question_id"],
            ["project_questions.owner_id", "project_questions.id"],
            name=op.f("fk_interview_questions_owner_id_project_questions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "session_id"],
            ["interview_sessions.owner_id", "interview_sessions.id"],
            name=op.f("fk_interview_questions_owner_id_interview_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_interview_questions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            name=op.f("fk_interview_questions_question_version_id_question_versions"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_questions")),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "session_id",
            name=op.f("uq_interview_questions_owner_id_id_session_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_interview_questions_owner_id_id")),
        sa.UniqueConstraint(
            "parent_question_id", name=op.f("uq_interview_questions_parent_question_id")
        ),
        sa.UniqueConstraint(
            "session_id",
            "question_version_id",
            name=op.f("uq_interview_questions_session_id_question_version_id"),
        ),
        sa.UniqueConstraint(
            "session_id", "sequence", name=op.f("uq_interview_questions_session_id_sequence")
        ),
    )
    op.create_index(
        "ix_interview_questions_owner_created",
        "interview_questions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_questions_project_question_id"),
        "interview_questions",
        ["project_question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_questions_question_version_id"),
        "interview_questions",
        ["question_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_questions_session_id"),
        "interview_questions",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "project_facts",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=False),
        sa.Column("fact_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=False),
        sa.Column("line_end", sa.Integer(), nullable=False),
        sa.Column("is_inference", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0", name=op.f("ck_project_facts_description")
        ),
        sa.CheckConstraint(
            "line_start > 0 AND line_end >= line_start", name=op.f("ck_project_facts_line_range")
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_facts_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "analysis_id"],
            ["project_analyses.owner_id", "project_analyses.id"],
            name=op.f("fk_project_facts_owner_id_project_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "source_file_id", "analysis_id"],
            [
                "project_source_files.owner_id",
                "project_source_files.id",
                "project_source_files.analysis_id",
            ],
            name=op.f("fk_project_facts_owner_id_project_source_files"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_facts_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_facts")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_project_facts_owner_id_id")),
    )
    op.create_index(
        op.f("ix_project_facts_analysis_id"), "project_facts", ["analysis_id"], unique=False
    )
    op.create_index(
        "ix_project_facts_owner_created", "project_facts", ["owner_id", "created_at"], unique=False
    )
    op.create_index(
        op.f("ix_project_facts_source_file_id"), "project_facts", ["source_file_id"], unique=False
    )
    op.create_table(
        "project_question_citations",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("project_question_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=False),
        sa.Column("line_end", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "line_start > 0 AND line_end >= line_start",
            name=op.f("ck_project_question_citations_line_range"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_project_question_citations_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "project_question_id", "analysis_id"],
            ["project_questions.owner_id", "project_questions.id", "project_questions.analysis_id"],
            name=op.f("fk_project_question_citations_owner_id_project_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "source_file_id", "analysis_id"],
            [
                "project_source_files.owner_id",
                "project_source_files.id",
                "project_source_files.analysis_id",
            ],
            name=op.f("fk_project_question_citations_owner_id_project_source_files"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_project_question_citations_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_question_citations")),
        sa.UniqueConstraint(
            "owner_id", "id", name=op.f("uq_project_question_citations_owner_id_id")
        ),
        sa.UniqueConstraint(
            "project_question_id",
            "source_file_id",
            "line_start",
            "line_end",
            name=op.f(
                "uq_project_question_citations_project_question_id_source_file_id_"
                "line_start_line_end"
            ),
        ),
    )
    op.create_index(
        op.f("ix_project_question_citations_analysis_id"),
        "project_question_citations",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_question_citations_owner_created",
        "project_question_citations",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_question_citations_project_question_id"),
        "project_question_citations",
        ["project_question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_question_citations_source_file_id"),
        "project_question_citations",
        ["source_file_id"],
        unique=False,
    )
    op.create_table(
        "roadmap_items",
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("resource_url", sa.String(length=2000), nullable=True),
        sa.Column("resource_review_version", sa.String(length=100), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("scheduled_on", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "planned",
                "in_progress",
                "completed",
                "skipped",
                name="roadmap_item_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name=op.f("ck_roadmap_items_completed_timestamp"),
        ),
        sa.CheckConstraint(
            "resource_url IS NULL OR resource_url LIKE 'https://%'",
            name=op.f("ck_roadmap_items_resource_https"),
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'in_progress', 'completed', 'skipped')",
            name=op.f("ck_roadmap_items_roadmap_item_status"),
        ),
        sa.CheckConstraint(
            "position > 0 AND estimated_minutes BETWEEN 1 AND 10080",
            name=op.f("ck_roadmap_items_effort"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_roadmap_items_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "roadmap_id"],
            ["roadmaps.owner_id", "roadmaps.id"],
            name=op.f("fk_roadmap_items_owner_id_roadmaps"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_roadmap_items_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_roadmap_items_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roadmap_items")),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_roadmap_items_owner_id_id")),
        sa.UniqueConstraint(
            "roadmap_id", "position", name=op.f("uq_roadmap_items_roadmap_id_position")
        ),
    )
    op.create_index(
        "ix_roadmap_items_owner_created", "roadmap_items", ["owner_id", "created_at"], unique=False
    )
    op.create_index(
        "ix_roadmap_items_owner_due",
        "roadmap_items",
        ["owner_id", "status", "scheduled_on"],
        unique=False,
    )
    op.create_index(
        op.f("ix_roadmap_items_roadmap_id"), "roadmap_items", ["roadmap_id"], unique=False
    )
    op.create_index(op.f("ix_roadmap_items_skill_id"), "roadmap_items", ["skill_id"], unique=False)
    op.create_table(
        "assessment_question_options",
        sa.Column("assessment_question_id", sa.Uuid(), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), nullable=False),
        sa.Column("option_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("position > 0", name=op.f("ck_assessment_question_options_position")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_assessment_question_options_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_question_id"],
            ["assessment_questions.owner_id", "assessment_questions.id"],
            name=op.f("fk_assessment_question_options_owner_id_assessment_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_assessment_question_options_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_version_id", "option_id"],
            ["question_options.question_version_id", "question_options.id"],
            name=op.f("fk_assessment_question_options_question_version_id_question_options"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_question_options")),
        sa.UniqueConstraint(
            "assessment_question_id",
            "option_id",
            name=op.f("uq_assessment_question_options_assessment_question_id_option_id"),
        ),
        sa.UniqueConstraint(
            "assessment_question_id",
            "position",
            name=op.f("uq_assessment_question_options_assessment_question_id_position"),
        ),
        sa.UniqueConstraint(
            "owner_id", "id", name=op.f("uq_assessment_question_options_owner_id_id")
        ),
    )
    op.create_index(
        op.f("ix_assessment_question_options_assessment_question_id"),
        "assessment_question_options",
        ["assessment_question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_question_options_option_id"),
        "assessment_question_options",
        ["option_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_question_options_owner_created",
        "assessment_question_options",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "interview_answers",
        sa.Column("interview_question_id", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "submitted",
                "skipped",
                name="interview_answer_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("submission_key", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'submitted') = (submitted_at IS NOT NULL)",
            name=op.f("ck_interview_answers_submission_timestamp"),
        ),
        sa.CheckConstraint(
            "status <> 'submitted' OR answer_text IS NOT NULL",
            name=op.f("ck_interview_answers_submitted_answer"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'skipped')",
            name=op.f("ck_interview_answers_interview_answer_status"),
        ),
        sa.CheckConstraint(
            "answer_text IS NULL OR length(answer_text) BETWEEN 1 AND 30000",
            name=op.f("ck_interview_answers_answer_length"),
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_interview_answers_revision")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_interview_answers_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "interview_question_id"],
            ["interview_questions.owner_id", "interview_questions.id"],
            name=op.f("fk_interview_answers_owner_id_interview_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_interview_answers_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_answers")),
        sa.UniqueConstraint(
            "interview_question_id", name=op.f("uq_interview_answers_interview_question_id")
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_interview_answers_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id", "submission_key", name=op.f("uq_interview_answers_owner_id_submission_key")
        ),
    )
    op.create_index(
        op.f("ix_interview_answers_interview_question_id"),
        "interview_answers",
        ["interview_question_id"],
        unique=False,
    )
    op.create_index(
        "ix_interview_answers_owner_created",
        "interview_answers",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "progress_events",
        sa.Column(
            "event_type",
            sa.Enum(
                "assessment_completed",
                "interview_completed",
                "roadmap_item_completed",
                name="progress_event_type",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "result_kind",
            sa.Enum(
                "deterministic",
                "model_assisted",
                "simulation",
                "self_review",
                name="progress_result_kind",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=True,
        ),
        sa.Column("assessment_attempt_id", sa.Uuid(), nullable=True),
        sa.Column("interview_session_id", sa.Uuid(), nullable=True),
        sa.Column("roadmap_item_id", sa.Uuid(), nullable=True),
        sa.Column("deduplication_key", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "(event_type = 'assessment_completed' AND assessment_attempt_id IS"
                " NOT NULL AND interview_session_id IS NULL AND roadmap_item_id IS"
                " NULL) OR (event_type = 'interview_completed' AND interview_sessi"
                "on_id IS NOT NULL AND assessment_attempt_id IS NULL AND roadmap_i"
                "tem_id IS NULL) OR (event_type = 'roadmap_item_completed' AND roa"
                "dmap_item_id IS NOT NULL AND assessment_attempt_id IS NULL AND in"
                "terview_session_id IS NULL)"
            ),
            name=op.f("ck_progress_events_event_origin"),
        ),
        sa.CheckConstraint(
            (
                "details IS NULL OR (jsonb_typeof(details) = 'object' AND octet_le"
                "ngth(details::text) <= 8192)"
            ),
            name=op.f("ck_progress_events_bounded_details"),
        ),
        sa.CheckConstraint(
            (
                "event_type IN ('assessment_completed', 'interview_completed', 'ro"
                "admap_item_completed')"
            ),
            name=op.f("ck_progress_events_progress_event_type"),
        ),
        sa.CheckConstraint(
            ("result_kind IN ('deterministic', 'model_assisted', 'simulation', 'self_review')"),
            name=op.f("ck_progress_events_progress_result_kind"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_progress_events_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_attempt_id"],
            ["assessment_attempts.owner_id", "assessment_attempts.id"],
            name=op.f("fk_progress_events_owner_id_assessment_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "interview_session_id"],
            ["interview_sessions.owner_id", "interview_sessions.id"],
            name=op.f("fk_progress_events_owner_id_interview_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "roadmap_item_id"],
            ["roadmap_items.owner_id", "roadmap_items.id"],
            name=op.f("fk_progress_events_owner_id_roadmap_items"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_progress_events_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_progress_events")),
        sa.UniqueConstraint(
            "owner_id",
            "deduplication_key",
            name=op.f("uq_progress_events_owner_id_deduplication_key"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_progress_events_owner_id_id")),
    )
    op.create_index(
        op.f("ix_progress_events_assessment_attempt_id"),
        "progress_events",
        ["assessment_attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_progress_events_interview_session_id"),
        "progress_events",
        ["interview_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_events_owner_created",
        "progress_events",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_progress_events_owner_occurred",
        "progress_events",
        ["owner_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_progress_events_roadmap_item_id"),
        "progress_events",
        ["roadmap_item_id"],
        unique=False,
    )
    op.create_table(
        "question_attempts",
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_attempt_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_question_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "submitted",
                "skipped",
                name="question_attempt_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("selected_option_id", sa.Uuid(), nullable=True),
        sa.Column("submission_key", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("result_kind", sa.String(length=20), nullable=True),
        sa.Column("grading_version", sa.String(length=100), nullable=True),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'submitted') = (submitted_at IS NOT NULL)",
            name=op.f("ck_question_attempts_submission_timestamp"),
        ),
        sa.CheckConstraint(
            (
                "is_correct IS NULL OR (status = 'submitted' AND result_kind IS NO"
                "T NULL AND grading_version IS NOT NULL)"
            ),
            name=op.f("ck_question_attempts_grading_provenance"),
        ),
        sa.CheckConstraint(
            (
                "result_kind IS NULL OR result_kind IN ('deterministic', 'simulati"
                "on', 'self_review')"
            ),
            name=op.f("ck_question_attempts_result_kind"),
        ),
        sa.CheckConstraint(
            ("status <> 'submitted' OR answer_text IS NOT NULL OR selected_option_id IS NOT NULL"),
            name=op.f("ck_question_attempts_submitted_answer"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'skipped')",
            name=op.f("ck_question_attempts_question_attempt_status"),
        ),
        sa.CheckConstraint(
            "answer_text IS NULL OR length(answer_text) <= 30000",
            name=op.f("ck_question_attempts_answer_length"),
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_question_attempts_revision")),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_question_attempts_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_attempt_id", "assessment_id"],
            [
                "assessment_attempts.owner_id",
                "assessment_attempts.id",
                "assessment_attempts.assessment_id",
            ],
            name=op.f("fk_question_attempts_owner_id_assessment_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "assessment_question_id", "assessment_id"],
            [
                "assessment_questions.owner_id",
                "assessment_questions.id",
                "assessment_questions.assessment_id",
            ],
            name=op.f("fk_question_attempts_owner_id_assessment_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_question_attempts_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["selected_option_id"],
            ["question_options.id"],
            name=op.f("fk_question_attempts_selected_option_id_question_options"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_attempts")),
        sa.UniqueConstraint(
            "assessment_attempt_id",
            "assessment_question_id",
            name=op.f("uq_question_attempts_assessment_attempt_id_assessment_question_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_question_attempts_owner_id_id")),
        sa.UniqueConstraint(
            "owner_id", "submission_key", name=op.f("uq_question_attempts_owner_id_submission_key")
        ),
    )
    op.create_index(
        op.f("ix_question_attempts_assessment_attempt_id"),
        "question_attempts",
        ["assessment_attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_attempts_assessment_id"),
        "question_attempts",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_attempts_assessment_question_id"),
        "question_attempts",
        ["assessment_question_id"],
        unique=False,
    )
    op.create_index(
        "ix_question_attempts_owner_created",
        "question_attempts",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_attempts_selected_option_id"),
        "question_attempts",
        ["selected_option_id"],
        unique=False,
    )
    op.create_table(
        "answer_evaluations",
        sa.Column("interview_answer_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes_id", sa.Uuid(), nullable=True),
        sa.Column(
            "kind",
            sa.Enum(
                "deterministic",
                "model_assisted",
                "simulation",
                "self_review",
                name="evaluation_kind",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                "not_evaluable",
                name="evaluation_status",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("evaluator_version", sa.String(length=100), nullable=False),
        sa.Column("rubric_version", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("prompt_version", sa.String(length=100), nullable=True),
        sa.Column("schema_version", sa.String(length=100), nullable=True),
        sa.Column("input_digest", sa.String(length=64), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2, asdecimal=False), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("usage_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "input_digest IS NULL OR input_digest ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_answer_evaluations_input_digest"),
        ),
        sa.CheckConstraint(
            "kind <> 'model_assisted' OR (provider IS NOT NULL AND model IS NOT NULL)",
            name=op.f("ck_answer_evaluations_model_provenance"),
        ),
        sa.CheckConstraint(
            "kind IN ('deterministic', 'model_assisted', 'simulation', 'self_review')",
            name=op.f("ck_answer_evaluations_evaluation_kind"),
        ),
        sa.CheckConstraint(
            "status = 'completed' OR score IS NULL",
            name=op.f("ck_answer_evaluations_score_availability"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'not_evaluable')",
            name=op.f("ck_answer_evaluations_evaluation_status"),
        ),
        sa.CheckConstraint(
            (
                "usage_metadata IS NULL OR (jsonb_typeof(usage_metadata) = 'object"
                "' AND octet_length(usage_metadata::text) <= 8192)"
            ),
            name=op.f("ck_answer_evaluations_bounded_usage"),
        ),
        sa.CheckConstraint(
            "score IS NULL OR score BETWEEN 0 AND 100",
            name=op.f("ck_answer_evaluations_score_range"),
        ),
        sa.CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id",
            name=op.f("ck_answer_evaluations_not_self_supersedes"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_answer_evaluations_timestamp_order")
        ),
        sa.CheckConstraint("version > 0", name=op.f("ck_answer_evaluations_version")),
        sa.ForeignKeyConstraint(
            ["owner_id", "interview_answer_id"],
            ["interview_answers.owner_id", "interview_answers.id"],
            name=op.f("fk_answer_evaluations_owner_id_interview_answers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "supersedes_id", "interview_answer_id"],
            [
                "answer_evaluations.owner_id",
                "answer_evaluations.id",
                "answer_evaluations.interview_answer_id",
            ],
            name=op.f("fk_answer_evaluations_owner_id_answer_evaluations"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_answer_evaluations_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answer_evaluations")),
        sa.UniqueConstraint(
            "interview_answer_id",
            "version",
            name=op.f("uq_answer_evaluations_interview_answer_id_version"),
        ),
        sa.UniqueConstraint(
            "owner_id",
            "id",
            "interview_answer_id",
            name=op.f("uq_answer_evaluations_owner_id_id_interview_answer_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_answer_evaluations_owner_id_id")),
    )
    op.create_index(
        op.f("ix_answer_evaluations_interview_answer_id"),
        "answer_evaluations",
        ["interview_answer_id"],
        unique=False,
    )
    op.create_index(
        "ix_answer_evaluations_owner_created",
        "answer_evaluations",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_answer_evaluations_supersedes_id"),
        "answer_evaluations",
        ["supersedes_id"],
        unique=False,
    )
    op.create_table(
        "evaluation_dimensions",
        sa.Column("evaluation_id", sa.Uuid(), nullable=False),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("not_evaluable", sa.Boolean(), nullable=False),
        sa.Column("feedback", sa.String(length=4000), nullable=False),
        sa.Column("answer_start", sa.Integer(), nullable=True),
        sa.Column("answer_end", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "(answer_start IS NULL AND answer_end IS NULL) OR (answer_start IS"
                " NOT NULL AND answer_end IS NOT NULL AND answer_start >= 0 AND an"
                "swer_end > answer_start)"
            ),
            name=op.f("ck_evaluation_dimensions_answer_span"),
        ),
        sa.CheckConstraint(
            ("(not_evaluable AND score IS NULL) OR (NOT not_evaluable AND score IS NOT NULL)"),
            name=op.f("ck_evaluation_dimensions_evaluable_score"),
        ),
        sa.CheckConstraint(
            "score IS NULL OR score BETWEEN 0 AND 4",
            name=op.f("ck_evaluation_dimensions_score_range"),
        ),
        sa.CheckConstraint(
            "updated_at >= created_at", name=op.f("ck_evaluation_dimensions_timestamp_order")
        ),
        sa.ForeignKeyConstraint(
            ["criterion_id"],
            ["question_rubric_criteria.id"],
            name=op.f("fk_evaluation_dimensions_criterion_id_question_rubric_criteria"),
            ondelete="NO ACTION",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "evaluation_id"],
            ["answer_evaluations.owner_id", "answer_evaluations.id"],
            name=op.f("fk_evaluation_dimensions_owner_id_answer_evaluations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["principals.id"],
            name=op.f("fk_evaluation_dimensions_owner_id_principals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_dimensions")),
        sa.UniqueConstraint(
            "evaluation_id",
            "criterion_id",
            name=op.f("uq_evaluation_dimensions_evaluation_id_criterion_id"),
        ),
        sa.UniqueConstraint("owner_id", "id", name=op.f("uq_evaluation_dimensions_owner_id_id")),
    )
    op.create_index(
        op.f("ix_evaluation_dimensions_criterion_id"),
        "evaluation_dimensions",
        ["criterion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_dimensions_evaluation_id"),
        "evaluation_dimensions",
        ["evaluation_id"],
        unique=False,
    )
    op.create_index(
        "ix_evaluation_dimensions_owner_created",
        "evaluation_dimensions",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.execute(
        sa.text(
            "INSERT INTO principals (id, kind, status, created_at, updated_at,"
            " expires_at) SELECT id, 'demo', 'active', created_at, created_at,"
            " expires_at FROM demo_workspaces"
        )
    )
    op.create_foreign_key(
        op.f("fk_demo_workspaces_id_principals"),
        "demo_workspaces",
        "principals",
        ["id"],
        ["id"],
        ondelete="CASCADE",
    )
    install_guards()


def downgrade() -> None:
    guard_empty_domain()
    op.execute(sa.text("DROP TRIGGER relational_demo ON demo_workspaces"))
    # Reviewed explicit schema; no runtime ORM imports.
    op.drop_constraint(
        op.f("fk_demo_workspaces_id_principals"), "demo_workspaces", type_="foreignkey"
    )
    op.drop_index("ix_evaluation_dimensions_owner_created", table_name="evaluation_dimensions")
    op.drop_index(
        op.f("ix_evaluation_dimensions_evaluation_id"), table_name="evaluation_dimensions"
    )
    op.drop_index(op.f("ix_evaluation_dimensions_criterion_id"), table_name="evaluation_dimensions")
    op.drop_table("evaluation_dimensions")
    op.drop_index(op.f("ix_answer_evaluations_supersedes_id"), table_name="answer_evaluations")
    op.drop_index("ix_answer_evaluations_owner_created", table_name="answer_evaluations")
    op.drop_index(
        op.f("ix_answer_evaluations_interview_answer_id"), table_name="answer_evaluations"
    )
    op.drop_table("answer_evaluations")
    op.drop_index(op.f("ix_question_attempts_selected_option_id"), table_name="question_attempts")
    op.drop_index("ix_question_attempts_owner_created", table_name="question_attempts")
    op.drop_index(
        op.f("ix_question_attempts_assessment_question_id"), table_name="question_attempts"
    )
    op.drop_index(op.f("ix_question_attempts_assessment_id"), table_name="question_attempts")
    op.drop_index(
        op.f("ix_question_attempts_assessment_attempt_id"), table_name="question_attempts"
    )
    op.drop_table("question_attempts")
    op.drop_index(op.f("ix_progress_events_roadmap_item_id"), table_name="progress_events")
    op.drop_index("ix_progress_events_owner_occurred", table_name="progress_events")
    op.drop_index("ix_progress_events_owner_created", table_name="progress_events")
    op.drop_index(op.f("ix_progress_events_interview_session_id"), table_name="progress_events")
    op.drop_index(op.f("ix_progress_events_assessment_attempt_id"), table_name="progress_events")
    op.drop_table("progress_events")
    op.drop_index("ix_interview_answers_owner_created", table_name="interview_answers")
    op.drop_index(
        op.f("ix_interview_answers_interview_question_id"), table_name="interview_answers"
    )
    op.drop_table("interview_answers")
    op.drop_index(
        "ix_assessment_question_options_owner_created", table_name="assessment_question_options"
    )
    op.drop_index(
        op.f("ix_assessment_question_options_option_id"), table_name="assessment_question_options"
    )
    op.drop_index(
        op.f("ix_assessment_question_options_assessment_question_id"),
        table_name="assessment_question_options",
    )
    op.drop_table("assessment_question_options")
    op.drop_index(op.f("ix_roadmap_items_skill_id"), table_name="roadmap_items")
    op.drop_index(op.f("ix_roadmap_items_roadmap_id"), table_name="roadmap_items")
    op.drop_index("ix_roadmap_items_owner_due", table_name="roadmap_items")
    op.drop_index("ix_roadmap_items_owner_created", table_name="roadmap_items")
    op.drop_table("roadmap_items")
    op.drop_index(
        op.f("ix_project_question_citations_source_file_id"),
        table_name="project_question_citations",
    )
    op.drop_index(
        op.f("ix_project_question_citations_project_question_id"),
        table_name="project_question_citations",
    )
    op.drop_index(
        "ix_project_question_citations_owner_created", table_name="project_question_citations"
    )
    op.drop_index(
        op.f("ix_project_question_citations_analysis_id"), table_name="project_question_citations"
    )
    op.drop_table("project_question_citations")
    op.drop_index(op.f("ix_project_facts_source_file_id"), table_name="project_facts")
    op.drop_index("ix_project_facts_owner_created", table_name="project_facts")
    op.drop_index(op.f("ix_project_facts_analysis_id"), table_name="project_facts")
    op.drop_table("project_facts")
    op.drop_index(op.f("ix_interview_questions_session_id"), table_name="interview_questions")
    op.drop_index(
        op.f("ix_interview_questions_question_version_id"), table_name="interview_questions"
    )
    op.drop_index(
        op.f("ix_interview_questions_project_question_id"), table_name="interview_questions"
    )
    op.drop_index("ix_interview_questions_owner_created", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index(
        op.f("ix_assessment_questions_question_version_id"), table_name="assessment_questions"
    )
    op.drop_index("ix_assessment_questions_owner_created", table_name="assessment_questions")
    op.drop_index(op.f("ix_assessment_questions_assessment_id"), table_name="assessment_questions")
    op.drop_table("assessment_questions")
    op.drop_index("ix_assessment_attempts_owner_status", table_name="assessment_attempts")
    op.drop_index("ix_assessment_attempts_owner_created", table_name="assessment_attempts")
    op.drop_index(op.f("ix_assessment_attempts_assessment_id"), table_name="assessment_attempts")
    op.drop_table("assessment_attempts")
    op.drop_index(op.f("ix_short_answer_keys_question_version_id"), table_name="short_answer_keys")
    op.drop_table("short_answer_keys")
    op.drop_index(op.f("ix_roadmaps_target_job_version_id"), table_name="roadmaps")
    op.drop_index("ix_roadmaps_owner_status", table_name="roadmaps")
    op.drop_index("ix_roadmaps_owner_created", table_name="roadmaps")
    op.drop_table("roadmaps")
    op.drop_index(op.f("ix_resume_skill_evidence_skill_id"), table_name="resume_skill_evidence")
    op.drop_index(
        op.f("ix_resume_skill_evidence_resume_version_id"), table_name="resume_skill_evidence"
    )
    op.drop_index("ix_resume_skill_evidence_owner_created", table_name="resume_skill_evidence")
    op.drop_table("resume_skill_evidence")
    op.drop_index(op.f("ix_question_skills_skill_id"), table_name="question_skills")
    op.drop_index(op.f("ix_question_skills_question_version_id"), table_name="question_skills")
    op.drop_table("question_skills")
    op.drop_index(
        op.f("ix_question_rubric_criteria_question_version_id"),
        table_name="question_rubric_criteria",
    )
    op.drop_table("question_rubric_criteria")
    op.drop_index(op.f("ix_question_options_question_version_id"), table_name="question_options")
    op.drop_table("question_options")
    op.drop_index("ix_project_source_files_owner_created", table_name="project_source_files")
    op.drop_index(op.f("ix_project_source_files_analysis_id"), table_name="project_source_files")
    op.drop_table("project_source_files")
    op.drop_index(op.f("ix_project_questions_question_version_id"), table_name="project_questions")
    op.drop_index("ix_project_questions_owner_created", table_name="project_questions")
    op.drop_index(op.f("ix_project_questions_analysis_id"), table_name="project_questions")
    op.drop_table("project_questions")
    op.drop_index(
        op.f("ix_job_skill_requirements_target_job_version_id"), table_name="job_skill_requirements"
    )
    op.drop_index(op.f("ix_job_skill_requirements_skill_id"), table_name="job_skill_requirements")
    op.drop_index("ix_job_skill_requirements_owner_created", table_name="job_skill_requirements")
    op.drop_table("job_skill_requirements")
    op.drop_index(
        op.f("ix_interview_sessions_target_job_version_id"), table_name="interview_sessions"
    )
    op.drop_index(op.f("ix_interview_sessions_resume_version_id"), table_name="interview_sessions")
    op.drop_index(
        op.f("ix_interview_sessions_project_analysis_id"), table_name="interview_sessions"
    )
    op.drop_index("ix_interview_sessions_owner_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_owner_created", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index(op.f("ix_bookmarks_question_version_id"), table_name="bookmarks")
    op.drop_index("ix_bookmarks_owner_created", table_name="bookmarks")
    op.drop_table("bookmarks")
    op.drop_index(op.f("ix_assessments_target_job_version_id"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_resume_version_id"), table_name="assessments")
    op.drop_index("ix_assessments_owner_status", table_name="assessments")
    op.drop_index("ix_assessments_owner_created", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index(op.f("ix_resume_versions_upload_expires_at"), table_name="resume_versions")
    op.drop_index(op.f("ix_resume_versions_resume_id"), table_name="resume_versions")
    op.drop_index("ix_resume_versions_owner_created", table_name="resume_versions")
    op.drop_table("resume_versions")
    op.drop_index(op.f("ix_question_versions_status"), table_name="question_versions")
    op.drop_index(op.f("ix_question_versions_question_id"), table_name="question_versions")
    op.drop_table("question_versions")
    op.drop_index(op.f("ix_project_analyses_upload_expires_at"), table_name="project_analyses")
    op.drop_index(op.f("ix_project_analyses_repository_id"), table_name="project_analyses")
    op.drop_index("ix_project_analyses_owner_created", table_name="project_analyses")
    op.drop_table("project_analyses")
    op.drop_index(op.f("ix_job_target_versions_target_job_id"), table_name="job_target_versions")
    op.drop_index("ix_job_target_versions_owner_created", table_name="job_target_versions")
    op.drop_table("job_target_versions")
    op.drop_index(op.f("ix_skill_aliases_skill_id"), table_name="skill_aliases")
    op.drop_table("skill_aliases")
    op.drop_index("ix_resumes_owner_created", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index(op.f("ix_questions_owner_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_canonical_concept"), table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_project_repositories_owner_created", table_name="project_repositories")
    op.drop_table("project_repositories")
    op.drop_index("ix_job_targets_owner_created", table_name="job_targets")
    op.drop_table("job_targets")
    op.drop_index("ix_candidate_profiles_owner_created", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
    op.drop_table("skills")
    op.drop_index(op.f("ix_principals_expires_at"), table_name="principals")
    op.drop_table("principals")

    for function in [
        "relational_touch",
        "relational_curriculum_child",
        "relational_demo_principal",
        "relational_frozen_assessment",
        *GUARDS,
    ]:
        op.execute(sa.text(f"DROP FUNCTION {function}()"))


DOMAIN_TABLES = [
    "principals",
    "skills",
    "candidate_profiles",
    "job_targets",
    "project_repositories",
    "questions",
    "resumes",
    "skill_aliases",
    "job_target_versions",
    "project_analyses",
    "question_versions",
    "resume_versions",
    "assessments",
    "bookmarks",
    "interview_sessions",
    "job_skill_requirements",
    "project_questions",
    "project_source_files",
    "question_options",
    "question_rubric_criteria",
    "question_skills",
    "resume_skill_evidence",
    "roadmaps",
    "short_answer_keys",
    "assessment_attempts",
    "assessment_questions",
    "interview_questions",
    "project_facts",
    "project_question_citations",
    "roadmap_items",
    "assessment_question_options",
    "interview_answers",
    "progress_events",
    "question_attempts",
    "answer_evaluations",
    "evaluation_dimensions",
]


GUARDS = {
    "relational_principal_identity": ["principals"],
    "relational_context_version": ["job_target_versions", "resume_versions", "project_analyses"],
    "relational_assessment_context": ["assessments"],
    "relational_job_source_span": ["job_skill_requirements"],
    "relational_publication": ["question_versions"],
    "relational_attempt_parent": ["assessment_attempts"],
    "relational_question_access": [
        "bookmarks",
        "assessment_questions",
        "interview_questions",
        "project_questions",
    ],
    "relational_question_immutable": ["question_versions"],
    "relational_question_identity": ["questions"],
    "relational_final_answer": ["question_attempts", "interview_answers"],
    "relational_assessment_option": ["assessment_question_options"],
    "relational_selected_option": ["question_attempts"],
    "relational_project_reference": ["project_facts", "project_question_citations"],
    "relational_project_turn": ["interview_questions"],
    "relational_evaluation_dimension": ["evaluation_dimensions"],
    "relational_terminal_evaluation": ["answer_evaluations"],
    "relational_progress_fact": ["progress_events"],
}


def install_guards() -> None:
    sql = (Path(__file__).resolve().parents[1] / "relational_guards.sql").read_text()
    for statement in sql.split("-- statement-break"):
        op.execute(sa.text(statement))
    for table in DOMAIN_TABLES:
        op.execute(
            sa.text(
                f"CREATE TRIGGER a_relational_touch BEFORE UPDATE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION relational_touch()"
            )
        )
    for function, tables in GUARDS.items():
        events = (
            "UPDATE"
            if function
            in {
                "relational_question_immutable",
                "relational_question_identity",
                "relational_final_answer",
                "relational_principal_identity",
                "relational_context_version",
                "relational_assessment_context",
            }
            else "INSERT OR UPDATE OR DELETE"
            if function == "relational_evaluation_dimension"
            else "INSERT OR UPDATE"
        )
        for table in tables:
            op.execute(
                sa.text(
                    f"CREATE TRIGGER {function} BEFORE {events} ON {table} "
                    f"FOR EACH ROW EXECUTE FUNCTION {function}()"
                )
            )
    for table in [
        "question_skills",
        "question_options",
        "short_answer_keys",
        "question_rubric_criteria",
    ]:
        op.execute(
            sa.text(
                "CREATE TRIGGER relational_curriculum_child BEFORE INSERT OR UPDATE "
                f"OR DELETE ON {table} FOR EACH ROW "
                "EXECUTE FUNCTION relational_curriculum_child()"
            )
        )
    op.execute(
        sa.text(
            "CREATE TRIGGER relational_frozen_assessment BEFORE INSERT OR UPDA"
            "TE OR DELETE ON assessment_questions FOR EACH ROW EXECUTE FUNCTIO"
            "N relational_frozen_assessment()"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER relational_demo BEFORE INSERT OR UPDATE ON demo_wo"
            "rkspaces FOR EACH ROW EXECUTE FUNCTION relational_demo_principal("
            ")"
        )
    )


def guard_empty_domain() -> None:
    # Refuse silent data loss. There is no force flag: review backup/erasure first.
    for table in DOMAIN_TABLES:
        predicate = (
            (
                "WHERE kind <> 'demo' OR NOT EXISTS (SELECT 1 FROM demo_workspaces"
                " d WHERE d.id = principals.id)"
            )
            if table == "principals"
            else ""
        )
        op.execute(
            sa.text(
                f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM {table} {predicate}) THEN "
                "RAISE EXCEPTION 'Unsafe downgrade: domain data exists'; END IF; END $$"
            )
        )
