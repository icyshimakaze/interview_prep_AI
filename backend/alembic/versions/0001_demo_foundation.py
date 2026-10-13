"""Create isolated expiring demo workspaces and hashed credentials.

Revision ID: 0001_demo_foundation
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_demo_foundation"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="ck_demo_workspaces_valid_expiry"),
        sa.PrimaryKeyConstraint("id", name="pk_demo_workspaces"),
    )
    op.create_index("ix_demo_workspaces_expires_at", "demo_workspaces", ["expires_at"])
    op.create_table(
        "demo_sessions",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("length(token_hash) = 64", name="ck_demo_sessions_token_hash_length"),
        sa.CheckConstraint("length(csrf_hash) = 64", name="ck_demo_sessions_csrf_hash_length"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["demo_workspaces.id"],
            name="fk_demo_sessions_workspace_id_demo_workspaces",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token_hash", name="pk_demo_sessions"),
        sa.UniqueConstraint("workspace_id", name="uq_demo_sessions_workspace_id"),
    )
    op.create_table(
        "demo_creation_limits",
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("count BETWEEN 1 AND 2", name="ck_demo_creation_limits_creation_quota"),
        sa.PrimaryKeyConstraint("key_hash", "window_start", name="pk_demo_creation_limits"),
    )
    op.create_index("ix_demo_creation_limits_expires_at", "demo_creation_limits", ["expires_at"])


def downgrade() -> None:
    op.drop_table("demo_creation_limits")
    op.drop_table("demo_sessions")
    op.drop_table("demo_workspaces")
