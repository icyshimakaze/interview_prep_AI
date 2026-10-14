"""Question-bank metadata and owned self-review attempts; preserve legacy versions."""

import sqlalchemy as sa

from alembic import op

revision: str = "0005_question_bank"
down_revision: str | None = "0004_resume_evidence"
branch_labels: str | None = None
depends_on: str | None = None


def record_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    for name, length in [("category", 100), ("subtopic", 100), ("source_classification", 17)]:
        op.add_column("question_versions", sa.Column(name, sa.String(length), nullable=True))
    for name in ("category", "subtopic"):
        op.create_check_constraint(
            name, "question_versions", f"{name} IS NULL OR length(trim({name})) BETWEEN 1 AND 100"
        )
    op.create_check_constraint(
        "question_source_classification",
        "question_versions",
        "source_classification IN "
        "('authored','legacy_adapted','external_reviewed','fictional_demo')",
    )
    op.create_index(
        "ix_question_versions_bank_filters",
        "question_versions",
        ["status", "category", "difficulty", "question_type"],
    )
    for table in ("question_expected_concepts", "question_tags", "question_roles"):
        fields: list[sa.SchemaItem] = [
            *record_columns(),
            sa.Column(
                "question_version_id",
                sa.Uuid(),
                sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
                nullable=False,
            ),
        ]
        if table == "question_expected_concepts":
            fields.extend(
                [
                    sa.Column("position", sa.Integer(), nullable=False),
                    sa.Column("text", sa.String(1000), nullable=False),
                    sa.UniqueConstraint("question_version_id", "position"),
                    sa.CheckConstraint("position BETWEEN 1 AND 12", name="position"),
                    sa.CheckConstraint("length(trim(text)) BETWEEN 1 AND 1000", name="text"),
                ]
            )
        else:
            fields.extend(
                [
                    sa.Column("label", sa.String(80), nullable=False),
                    sa.UniqueConstraint("question_version_id", "label"),
                    sa.CheckConstraint("length(trim(label)) BETWEEN 1 AND 80", name="label"),
                ]
            )
        op.create_table(table, *fields)
        op.create_index(f"ix_{table}_question_version_id", table, ["question_version_id"])
        if table != "question_expected_concepts":
            op.create_index(f"ix_{table}_label", table, ["label"])
        op.execute(
            f"CREATE TRIGGER bank_frozen_content BEFORE INSERT OR UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION relational_curriculum_child()"
        )
        op.execute(
            f"CREATE TRIGGER bank_touch BEFORE UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION relational_touch()"
        )
    table = "question_practice_attempts"
    op.create_table(
        table,
        *record_columns(),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            sa.ForeignKey("principals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_version_id",
            sa.Uuid(),
            sa.ForeignKey(
                "question_versions.id", ondelete="NO ACTION", deferrable=True, initially="DEFERRED"
            ),
            nullable=False,
        ),
        sa.Column("submission_key", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_kind", sa.String(20), nullable=False),
        sa.UniqueConstraint("owner_id", "id"),
        sa.UniqueConstraint("owner_id", "submission_key"),
        sa.CheckConstraint("updated_at >= created_at", name="timestamp_order"),
        sa.CheckConstraint("length(trim(answer_text)) BETWEEN 1 AND 10000", name="answer_length"),
        sa.CheckConstraint("result_kind IN ('self_review','simulation')", name="result_kind"),
    )
    op.create_index(f"ix_{table}_owner_created", table, ["owner_id", "created_at"])
    op.create_index(f"ix_{table}_question_version_id", table, ["question_version_id"])
    op.create_index(
        f"ix_{table}_owner_version", table, ["owner_id", "question_version_id", "submitted_at"]
    )
    op.execute(
        f"CREATE TRIGGER bank_owned_question BEFORE INSERT ON {table} "
        "FOR EACH ROW EXECUTE FUNCTION relational_question_access()"
    )
    op.execute("""CREATE FUNCTION bank_immutable_attempt() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'Practice attempts are append-only' USING ERRCODE = '23514'; END $$""")
    op.execute(
        f"CREATE TRIGGER bank_immutable_attempt BEFORE UPDATE ON {table} "
        "FOR EACH ROW EXECUTE FUNCTION bank_immutable_attempt()"
    )


def downgrade() -> None:
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM question_versions
        WHERE category IS NOT NULL OR subtopic IS NOT NULL OR source_classification IS NOT NULL)
        OR EXISTS (SELECT 1 FROM question_expected_concepts)
        OR EXISTS (SELECT 1 FROM question_tags) OR EXISTS (SELECT 1 FROM question_roles)
        OR EXISTS (SELECT 1 FROM question_practice_attempts)
      THEN RAISE EXCEPTION 'Unsafe downgrade: question bank content or history exists'; END IF;
    END $$""")
    op.drop_table("question_practice_attempts")
    op.execute("DROP FUNCTION bank_immutable_attempt()")
    for table in ("question_expected_concepts", "question_tags", "question_roles"):
        op.drop_table(table)
    op.drop_index("ix_question_versions_bank_filters", table_name="question_versions")
    for name in ("category", "subtopic", "question_source_classification"):
        op.drop_constraint(op.f(f"ck_question_versions_{name}"), "question_versions")
    for name in ("category", "subtopic", "source_classification"):
        op.drop_column("question_versions", name)
