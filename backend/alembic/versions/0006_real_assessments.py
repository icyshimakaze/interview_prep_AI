"""Persist real assessment responses and evaluation provenance without rewriting history."""

from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_real_assessments"
down_revision: str | None = "0005_question_bank"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_question_versions_question_type"), "question_versions")
    op.create_check_constraint(
        "question_type",
        "question_versions",
        "question_type IN ('multiple_choice','multiple_select','short_answer',"
        "'written','design','behavioral')",
    )
    op.add_column("assessments", sa.Column("configuration", postgresql.JSONB(), nullable=True))
    for column in (
        sa.Column(
            "selected_option_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("evaluation_metadata", postgresql.JSONB(), nullable=True),
    ):
        op.add_column("question_attempts", column)
    for name in ("submitted_answer", "result_kind"):
        op.drop_constraint(op.f(f"ck_question_attempts_{name}"), "question_attempts")
    op.create_check_constraint(
        "submitted_answer",
        "question_attempts",
        "status <> 'submitted' OR answer_text IS NOT NULL OR selected_option_id IS NOT NULL "
        "OR cardinality(selected_option_ids) > 0",
    )
    op.create_check_constraint(
        "result_kind",
        "question_attempts",
        "result_kind IS NULL OR result_kind IN ('deterministic','simulation',"
        "'self_review','model_assisted')",
    )
    op.create_check_constraint(
        "score_provenance",
        "question_attempts",
        "(score IS NULL AND max_score IS NULL) OR "
        "(score IS NOT NULL AND max_score IS NOT NULL AND max_score IN (1,4) "
        "AND score BETWEEN 0 AND max_score "
        "AND status = 'submitted' AND result_kind IS NOT NULL AND grading_version IS NOT NULL)",
    )
    op.create_check_constraint(
        "selection_limit", "question_attempts", "cardinality(selected_option_ids) <= 6"
    )
    op.execute("""CREATE FUNCTION assessment_selections() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF cardinality(NEW.selected_option_ids) <>
          (SELECT count(DISTINCT x) FROM unnest(NEW.selected_option_ids) x)
          OR EXISTS (SELECT 1 FROM unnest(NEW.selected_option_ids) x WHERE x IS NULL OR NOT EXISTS (
            SELECT 1 FROM assessment_question_options p WHERE p.owner_id = NEW.owner_id
              AND p.assessment_question_id = NEW.assessment_question_id AND p.option_id = x))
        THEN RAISE EXCEPTION 'Selections must be distinct presented options'
          USING ERRCODE = '23514'; END IF;
        RETURN NEW;
      END $$""")
    op.execute("""CREATE TRIGGER assessment_selections BEFORE INSERT OR UPDATE ON question_attempts
      FOR EACH ROW EXECUTE FUNCTION assessment_selections()""")
    op.execute("""CREATE OR REPLACE FUNCTION relational_publication()
      RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF NEW.status = 'published' THEN
          IF NEW.question_type = 'short_answer' AND NOT EXISTS (
            SELECT 1 FROM short_answer_keys WHERE question_version_id = NEW.id)
          OR NEW.question_type IN ('multiple_choice','multiple_select') AND (
            (SELECT count(*) FROM question_options WHERE question_version_id = NEW.id)
              NOT BETWEEN 2 AND 6
            OR (NEW.question_type = 'multiple_choice' AND
              (SELECT count(*) FROM question_options WHERE question_version_id = NEW.id
                AND is_correct) <> 1)
            OR (NEW.question_type = 'multiple_select' AND (
              (SELECT count(*) FROM question_options WHERE question_version_id = NEW.id
                AND is_correct) < 2
              OR NOT EXISTS (SELECT 1 FROM question_options WHERE question_version_id = NEW.id
                AND NOT is_correct))))
          OR NEW.question_type IN ('written','design','behavioral') AND (
            SELECT coalesce(sum(weight),0) FROM question_rubric_criteria
            WHERE question_version_id = NEW.id) <> 1
          THEN RAISE EXCEPTION 'Published question requires a complete grading specification'
            USING ERRCODE = '23514'; END IF;
        END IF;
        RETURN NEW;
      END $$""")


def downgrade() -> None:
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM assessments WHERE configuration IS NOT NULL)
        OR EXISTS (SELECT 1 FROM question_versions WHERE question_type = 'multiple_select')
        OR EXISTS (SELECT 1 FROM question_attempts WHERE score IS NOT NULL
          OR max_score IS NOT NULL OR feedback IS NOT NULL OR evaluation_metadata IS NOT NULL
          OR cardinality(selected_option_ids) > 0 OR result_kind = 'model_assisted')
      THEN RAISE EXCEPTION 'Unsafe downgrade: real assessment data exists'; END IF;
    END $$""")
    op.execute("DROP TRIGGER assessment_selections ON question_attempts")
    op.execute("DROP FUNCTION assessment_selections()")
    for name in ("score_provenance", "selection_limit", "submitted_answer", "result_kind"):
        op.drop_constraint(op.f(f"ck_question_attempts_{name}"), "question_attempts")
    for name in ("selected_option_ids", "score", "max_score", "feedback", "evaluation_metadata"):
        op.drop_column("question_attempts", name)
    op.create_check_constraint(
        "submitted_answer",
        "question_attempts",
        "status <> 'submitted' OR answer_text IS NOT NULL OR selected_option_id IS NOT NULL",
    )
    op.create_check_constraint(
        "result_kind",
        "question_attempts",
        "result_kind IS NULL OR result_kind IN ('deterministic','simulation','self_review')",
    )
    op.drop_column("assessments", "configuration")
    op.drop_constraint(op.f("ck_question_versions_question_type"), "question_versions")
    op.create_check_constraint(
        "question_type",
        "question_versions",
        "question_type IN ('multiple_choice','short_answer','written','design','behavioral')",
    )
    # Restore the exact predecessor function without altering historical migrations.
    source = (Path(__file__).resolve().parents[1] / "relational_guards.sql").read_text(
        encoding="utf-8"
    )
    publication = next(
        s
        for s in source.split("-- statement-break")
        if "CREATE FUNCTION relational_publication()" in s
    )
    op.execute(publication.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
