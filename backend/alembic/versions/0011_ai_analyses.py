"""Owned cached resume/Project Defense feedback; no existing rows changed."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011_ai_analyses"
down_revision: str | Sequence[str] | None = "0010_security_budgets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_analysis_receipts",
        sa.Column("owner_id", sa.Uuid(), primary_key=True),
        sa.Column("input_key", sa.String(64), primary_key=True),
        sa.Column("dispatch_token", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("defense_answer_id", sa.Uuid(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["principals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["owner_id", "resume_id"], ["resumes.owner_id", "resumes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "defense_answer_id"],
            ["project_defense_answers.owner_id", "project_defense_answers.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("num_nonnulls(resume_id, defense_answer_id) = 1", name="one_source"),
        sa.CheckConstraint("attempts BETWEEN 1 AND 2", name="attempt_limit"),
        sa.CheckConstraint("state IN ('started', 'failed', 'completed')", name="state"),
        sa.CheckConstraint("(state = 'completed') = (result IS NOT NULL)", name="completed_result"),
        sa.CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 131072", name="result_size"
        ),
    )
    op.create_index("ix_ai_analysis_receipts_expires_at", "ai_analysis_receipts", ["expires_at"])


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM ai_analysis_receipts)")):
        raise RuntimeError("Unsafe downgrade: saved AI analyses exist; preserve them first.")
    op.drop_table("ai_analysis_receipts")
