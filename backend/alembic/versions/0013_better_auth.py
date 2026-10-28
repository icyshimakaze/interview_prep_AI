"""Add isolated Better Auth schema and provider bindings; preserve every owner."""

from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "0013_better_auth"
down_revision = "0012_ai_context_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA auth")
    op.execute("REVOKE ALL ON SCHEMA auth FROM PUBLIC")
    op.execute("SET LOCAL search_path = auth")
    sql = (Path(__file__).parents[1] / "better_auth_1_7_12.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute(
        "CREATE TABLE auth.request_limits (key_hash varchar(64) PRIMARY KEY, "
        "count integer NOT NULL CHECK (count > 0), expires_at timestamptz NOT NULL)"
    )
    op.execute("CREATE INDEX request_limits_expiry ON auth.request_limits (expires_at)")
    op.execute(
        'CREATE VIEW auth.api_sessions AS SELECT id, "userId" AS user_id, '
        '"expiresAt" AS expires_at FROM auth.session'
    )
    op.execute("SET LOCAL search_path = public")
    op.create_table(
        "principal_identities",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "principal_id",
            sa.Uuid(),
            sa.ForeignKey("principals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("issuer", sa.String(500), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.UniqueConstraint("issuer", "subject"),
        sa.UniqueConstraint("principal_id", "issuer"),
        sa.CheckConstraint(
            "length(trim(issuer)) > 0 AND length(trim(subject)) > 0", name="identity"
        ),
    )
    op.create_index(
        "ix_principal_identities_principal_id", "principal_identities", ["principal_id"]
    )
    op.execute(
        "INSERT INTO principal_identities(principal_id, issuer, subject) "
        "SELECT id, issuer, subject FROM principals WHERE kind='account'"
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.scalar(sa.text('SELECT EXISTS (SELECT 1 FROM auth."user")')) or connection.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM principal_identities i JOIN principals p "
            "ON p.id=i.principal_id WHERE i.issuer<>p.issuer OR i.subject<>p.subject)"
        )
    ):
        raise RuntimeError(
            "Refusing to discard auth users or linked identities; use compatibility rollback."
        )
    op.drop_table("principal_identities")
    # Named objects only: never CASCADE-drop unknown objects/data in an existing schema.
    op.execute("DROP VIEW auth.api_sessions")
    for table in ("request_limits", "jwks", "verification", "account", "session", "user"):
        op.execute(f'DROP TABLE auth."{table}"')
    op.execute("DROP SCHEMA auth")
