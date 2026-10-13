"""Optional candidate context and editable target job metadata.

Revision ID: 0003_candidate_context
Revises: 0002_relational_model
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0003_candidate_context"
down_revision: str | None = "0002_relational_model"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("education", sa.String(300), nullable=True))
    op.add_column("candidate_profiles", sa.Column("graduation_year", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "education",
        "candidate_profiles",
        "education IS NULL OR length(trim(education)) BETWEEN 1 AND 300",
    )
    op.create_check_constraint(
        "graduation_year",
        "candidate_profiles",
        "graduation_year IS NULL OR graduation_year BETWEEN 1900 AND 2100",
    )
    op.create_table(
        "profile_interests",
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
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["principals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["owner_id", "profile_id"],
            ["candidate_profiles.owner_id", "candidate_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("owner_id", "id"),
        sa.UniqueConstraint("owner_id", "profile_id", "position"),
        sa.UniqueConstraint("owner_id", "profile_id", "label"),
        sa.CheckConstraint("updated_at >= created_at", name="timestamp_order"),
        sa.CheckConstraint("position BETWEEN 0 AND 19", name="position"),
        sa.CheckConstraint("length(trim(label)) BETWEEN 1 AND 80", name="label"),
    )
    op.create_index(
        "ix_profile_interests_owner_created", "profile_interests", ["owner_id", "created_at"]
    )
    op.create_index("ix_profile_interests_profile_id", "profile_interests", ["profile_id"])
    for column in [
        sa.Column("source_url", sa.String(2000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(6), server_default="normal", nullable=False),
        sa.Column("status", sa.String(12), server_default="saved", nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
    ]:
        op.add_column("job_targets", column)
    for name, expression in {
        "target_priority": "priority IN ('low', 'normal', 'high')",
        "target_status": "status IN ('saved', 'applied', 'interviewing', 'archived')",
        "revision": "revision > 0",
        "notes_length": "notes IS NULL OR length(notes) <= 5000",
        "source_url_length": "source_url IS NULL OR length(source_url) <= 2000",
    }.items():
        op.create_check_constraint(name, "job_targets", expression)


def downgrade() -> None:
    # Preserve supplied personal/job context rather than silently discard it.
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM profile_interests)
        OR EXISTS (SELECT 1 FROM candidate_profiles
          WHERE education IS NOT NULL OR graduation_year IS NOT NULL)
        OR EXISTS (SELECT 1 FROM job_targets
          WHERE source_url IS NOT NULL OR notes IS NOT NULL
          OR priority <> 'normal' OR status <> 'saved' OR revision <> 1)
      THEN RAISE EXCEPTION 'Unsafe downgrade: candidate context data exists'; END IF;
    END $$""")
    op.drop_table("profile_interests")
    for name in ("education", "graduation_year"):
        op.drop_constraint(
            op.f(f"ck_candidate_profiles_{name}"), "candidate_profiles", type_="check"
        )
        op.drop_column("candidate_profiles", name)
    for name in (
        "target_priority",
        "target_status",
        "revision",
        "notes_length",
        "source_url_length",
    ):
        op.drop_constraint(op.f(f"ck_job_targets_{name}"), "job_targets", type_="check")
    for name in ("source_url", "notes", "priority", "status", "revision"):
        op.drop_column("job_targets", name)
