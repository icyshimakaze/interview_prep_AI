"""Editable, categorized resume evidence; preserve existing source claims.

Revision ID: 0004_resume_evidence
Revises: 0003_candidate_context
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0004_resume_evidence"
down_revision: str | None = "0003_candidate_context"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "resumes", sa.Column("revision", sa.Integer(), server_default="1", nullable=False)
    )
    op.create_check_constraint("revision", "resumes", "revision > 0")
    op.add_column("resume_versions", sa.Column("extraction_note", sa.String(100), nullable=True))
    op.add_column(
        "resume_skill_evidence",
        sa.Column("category", sa.String(10), server_default="other", nullable=False),
    )
    op.add_column(
        "resume_skill_evidence",
        sa.Column("origin", sa.String(6), server_default="resume", nullable=False),
    )
    for name in ("source_span", "claim_and_excerpt"):
        op.drop_constraint(op.f(f"ck_resume_skill_evidence_{name}"), "resume_skill_evidence")
    for column, kind in [
        ("source_excerpt", sa.String(2000)),
        ("source_start", sa.Integer()),
        ("source_end", sa.Integer()),
    ]:
        op.alter_column("resume_skill_evidence", column, existing_type=kind, nullable=True)
    for name, expression in {
        "evidence_category": "category IN ('language','framework','database','tool',"
        "'project','education','experience','other')",
        "evidence_origin": "origin IN ('resume','user')",
        "claim_and_excerpt": "length(trim(claim)) > 0",
        "source_span": "(origin = 'resume' AND source_start IS NOT NULL AND source_end IS NOT NULL "
        "AND source_start >= 0 AND source_end > source_start "
        "AND source_excerpt IS NOT NULL AND length(trim(source_excerpt)) > 0) OR "
        "(origin = 'user' AND source_start IS NULL AND source_end IS NULL "
        "AND source_excerpt IS NULL AND source_page IS NULL)",
    }.items():
        op.create_check_constraint(name, "resume_skill_evidence", expression)


def downgrade() -> None:
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM resumes WHERE revision <> 1)
        OR EXISTS (SELECT 1 FROM resume_versions WHERE extraction_note IS NOT NULL)
        OR EXISTS (SELECT 1 FROM resume_skill_evidence
          WHERE category <> 'other' OR origin <> 'resume')
      THEN RAISE EXCEPTION 'Unsafe downgrade: reviewed resume evidence exists'; END IF;
    END $$""")
    for name in ("source_span", "claim_and_excerpt", "evidence_category", "evidence_origin"):
        op.drop_constraint(op.f(f"ck_resume_skill_evidence_{name}"), "resume_skill_evidence")
    for column, kind in [
        ("source_excerpt", sa.String(2000)),
        ("source_start", sa.Integer()),
        ("source_end", sa.Integer()),
    ]:
        op.alter_column("resume_skill_evidence", column, existing_type=kind, nullable=False)
    op.create_check_constraint(
        "source_span", "resume_skill_evidence", "source_start >= 0 AND source_end > source_start"
    )
    op.create_check_constraint(
        "claim_and_excerpt",
        "resume_skill_evidence",
        "length(trim(claim)) > 0 AND length(trim(source_excerpt)) > 0",
    )
    op.drop_column("resume_skill_evidence", "origin")
    op.drop_column("resume_skill_evidence", "category")
    op.drop_column("resume_versions", "extraction_note")
    op.drop_constraint(op.f("ck_resumes_revision"), "resumes")
    op.drop_column("resumes", "revision")
