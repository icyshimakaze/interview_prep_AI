"""Synthetic dump/restore drill; accepts only the current owned disposable container."""

import asyncio
import difflib
import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from interview_prep.db.models import Base
from interview_prep.modules.context.models import Resume
from interview_prep.modules.identity.models import PrincipalIdentity, Profile, User
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from interview_prep.modules.questions.models import QuestionVersion
from interview_prep.modules.questions.seed import load_assessment_seed, load_bank_seed

ROOT = Path(__file__).resolve().parents[1]


def docker(*arguments: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["docker", *arguments],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Recovery Docker operation failed; raw diagnostics withheld")
    return result.stdout


def owned_target() -> tuple[str, URL]:
    container = os.environ.get("AUTH_RECOVERY_TEST_CONTAINER", "")
    url = make_url(os.environ.get("TEST_DATABASE_URL", ""))
    if (
        not re.fullmatch(r"interview-prep-auth-[a-f0-9]{12}", container)
        or url.host != "127.0.0.1"
        or not re.fullmatch(r"interview_prep_[a-f0-9]{12}_test", url.database or "")
        or url.drivername != "postgresql+asyncpg"
    ):
        raise ValueError("Recovery requires an explicit owned loopback test target")
    details = json.loads(docker("inspect", container))[0]
    if details["Config"]["Labels"].get("interview-prep.disposable-auth") != "true":
        raise ValueError("Container is not owned by the disposable auth runner")
    if "/tmp" not in details["HostConfig"].get("Tmpfs", {}):
        raise ValueError("Recovery archive requires owned temporary memory storage")
    if f"POSTGRES_DB={url.database}" not in details["Config"]["Env"]:
        raise ValueError("Container database identity mismatch")
    ports = details["NetworkSettings"]["Ports"]["5432/tcp"]
    if ports != [{"HostIp": "127.0.0.1", "HostPort": str(url.port)}]:
        raise ValueError("Container port identity mismatch")
    return container, url


def schema_dump(container: str, database: str) -> str:
    result = docker(
        "exec",
        container,
        "pg_dump",
        "-U",
        "postgres",
        "-d",
        database,
        "--schema-only",
        "--no-owner",
        "--no-acl",
    )
    # PostgreSQL 18 emits independent random psql restriction keys on every dump.
    return "\n".join(
        line
        for line in result.splitlines()
        if not line.startswith(("\\restrict ", "\\unrestrict "))
    )


async def fingerprint(url: URL) -> dict[str, dict[str, int | str]]:
    engine = create_async_engine(url)
    result: dict[str, dict[str, int | str]] = {}
    try:
        async with engine.connect() as connection:
            tables = await connection.execute(
                text(
                    "SELECT table_schema,table_name FROM information_schema.tables "
                    "WHERE table_schema IN ('auth','public') AND table_type='BASE TABLE' "
                    "ORDER BY table_schema,table_name"
                )
            )
            for schema, table in tables:
                if not all(
                    re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", part) for part in (schema, table)
                ):
                    raise ValueError("Unexpected synthetic relation")
                rows = (
                    (
                        await connection.execute(
                            text(
                                f'SELECT row_to_json(t)::text FROM "{schema}"."{table}" t '
                                "ORDER BY row_to_json(t)::text"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                result[f"{schema}.{table}"] = {
                    "rows": len(rows),
                    "sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest(),
                }
    finally:
        await engine.dispose()
    return result


async def seed(url: URL) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = create_async_engine(url)
    try:
        async with async_sessionmaker(engine)() as session, session.begin():
            await load_bank_seed(session)
            await load_assessment_seed(session)
            question_version = await session.scalar(
                select(QuestionVersion).order_by(QuestionVersion.id)
            )
            assert question_version
            owner = User(
                kind="account",
                issuer="https://legacy.example.test",
                subject="synthetic",
            )
            session.add(owner)
            await session.flush()
            session.add_all(
                [
                    PrincipalIdentity(
                        principal_id=owner.id,
                        issuer=owner.issuer,
                        subject=owner.subject,
                    ),
                    Profile(
                        owner_id=owner.id,
                        target_role="Synthetic recovery",
                        experience_band="entry",
                        timezone="UTC",
                        weekly_minutes=180,
                        revision=3,
                    ),
                    Resume(owner_id=owner.id, label="Synthetic resume"),
                ]
            )
            interview = InterviewSession(
                owner_id=owner.id,
                mode="mock_interview",
                status="completed",
                context_version="synthetic",
                policy_version="synthetic",
                provider="mock",
                main_question_limit=1,
                completed_at=datetime.now(UTC),
            )
            session.add(interview)
            await session.flush()
            question = InterviewQuestion(
                owner_id=owner.id,
                session_id=interview.id,
                question_version_id=question_version.id,
                stable_question_id=question_version.question_id,
                sequence=1,
                main_ordinal=1,
                status="evaluated",
                source_kind="bank",
            )
            session.add(question)
            await session.flush()
            answer = InterviewAnswer(
                owner_id=owner.id,
                interview_question_id=question.id,
                status="submitted",
                answer_text="Synthetic retained recovery answer.",
                submitted_at=datetime.now(UTC),
                submission_key=uuid4(),
            )
            session.add(answer)
            await session.flush()
            session.add(
                AnswerEvaluation(
                    owner_id=owner.id,
                    interview_answer_id=answer.id,
                    version=1,
                    kind="self_review",
                    status="not_evaluable",
                    evaluator_version="synthetic",
                    rubric_version="synthetic",
                    feedback="Synthetic self-review only; no predictive score.",
                )
            )
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    'INSERT INTO auth."user" (id,name,email,"emailVerified") '
                    "VALUES ('recovery-user','Synthetic','recovery@example.invalid',false)"
                )
            )
            await connection.execute(
                text(
                    'INSERT INTO auth.session (id,"userId",token,"expiresAt","updatedAt") '
                    "VALUES ('recovery-session','recovery-user',:token,"
                    "CURRENT_TIMESTAMP + interval '1 day',CURRENT_TIMESTAMP)"
                ),
                {"token": uuid4().hex},
            )
    finally:
        await engine.dispose()


async def validate_recovery(url: URL) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            if (
                await connection.scalar(text("SELECT version_num FROM alembic_version"))
                != "0013_better_auth"
            ):
                raise AssertionError("Restored migration revision mismatch")
            # Database-enforced FKs were recreated and validated by pg_restore.
            if (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM pg_constraint c "
                        "JOIN pg_namespace n ON n.oid=c.connamespace "
                        "WHERE n.nspname IN ('public','auth') AND NOT c.convalidated"
                    )
                )
                != 0
            ):
                raise AssertionError("Restored constraints are not validated")
            for table in ("candidate_profiles", "resumes", "interview_sessions"):
                if (
                    await connection.scalar(
                        text(
                            f"SELECT count(*) FROM {table} r "
                            "LEFT JOIN principals p ON p.id=r.owner_id "
                            "WHERE p.id IS NULL"
                        )
                    )
                    != 0
                ):
                    raise AssertionError("Restored ownership mismatch")
            if await connection.scalar(text("SELECT count(*) FROM auth.api_sessions")) != 1:
                raise AssertionError("Session projection did not restore")
            # Recovery would resurrect pre-backup sessions. Expire them before opening traffic.
            await connection.execute(text('UPDATE auth.session SET "expiresAt"=CURRENT_TIMESTAMP'))
            if (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM auth.api_sessions "
                        "WHERE expires_at > CURRENT_TIMESTAMP"
                    )
                )
                != 0
            ):
                raise AssertionError("Restored sessions were not revoked")
    finally:
        await engine.dispose()


async def main() -> None:
    container, source = owned_target()
    source_name = source.database
    assert source_name
    restored_name = f"interview_prep_{uuid4().hex[:12]}_test"
    restored = source.set(database=restored_name)
    await seed(source)
    before = await fingerprint(source)
    if not {f"public.{name}" for name in Base.metadata.tables} <= before.keys():
        raise AssertionError("Recovery schema is missing business tables")
    original_schema = schema_dump(container, source_name)
    # Parse the independent plain-schema dump into a separate empty reference.
    # PG18 deparses some equivalent CHECK expressions differently after parsing;
    # compare two parsed schemas rather than discarding or normalizing constraints.
    reference_name = f"interview_prep_{uuid4().hex[:12]}_test"
    docker("exec", container, "createdb", "-U", "postgres", reference_name)
    docker(
        "exec",
        "-i",
        container,
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-1",
        "-U",
        "postgres",
        "-d",
        reference_name,
        input_text=original_schema,
    )
    expected_schema = schema_dump(container, reference_name)
    docker(
        "exec",
        container,
        "pg_dump",
        "-U",
        "postgres",
        "-d",
        source_name,
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--file=/tmp/phase4.dump",
    )
    digest = docker("exec", container, "sha256sum", "/tmp/phase4.dump").split()[0]
    docker("exec", container, "createdb", "-U", "postgres", restored_name)
    if await fingerprint(restored):
        raise AssertionError("Refusing to restore into a nonempty database")
    docker(
        "exec",
        container,
        "pg_restore",
        "-U",
        "postgres",
        "-d",
        restored_name,
        "--single-transaction",
        "--exit-on-error",
        "--no-owner",
        "--no-acl",
        "/tmp/phase4.dump",
    )
    if before != await fingerprint(restored):
        raise AssertionError("Restored row counts/content fingerprints differ")
    restored_schema = schema_dump(container, restored_name)
    if expected_schema != restored_schema:
        output = ROOT / ".cache/phase-4"
        output.mkdir(parents=True, exist_ok=True)
        (output / "schema-difference.txt").write_text(
            "\n".join(
                difflib.unified_diff(expected_schema.splitlines(), restored_schema.splitlines())
            ),
            encoding="utf-8",
        )
        raise AssertionError("Restored schema differs")
    await validate_recovery(restored)
    # The source remains unchanged even after session revocation on the restored target.
    if before != await fingerprint(source):
        raise AssertionError("Recovery changed the source")
    report = {
        "result": "passed",
        "synthetic_only": True,
        "existing_databases_used": False,
        "tables": before,
        "schema_equal": True,
        "archive_sha256": digest,
        "row_content_equal": True,
        "validated_constraints": True,
        "ownership_orphans": 0,
        "restored_active_sessions_after_revocation": 0,
        "source_unchanged": True,
        "archive_location": "owned container tmpfs; removed with container",
        "limitations": (
            "No hosted Neon restore, real credentials, roles/ACL backup or upload blob restore"
        ),
    }
    output = ROOT / ".cache/phase-4"
    output.mkdir(parents=True, exist_ok=True)
    (output / "recovery.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "tables"}))


if __name__ == "__main__":
    asyncio.run(main())
