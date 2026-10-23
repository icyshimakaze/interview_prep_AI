"""Add owned immutable context sources to cached opt-in AI reviews."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_ai_context_reviews"
down_revision: str | Sequence[str] | None = "0011_ai_analyses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCES = {
    "target_version_id": "job_target_versions",
    "roadmap_id": "roadmaps",
    "project_analysis_id": "project_analyses",
}


def upgrade() -> None:
    for column, parent in SOURCES.items():
        op.add_column("ai_analysis_receipts", sa.Column(column, sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"fk_ai_analysis_receipts_owner_id_{parent}",
            "ai_analysis_receipts",
            parent,
            ["owner_id", column],
            ["owner_id", "id"],
            ondelete="CASCADE",
        )
    op.drop_constraint("ck_ai_analysis_receipts_one_source", "ai_analysis_receipts")
    op.create_check_constraint(
        "one_source",
        "ai_analysis_receipts",
        "num_nonnulls(resume_id, defense_answer_id, target_version_id, "
        "roadmap_id, project_analysis_id) = 1",
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM ai_analysis_receipts WHERE "
            "target_version_id IS NOT NULL OR roadmap_id IS NOT NULL "
            "OR project_analysis_id IS NOT NULL)"
        )
    ):
        raise RuntimeError("Unsafe downgrade: context reviews exist; preserve them first.")
    op.drop_constraint("ck_ai_analysis_receipts_one_source", "ai_analysis_receipts")
    op.create_check_constraint(
        "one_source", "ai_analysis_receipts", "num_nonnulls(resume_id, defense_answer_id) = 1"
    )
    for column, parent in reversed(list(SOURCES.items())):
        op.drop_constraint(
            f"fk_ai_analysis_receipts_owner_id_{parent}",
            "ai_analysis_receipts",
            type_="foreignkey",
        )
        op.drop_column("ai_analysis_receipts", column)
