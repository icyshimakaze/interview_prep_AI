"""Encrypted pre-0013 backup; source is read-only, restoration is owned local tmpfs."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import ssl
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from uuid import uuid4

from check_better_auth import IMAGE
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from test_support import mock_environment

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".cache/production-release/private"
SOURCE_FILE = PRIVATE / "production-backup-url.local"
HOST = "ep-square-brook-b3ybm6sa.c-4.ap-southeast-1.aws.neon.tech"
PROJECT = "autumn-sound-91017993"
BRANCH = "br-twilight-resonance-b3ukxsc8"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
AAD = (PROJECT + "/" + BRANCH + "/neondb/pre-0013").encode()
MAGIC = b"IPAI-BACKUP-V1\0"


class BackupToolError(RuntimeError):
    def __init__(self, tool: str, diagnostics: bytes) -> None:
        self.tool = tool if tool in {"pg_dump.exe", "docker", "python.exe"} else "subprocess"
        self.category = "unclassified"
        for marker, category in (
            (b"server version mismatch", "client_version_mismatch"),
            (b"password authentication failed", "authentication_failed"),
            (b"root certificate", "root_certificate_unavailable"),
            (b"certificate verify failed", "certificate_verification_failed"),
            (b"permission denied", "permission_denied"),
            (b"could not translate host name", "dns_failed"),
            (b"connection timed out", "connection_timeout"),
        ):
            if marker in diagnostics.lower():
                self.category = category
                break
        super().__init__("Backup tool failed; raw diagnostics withheld")


@dataclass(frozen=True, repr=False)
class Source:
    user: str
    password: str

    def url(self) -> URL:
        return URL.create("postgresql+asyncpg", self.user, self.password, HOST, 5432, "neondb")


def validate_source(value: str) -> Source:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname != HOST
        or parsed.port not in {None, 5432}
        or parsed.path != "/neondb"
        or parsed.fragment
        or not parsed.username
        or not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", unquote(parsed.username))
        or not parsed.password
        or any(
            key not in {"sslmode", "channel_binding", "sslrootcert", "application_name"}
            or len(items) != 1
            for key, items in parse_qs(parsed.query, keep_blank_values=True).items()
        )
    ):
        raise ValueError("Exact direct production backup source required")
    return Source(unquote(parsed.username), unquote(parsed.password))


async def command(
    arguments: list[str],
    *,
    environment: dict[str, str] | None = None,
    payload: bytes | None = None,
) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *arguments,
        env=environment,
        stdin=asyncio.subprocess.PIPE if payload is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        async with asyncio.timeout(180):
            output, diagnostics = await process.communicate(payload)
    except BaseException:
        if process.returncode is None:
            process.kill()
            await process.wait()
        raise
    if process.returncode:
        raise BackupToolError(Path(arguments[0]).name, diagnostics)
    return output


async def fingerprint(connection: AsyncConnection) -> dict[str, dict[str, int | str]]:
    relations = await connection.execute(
        text(
            "SELECT schemaname,tablename FROM pg_tables "
            "WHERE schemaname IN ('public','auth') ORDER BY schemaname,tablename"
        )
    )
    result: dict[str, dict[str, int | str]] = {}
    for schema, table in relations:
        if not all(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", str(v)) for v in (schema, table)):
            raise ValueError("Unexpected relation identifier")
        row = (
            await connection.execute(
                text(
                    f"SELECT count(*) AS rows, md5(coalesce(jsonb_agg(to_jsonb(t) "
                    f"ORDER BY to_jsonb(t)::text COLLATE \"C\")::text,'[]')) AS digest "
                    f'FROM "{schema}"."{table}" t'
                )
            )
        ).one()
        result[f"{schema}.{table}"] = {"rows": int(row.rows), "md5": str(row.digest)}
    return result


async def readonly_dump(source: Source) -> tuple[bytes, dict[str, dict[str, int | str]]]:
    context = ssl.create_default_context()
    # Native libpq/OpenSSL does not necessarily load Windows' trusted CA store.
    # Export only public trust roots from the same verifying Python context.
    trust_roots = PRIVATE / "backup-trust-roots.local"
    roots = context.get_ca_certs(binary_form=True)
    if not roots:
        raise ValueError("Verified system trust roots required")
    trust_roots.write_text("".join(ssl.DER_cert_to_PEM_cert(root) for root in roots))
    engine = create_async_engine(
        source.url(),
        connect_args={
            "ssl": context,
            "server_settings": {
                "default_transaction_read_only": "on",
                "timezone": "UTC",
                "statement_timeout": "60000",
            },
            "timeout": 10,
        },
    )
    try:
        async with engine.connect() as connection, connection.begin():
            await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            await connection.execute(text("SET TRANSACTION READ ONLY"))
            if await connection.scalar(text("SHOW transaction_read_only")) != "on":
                raise ValueError("Read-only source transaction required")
            if (
                await connection.scalar(text("SELECT version_num FROM public.alembic_version"))
                != "0012_ai_context_reviews"
            ):
                raise ValueError("This helper is restricted to the pre-0013 backup")
            snapshot = str(await connection.scalar(text("SELECT pg_export_snapshot()")))
            before = await fingerprint(connection)
            environment = {
                **{key: value for key, value in os.environ.items() if not key.startswith("PG")},
                "PGHOST": HOST,
                "PGPORT": "5432",
                "PGDATABASE": "neondb",
                "PGUSER": source.user,
                "PGPASSWORD": source.password,
                "PGSSLMODE": "verify-full",
                "PGSSLROOTCERT": str(trust_roots),
                "PGCONNECT_TIMEOUT": "10",
                "PGAPPNAME": "interview-prep-readonly-backup",
                "PGOPTIONS": "-c default_transaction_read_only=on",
            }
            archive = await command(
                [
                    str(BIN / "pg_dump.exe"),
                    "--no-password",
                    "--format=custom",
                    "--no-owner",
                    "--no-acl",
                    "--snapshot=" + snapshot,
                ],
                environment=environment,
            )
            if not archive.startswith(b"PGDMP") or len(archive) > 128 * 1024 * 1024:
                raise ValueError("Unexpected or oversized backup")
            return archive, before
    finally:
        await engine.dispose()


async def restore_and_check(
    archive: bytes, expected: dict[str, dict[str, int | str]]
) -> dict[str, object]:
    suffix = uuid4().hex[:12]
    name = "interview-prep-auth-" + suffix
    database = "interview_prep_" + suffix + "_test"
    password = secrets.token_urlsafe(32)
    container = ""
    try:
        container = (
            (
                await command(
                    [
                        "docker",
                        "run",
                        "--pull=never",
                        "-d",
                        "--name",
                        name,
                        "--label",
                        "interview-prep.disposable-auth=true",
                        "--memory",
                        "256m",
                        "--memory-swap",
                        "256m",
                        "--tmpfs",
                        "/var/lib/postgresql",
                        "--tmpfs",
                        "/tmp",
                        "-p",
                        "127.0.0.1::5432",
                        "-e",
                        "POSTGRES_PASSWORD",
                        "-e",
                        "POSTGRES_DB=" + database,
                        IMAGE,
                        "-c",
                        "shared_buffers=16MB",
                        "-c",
                        "max_connections=50",
                    ],
                    environment={**os.environ, "POSTGRES_PASSWORD": password},
                )
            )
            .decode()
            .strip()
        )
        if not re.fullmatch(r"[a-f0-9]{64}", container):
            raise ValueError("Owned restore container ID required")
        address = (await command(["docker", "port", container, "5432/tcp"])).decode().strip()
        port = re.fullmatch(r"127\.0\.0\.1:([0-9]+)", address)
        if not port:
            raise ValueError("Loopback-only restore target required")
        for _ in range(60):
            try:
                await command(["docker", "exec", container, "pg_isready", "-U", "postgres"])
                break
            except RuntimeError:
                await asyncio.sleep(0.5)
        else:
            raise RuntimeError("Owned restore server unavailable")
        await command(
            [
                "docker",
                "exec",
                "-i",
                container,
                "pg_restore",
                "-U",
                "postgres",
                "-d",
                database,
                "--no-owner",
                "--no-acl",
                "--single-transaction",
                "--exit-on-error",
            ],
            payload=archive,
        )
        local_url = URL.create(
            "postgresql+asyncpg", "postgres", password, "127.0.0.1", int(port[1]), database
        )
        engine = create_async_engine(
            local_url, connect_args={"server_settings": {"timezone": "UTC"}}
        )
        try:
            async with engine.connect() as connection:
                restored = await fingerprint(connection)
            if restored != expected:
                raise ValueError("Restored production backup fingerprints differ")
            environment = {
                **mock_environment(),
                "DATABASE_URL": local_url.render_as_string(hide_password=False),
                "DATABASE_SSL_MODE": "disable",
            }
            await command(
                [
                    str(ROOT / "backend/.venv/Scripts/python.exe"),
                    "-m",
                    "alembic",
                    "-c",
                    str(ROOT / "backend/alembic.ini"),
                    "upgrade",
                    "head",
                ],
                environment=environment,
            )
            async with engine.connect() as connection:
                upgraded = await fingerprint(connection)
                revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0013_better_auth" or any(
                upgraded.get(key) != value
                for key, value in expected.items()
                if key != "public.alembic_version"
            ):
                raise ValueError("Local additive migration changed old data")
            return {
                "restore_equal": True,
                "local_0013_upgrade_preserves_old_rows": True,
                "source_tables": len(expected),
                "source_rows": sum(int(v["rows"]) for v in expected.values()),
            }
        finally:
            await engine.dispose()
    finally:
        if re.fullmatch(r"[a-f0-9]{64}", container):
            await command(["docker", "rm", "-f", container])


async def create_backup() -> None:
    if not SOURCE_FILE.is_file() or not SOURCE_FILE.read_text().strip():
        print(json.dumps({"state": "blocked", "reason": "Private production backup URL required"}))
        raise SystemExit(2)
    source = validate_source(SOURCE_FILE.read_text())
    archive, before = await readonly_dump(source)
    key_path = PRIVATE / "backup-encryption-key.local"
    if not key_path.exists():
        with key_path.open("xb") as output:
            output.write(AESGCM.generate_key(bit_length=256))
    key = key_path.read_bytes()
    if len(key) != 32:
        raise ValueError("Existing backup encryption key is invalid")
    nonce = os.urandom(12)
    encrypted = MAGIC + nonce + AESGCM(key).encrypt(nonce, archive, AAD)
    path = PRIVATE / ("pre-0013-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".dump.aesgcm")
    with path.open("xb") as output:
        output.write(encrypted)
    restored_archive = AESGCM(key).decrypt(nonce, path.read_bytes()[len(MAGIC) + 12 :], AAD)
    if restored_archive != archive:
        raise ValueError("Encrypted backup readback differs")
    result = await restore_and_check(restored_archive, before)
    result.update(
        source_project=PROJECT,
        source_branch=BRANCH,
        source_transaction_read_only=True,
        encrypted_archive=str(path.relative_to(ROOT)),
        ciphertext_sha256=hashlib.sha256(encrypted).hexdigest(),
        encryption="AES-256-GCM; separate private key file; no plaintext dump on disk",
        roles_and_acl="Reapply reviewed grants; portable archive omits ACL/owner",
        production_writes=False,
    )
    evidence = ROOT / "docs/evidence/better-auth-production-release"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "production-backup.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create", action="store_true", required=True)
    parser.parse_args()
    try:
        asyncio.run(create_backup())
    except Exception as error:
        print(
            json.dumps(
                {
                    "state": "failed",
                    "error_type": type(error).__name__,
                    "tool": error.tool if isinstance(error, BackupToolError) else None,
                    "category": error.category if isinstance(error, BackupToolError) else None,
                    "message": "Backup not certified; raw diagnostics withheld",
                }
            )
        )
        raise SystemExit(1) from None
