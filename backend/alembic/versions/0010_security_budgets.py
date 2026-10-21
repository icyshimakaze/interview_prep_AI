"""Durable operation budgets and bounded private evaluation receipts.

Revision ID: 0010_security_budgets
Revises: 0009_personal_roadmaps
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010_security_budgets"
down_revision: str | Sequence[str] | None = "0009_personal_roadmaps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "operation_quotas",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("count > 0", name="positive_count"),
    )
    op.create_index("ix_operation_quotas_expires_at", "operation_quotas", ["expires_at"])
    op.create_table(
        "assessment_evaluation_receipts",
        sa.Column(
            "owner_id",
            sa.Uuid(),
            sa.ForeignKey("principals.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("input_key", sa.String(64), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts BETWEEN 1 AND 2", name="attempt_limit"),
        sa.CheckConstraint("state IN ('started', 'failed', 'completed')", name="state"),
        sa.CheckConstraint("(state = 'completed') = (result IS NOT NULL)", name="completed_result"),
        sa.CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 20000", name="result_size"
        ),
    )
    op.create_index(
        "ix_assessment_evaluation_receipts_expires_at",
        "assessment_evaluation_receipts",
        ["expires_at"],
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM operation_quotas WHERE expires_at > now()) "
            "OR EXISTS (SELECT 1 FROM assessment_evaluation_receipts WHERE expires_at > now())"
        )
    ):
        raise RuntimeError("Unsafe downgrade: live security budgets or evaluation receipts exist.")
    op.drop_table("assessment_evaluation_receipts")
    op.drop_table("operation_quotas")
