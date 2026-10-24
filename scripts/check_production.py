"""Verify production-mode TLS, roles, migrations, mock demo and the built gateway locally."""

import argparse
import asyncio
import json
import secrets
import shutil
import ssl
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

import httpx
from production_support import generate_certificates, tls_gateway
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from test_support import (
    mock_environment,
    require_free_port,
    stop_owned_process,
    wait_for_server,
)

ROOT = Path(__file__).resolve().parents[1]
POSTGRES_DIGEST = "afc7e2d441324c0388fa80c3d24f733b4194a4eb7f47dd8ee2b08eb1a24a647c"
POSTGRES_IMAGE = f"postgres:18-bookworm@sha256:{POSTGRES_DIGEST}"


def docker(*arguments: str) -> str:
    result = subprocess.run(
        ["docker", *arguments], cwd=ROOT, capture_output=True, timeout=300, check=False
    )
    if result.returncode:
        # Runtime/config errors may include connection strings; retain no raw output here.
        raise RuntimeError("Local production-check container command failed")
    return result.stdout.decode("utf-8").strip()


def write_environment(path: Path, values: dict[str, str]) -> None:
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )


async def initialize_roles(url: str, ca: Path, password: str) -> None:
    engine = create_async_engine(
        url,
        connect_args={"ssl": ssl.create_default_context(cafile=ca)},
        hide_parameters=True,
    )
    try:
        async with engine.begin() as connection:
            assert await connection.scalar(
                text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
            )
            # Password is generated hexadecimal, never supplied input or printed.
            assert len(password) == 48 and all(c in "0123456789abcdef" for c in password)
            await connection.execute(
                text(f"CREATE ROLE interview_prep_runtime LOGIN PASSWORD '{password}'")
            )
            grants = "\n".join(
                line
                for line in (ROOT / "deploy/runtime-grants.sql").read_text().splitlines()
                if not line.lstrip().startswith("--")
            )
            for statement in grants.split(";"):
                if statement.strip():
                    await connection.execute(text(statement))
            assert not await connection.scalar(
                text("SELECT has_schema_privilege('interview_prep_runtime', 'public', 'CREATE')")
            )
            assert not await connection.scalar(
                text(
                    "SELECT has_table_privilege('interview_prep_runtime', "
                    "'alembic_version', 'UPDATE')"
                )
            )
    except SQLAlchemyError as error:
        raise RuntimeError(
            f"Restricted runtime-role setup failed ({type(error).__name__})"
        ) from None
    finally:
        await engine.dispose()


async def expire_demo(url: str, ca: Path, workspace: str) -> None:
    engine = create_async_engine(
        url,
        connect_args={"ssl": ssl.create_default_context(cafile=ca)},
        hide_parameters=True,
    )
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE demo_workspaces SET expires_at=now()-interval '1 second' "
                    "WHERE id=CAST(:id AS uuid)"
                ),
                {"id": workspace},
            )
    finally:
        await engine.dispose()


async def verify_cleanup(url: str, ca: Path, workspace: str) -> None:
    engine = create_async_engine(
        url,
        connect_args={"ssl": ssl.create_default_context(cafile=ca)},
        hide_parameters=True,
    )
    try:
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM principals WHERE id=CAST(:id AS uuid)"),
                    {"id": workspace},
                )
                == 0
            )
            assert await connection.scalar(text("SELECT count(*) FROM demo_workspaces")) == 1
    finally:
        await engine.dispose()


def verify_http(frontend: str, backend: str, ca: Path, secret: str, cookie_file: Path) -> str:
    context = ssl.create_default_context(cafile=ca)
    with ExitStack() as stack:
        first, second = [
            stack.enter_context(
                httpx.Client(base_url=frontend, verify=context, timeout=45, trust_env=False)
            )
            for _ in range(2)
        ]
        direct = stack.enter_context(
            httpx.Client(base_url=backend, verify=context, timeout=15, trust_env=False)
        )
        assert first.get("/").status_code == 200
        ready = first.get("/api/v1/health/ready")
        assert (
            ready.status_code == 200
            and ready.json()["schema_revision"] == "0012_ai_context_reviews"
        )
        assert secret not in ready.text and secret not in str(ready.headers)
        assert direct.get("/api/v1/health/ready").status_code == 200
        assert (
            direct.post("/api/v1/demo/sessions", json={}, headers={"origin": frontend}).status_code
            == 403
        )
        allowed = direct.options(
            "/api/v1/demo/sessions",
            headers={"origin": frontend, "access-control-request-method": "POST"},
        )
        assert (
            allowed.status_code == 200
            and allowed.headers["access-control-allow-origin"] == frontend
        )
        assert (
            direct.options(
                "/api/v1/demo/sessions",
                headers={
                    "origin": "https://untrusted.example",
                    "access-control-request-method": "POST",
                },
            ).status_code
            == 400
        )
        identifiers: list[str] = []
        for visitor in (first, second):
            response = visitor.post(
                "/api/v1/demo/sessions",
                json={},
                headers={
                    "Origin": frontend,
                    "x-interview-prep-gateway": "forged",
                    "x-interview-prep-client-ip": "192.0.2.90",
                    "x-forwarded-for": "192.0.2.91",
                    "x-vercel-forwarded-for": "192.0.2.92",
                },
            )
            assert response.status_code == 200, "Production secure-cookie demo bootstrap failed"
            identifiers.append(response.json()["id"])
            cookies = response.headers.get_list("set-cookie")
            assert len(cookies) == 2 and all("Secure" in c and "SameSite=lax" in c for c in cookies)
            assert "HttpOnly" in next(c for c in cookies if c.startswith("interview_prep_demo="))
            assert all("Domain=" not in c for c in cookies)
            assert secret not in response.text and secret not in str(response.headers)
            assert visitor.get("/api/v1/demo/dashboard").json()["mode"] == "demo"
            assert visitor.get("/api/v1/demo/questions?limit=12&offset=0").json()["total"] == 29
            assert (
                visitor.get("/api/v1/demo/assessments/options").json()["conceptual_kind"]
                == "simulation"
            )
            assert (
                visitor.get("/api/v1/demo/interviews/options").json()["provider"]["name"]
                == "MockAIProvider"
            )
            assert (
                visitor.post(
                    "/api/v1/demo/sessions", json={}, headers={"Origin": frontend}
                ).status_code
                == 403
            )
            csrf = visitor.cookies.get("interview_prep_csrf")
            assert csrf
            assert (
                visitor.post(
                    "/api/v1/demo/sessions",
                    json={},
                    headers={"Origin": frontend, "X-CSRF-Token": csrf},
                ).json()["id"]
                == identifiers[-1]
            )
            assert visitor.get("/api/v1/account/dashboard").status_code == 403
        assert identifiers[0] != identifiers[1]
        # Exercise PDF parsing inside the non-root 512 MiB Linux container using
        # the restricted database role, not just the development Python worker.
        upload_path = "/api/v1/demo/resume-library"
        upload_headers = {
            "Origin": frontend,
            "X-CSRF-Token": first.cookies.get("interview_prep_csrf") or "",
            "Content-Type": "application/pdf",
            "X-Resume-Filename": "synthetic-resume.pdf",
        }
        uploaded = first.post(
            upload_path,
            headers=upload_headers,
            content=(ROOT / "frontend/tests/e2e/fixtures/synthetic-resume.pdf").read_bytes(),
        )
        assert uploaded.status_code == 201, "Production PDF upload failed"
        resume = uploaded.json()
        assert resume["is_sample"] is False and resume["page_count"] == 1
        assert any(item["claim"] == "Python" for item in resume["evidence"])
        resource = f"{upload_path}/{resume['id']}"
        assert second.get(resource).status_code == 404
        assert (
            first.delete(f"{resource}?expected_revision=1", headers=upload_headers).status_code
            == 204
        )
        assert first.get(resource).status_code == 404
        with httpx.Client(base_url=frontend, verify=context, timeout=30, trust_env=False) as third:
            assert (
                third.post(
                    "/api/v1/demo/sessions",
                    json={},
                    headers={"Origin": frontend, "X-Forwarded-For": "192.0.2.100"},
                ).status_code
                == 429
            )
        wrong_origin = first.post(
            "/api/v1/demo/sessions",
            json={},
            headers={
                "Origin": "https://untrusted.example",
                "X-CSRF-Token": first.cookies.get("interview_prep_csrf") or "",
            },
        )
        assert wrong_origin.status_code == 403
        # Keep only a credential for the soon-expired fictional visitor in ignored diagnostics.
        cookie_file.write_text(first.cookies.get("interview_prep_demo") or "")
        return identifiers[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Use the local production-check backend image",
    )
    parser.add_argument("--database-port", type=int, default=18543)
    parser.add_argument("--api-port", type=int, default=18102)
    parser.add_argument("--frontend-port", type=int, default=13102)
    parser.add_argument("--backend-tls-port", type=int, default=18443)
    parser.add_argument("--frontend-tls-port", type=int, default=13443)
    args = parser.parse_args()
    ports = [
        args.database_port,
        args.api_port,
        args.frontend_port,
        args.backend_tls_port,
        args.frontend_tls_port,
    ]
    if len(set(ports)) != len(ports):
        parser.error("Verification ports must be distinct")
    for port in ports:
        require_free_port(port)
    pnpm, node = shutil.which("pnpm"), shutil.which("node")
    if pnpm is None or node is None:
        raise RuntimeError("Node and pnpm are required")
    image = "interview-prep-api:production-check"
    if not args.skip_build:
        subprocess.run(
            ["docker", "build", "-f", "deploy/backend.Dockerfile", "-t", image, "."],
            cwd=ROOT,
            check=True,
            timeout=600,
        )
    run_id = uuid4().hex[:12]
    directory = ROOT / ".cache" / f"production-{run_id}"
    directory.mkdir(parents=True, exist_ok=False)
    certificates = directory / "tls"
    generate_certificates(certificates)
    database_name, api_name = (
        f"production-check-db-{run_id}",
        f"production-check-api-{run_id}",
    )
    owner_password, runtime_password = secrets.token_hex(24), secrets.token_hex(24)
    secret, quota = secrets.token_urlsafe(48), secrets.token_urlsafe(48)
    frontend, backend = (
        f"https://localhost:{args.frontend_tls_port}",
        f"https://localhost:{args.backend_tls_port}",
    )
    common = {
        "APP_ENV": "production",
        "PUBLIC_DEMO_ONLY": "true",
        "AUTH_ENABLED": "false",
        "AI_PROVIDER": "mock",
        "OPENAI_API_KEY": "",
        "XKIRO_API_KEY": "",
        "OPENAI_MODEL": "",
        "OLLAMA_BASE_URL": "",
        "OLLAMA_MODEL": "",
        "BACKEND_PROXY_SECRET": secret,
        "DEMO_RATE_LIMIT_KEY": quota,
        "ALLOWED_ORIGINS": json.dumps([frontend]),
        "DATABASE_SSL_MODE": "verify-full",
        "DATABASE_SSL_CA_FILE": "/run/check-ca.pem",
        "DATABASE_CONNECT_TIMEOUT_SECONDS": "10",
        "PORT": "10000",
        "INTERVIEW_WORKER_ENABLED": "true",
        "INTERVIEW_POLL_SECONDS": "600",
        "CLEANUP_ENABLED": "true",
        "FILE_WORKER_SLOTS": "1",
        "DEMO_TTL_SECONDS": "86400",
    }
    owner = {
        **common,
        "DATABASE_URL": f"postgresql+asyncpg://production_owner:{owner_password}@host.docker.internal:{args.database_port}/production_test",
    }
    runtime = {
        **common,
        "DATABASE_URL": f"postgresql+asyncpg://interview_prep_runtime:{runtime_password}@host.docker.internal:{args.database_port}/production_test",
    }
    write_environment(directory / "owner.env", owner)
    write_environment(directory / "runtime.env", runtime)
    write_environment(
        directory / "postgres.env",
        {
            "POSTGRES_USER": "production_owner",
            "POSTGRES_PASSWORD": owner_password,
            "POSTGRES_DB": "production_test",
        },
    )
    mount = f"type=bind,source={certificates / 'ca.pem'},target=/run/check-ca.pem,readonly"
    postgres_mount = f"type=bind,source={certificates},target=/run/check-tls,readonly"
    owned: list[str] = []
    try:
        docker(
            "run",
            "-d",
            "--name",
            database_name,
            "--env-file",
            str(directory / "postgres.env"),
            "--mount",
            postgres_mount,
            "-p",
            f"127.0.0.1:{args.database_port}:5432",
            "--entrypoint",
            "sh",
            POSTGRES_IMAGE,
            "-c",
            "mkdir /tmp/check-tls && cp /run/check-tls/server.* /tmp/check-tls/ && "
            "chown -R postgres:postgres /tmp/check-tls && "
            "chmod 600 /tmp/check-tls/server.key && "
            "exec docker-entrypoint.sh postgres -c ssl=on "
            "-c ssl_cert_file=/tmp/check-tls/server.pem "
            "-c ssl_key_file=/tmp/check-tls/server.key",
        )
        owned.append(database_name)
        for _ in range(60):
            if (
                subprocess.run(
                    [
                        "docker",
                        "exec",
                        database_name,
                        "pg_isready",
                        "-U",
                        "production_owner",
                        "-d",
                        "production_test",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                ).returncode
                == 0
            ):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Disposable TLS PostgreSQL did not start")
        run_image = [
            "run",
            "--rm",
            "--env-file",
            str(directory / "owner.env"),
            "--mount",
            mount,
            image,
        ]
        docker(*run_image, "alembic", "upgrade", "head")
        docker(*run_image, "alembic", "check")
        first_seed = json.loads(
            docker(
                *run_image,
                "python",
                "-m",
                "interview_prep.modules.questions.seed",
                "--apply",
            )
        )
        second_seed = json.loads(
            docker(
                *run_image,
                "python",
                "-m",
                "interview_prep.modules.questions.seed",
                "--apply",
            )
        )
        assert first_seed["new_versions"] == 29 and second_seed["new_versions"] == 0
        host_url = f"postgresql+asyncpg://production_owner:{owner_password}@localhost:{args.database_port}/production_test"
        asyncio.run(initialize_roles(host_url, certificates / "ca.pem", runtime_password))
        docker(
            "run",
            "-d",
            "--name",
            api_name,
            "--memory",
            "512m",
            "--env-file",
            str(directory / "runtime.env"),
            "--mount",
            mount,
            "-p",
            f"127.0.0.1:{args.api_port}:10000",
            image,
        )
        owned.append(api_name)
        assert docker("inspect", "--format", "{{.Config.User}}", api_name) == "10001:10001"
        environment = {
            **mock_environment(),
            "VERCEL_ENV": "production",
            "PUBLIC_DEMO_ONLY": "true",
            "BACKEND_PROXY_SECRET": secret,
            "BACKEND_INTERNAL_URL": backend,
            "FRONTEND_ORIGIN": frontend,
            "NODE_EXTRA_CA_CERTS": str(certificates / "ca.pem"),
        }
        with ExitStack() as stack:
            stack.enter_context(
                tls_gateway(args.backend_tls_port, args.api_port, certificates, vercel=False)
            )
            with httpx.Client(timeout=3, trust_env=False) as waiting:
                for _ in range(60):
                    try:
                        if (
                            waiting.get(
                                f"http://127.0.0.1:{args.api_port}/api/v1/health/ready"
                            ).status_code
                            == 200
                        ):
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.5)
                else:
                    raise RuntimeError("Production API readiness failed")
            subprocess.run([pnpm, "build"], cwd=ROOT, env=environment, check=True, timeout=300)
            for path in (ROOT / "frontend/.next/static").rglob("*.js"):
                payload = path.read_bytes()
                assert all(
                    value.encode() not in payload
                    for value in (secret, quota, owner_password, runtime_password)
                ), "Server credential found in browser bundle"
            log = stack.enter_context((directory / "frontend.log").open("wb"))
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(
                [node, "scripts/start_frontend.mjs"],
                cwd=ROOT,
                env={
                    **environment,
                    "VERCEL": "1",
                    "PORT": str(args.frontend_port),
                    "FRONTEND_HOSTNAME": "127.0.0.1",
                },
                stdout=log,
                stderr=log,
                creationflags=creation_flags,
            )
            stack.callback(stop_owned_process, process)
            wait_for_server(process, f"http://127.0.0.1:{args.frontend_port}")
            stack.enter_context(
                tls_gateway(
                    args.frontend_tls_port,
                    args.frontend_port,
                    certificates,
                    vercel=True,
                )
            )
            expired = verify_http(
                frontend,
                backend,
                certificates / "ca.pem",
                secret,
                directory / "visitor-cookie.txt",
            )
            asyncio.run(expire_demo(host_url, certificates / "ca.pem", expired))
            docker(
                "run",
                "--rm",
                "--env-file",
                str(directory / "runtime.env"),
                "--mount",
                mount,
                image,
                "python",
                "-m",
                "interview_prep.cleanup",
            )
            asyncio.run(verify_cleanup(host_url, certificates / "ca.pem", expired))
            with httpx.Client(
                base_url=frontend,
                verify=ssl.create_default_context(cafile=certificates / "ca.pem"),
                trust_env=False,
            ) as check:
                check.cookies.set(
                    "interview_prep_demo",
                    (directory / "visitor-cookie.txt").read_text(),
                )
                assert check.get("/api/v1/demo/dashboard").status_code == 401
            report = {
                "status": "passed",
                "profile": "production",
                "ai_provider": "mock",
                "ai_credentials": False,
                "tls_database": True,
                "tls_frontend_backend": True,
                "restricted_runtime_role": True,
                "migrations": "0012_ai_context_reviews",
                "published": 29,
                "repeat_seed_writes": 0,
                "secure_cookie_csrf": True,
                "gateway_spoofing_rejected": True,
                "cleanup": True,
            }
            (directory / "result.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report))
    finally:
        for name in reversed(owned):
            if not name.endswith(run_id) or not name.startswith("production-check-"):
                raise RuntimeError("Refusing to remove an unowned container")
            subprocess.run(["docker", "rm", "-f", "-v", name], capture_output=True, check=False)
        for filename in (
            "owner.env",
            "runtime.env",
            "postgres.env",
            "visitor-cookie.txt",
        ):
            (directory / filename).unlink(missing_ok=True)
        (certificates / "server.key").unlink(missing_ok=True)
        print(
            "Owned verification containers stopped; ephemeral credentials removed. "
            "No hosted deployment."
        )


if __name__ == "__main__":
    main()
