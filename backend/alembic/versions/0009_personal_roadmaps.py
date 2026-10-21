"""Preserved personalized roadmap generations and item rationale.

Revision ID: 0009_personal_roadmaps
Revises: 0008_project_defense
"""

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_personal_roadmaps"
down_revision: str | Sequence[str] | None = "0008_project_defense"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("roadmaps", sa.Column("generation_key", sa.Uuid(), nullable=True))
    op.add_column("roadmaps", sa.Column("input_snapshot", postgresql.JSONB(), nullable=True))
    op.add_column("roadmap_items", sa.Column("recommendation", postgresql.JSONB(), nullable=True))
    op.create_unique_constraint(
        "uq_roadmaps_owner_id_generation_key", "roadmaps", ["owner_id", "generation_key"]
    )
    op.create_index(
        "uq_generated_active_roadmap",
        "roadmaps",
        ["owner_id"],
        unique=True,
        postgresql_where=sa.text("generation_key IS NOT NULL AND status = 'active'"),
    )
    op.create_check_constraint(
        "input_size",
        "roadmaps",
        "input_snapshot IS NULL OR octet_length(input_snapshot::text) <= 32768",
    )
    op.create_check_constraint(
        "recommendation_size",
        "roadmap_items",
        "recommendation IS NULL OR octet_length(recommendation::text) <= 8192",
    )
    sql = (Path(__file__).parents[1] / "roadmap_guards_v1.sql").read_text(encoding="utf-8")
    for statement in sql.split("-- statement-break"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM roadmaps WHERE generation_key IS NOT NULL "
            "OR input_snapshot IS NOT NULL) OR EXISTS "
            "(SELECT 1 FROM roadmap_items WHERE recommendation IS NOT NULL)"
        )
    ):
        raise RuntimeError("Unsafe downgrade: personalized roadmap history would be lost.")
    op.execute("DROP TRIGGER personal_roadmap_guard ON roadmaps")
    op.execute("DROP TRIGGER personal_roadmap_item_guard ON roadmap_items")
    op.execute("DROP FUNCTION personal_roadmap_guard()")
    op.execute("DROP FUNCTION personal_roadmap_item_guard()")
    op.drop_index("uq_generated_active_roadmap", table_name="roadmaps")
    op.drop_constraint("uq_roadmaps_owner_id_generation_key", "roadmaps", type_="unique")
    op.drop_constraint(op.f("ck_roadmaps_input_size"), "roadmaps")
    op.drop_constraint(op.f("ck_roadmap_items_recommendation_size"), "roadmap_items")
    op.drop_column("roadmap_items", "recommendation")
    op.drop_column("roadmaps", "input_snapshot")
    op.drop_column("roadmaps", "generation_key")
