"""Owned local servers and a source-only snapshot; called by the disposable DB runner."""

import argparse
import asyncio
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from credential_scan import contains_server_credential
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from test_support import stop_owned_process, wait_for_server

ROOT = Path(__file__).resolve().parents[1]


async def runtime_urls(target: URL, suffix: str) -> tuple[str, str]:
    """Provision only this owned runner's roles, testing real privilege boundaries."""
    auth_role, api_role = "auth_test_" + suffix, "api_test_" + suffix
    auth_password, api_password = secrets.token_hex(24), secrets.token_hex(24)
    engine = create_async_engine(target, hide_parameters=True)
    try:
        async with engine.begin() as connection:
            for role, password in (
                (auth_role, auth_password),
                (api_role, api_password),
            ):
                await connection.execute(text(f"CREATE ROLE {role} LOGIN PASSWORD '{password}'"))
            for name in ("runtime-grants.sql", "better-auth-grants.sql"):
                sql = "\n".join(
                    line
                    for line in (ROOT / "deploy" / name).read_text(encoding="utf-8").splitlines()
                    if not line.lstrip().startswith("--")
                )
                sql = sql.replace("interview_prep_runtime", api_role).replace(
                    "interview_prep_auth", auth_role
                )
                for statement in sql.split(";"):
                    if statement.strip():
                        await connection.execute(text(statement))
    except SQLAlchemyError:
        raise RuntimeError(
            "Disposable runtime role setup failed; raw diagnostics withheld"
        ) from None
    finally:
        await engine.dispose()
    return (
        target.set(
            username=auth_role, password=auth_password, drivername="postgresql"
        ).render_as_string(hide_password=False),
        target.set(username=api_role, password=api_password).render_as_string(hide_password=False),
    )


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def junction(path: Path, target: Path) -> None:
    if os.name == "nt":

        def quote(value: Path) -> str:
            return "'" + str(value).replace("'", "''") + "'"

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "New-Item -ItemType Junction -Path "
                + quote(path)
                + " -Target "
                + quote(target)
                + " | Out-Null",
            ],
            check=True,
            capture_output=True,
        )
    else:
        path.symlink_to(target, target_is_directory=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run the full ordinary demo suite")
    parser.add_argument("--android", action="store_true", help="Use an authorized physical Android")
    parser.add_argument(
        "--social",
        action="store_true",
        help="Signed synthetic OAuth, never live providers",
    )
    arguments = parser.parse_args()
    demo, android = arguments.demo, arguments.android
    social = arguments.social
    if demo and (android or social):
        parser.error("Choose either the ordinary demo or physical Android journey")
    from sqlalchemy.engine import make_url

    target = make_url(os.environ.get("TEST_DATABASE_URL", ""))
    if target.host not in {"127.0.0.1", "localhost"} or not (target.database or "").endswith(
        "_test"
    ):
        raise ValueError("Only the disposable runner's loopback test database is allowed")
    cache = ROOT / ".cache" / "better-auth" / uuid4().hex[:12]
    cache.mkdir(parents=True)
    frontend = cache / "frontend"
    shutil.copytree(
        ROOT / "frontend",
        frontend,
        ignore=shutil.ignore_patterns(
            "node_modules",
            ".next",
            ".env*",
            "*.tsbuildinfo",
            "playwright-report",
            "test-results",
            ".cache",
        ),
    )
    for name in (
        "package.json",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
        "prettier.config.mjs",
    ):
        shutil.copy2(ROOT / name, cache / name)
    junction(frontend / "node_modules", ROOT / "frontend/node_modules")
    junction(cache / "node_modules", ROOT / "node_modules")
    config_path = frontend / "next.config.ts"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'const workspaceRoot = fileURLToPath(new URL("..", import.meta.url));',
            "const workspaceRoot = " + json.dumps(str(ROOT)) + ";",
        ),
        encoding="utf-8",
    )
    api_port, frontend_port = free_port(), free_port()
    while frontend_port == api_port:
        frontend_port = free_port()
    origin = f"http://localhost:{frontend_port}"
    environment = {
        **os.environ,
        "AUTH_PROVIDER": "better_auth",
        "AUTH_LOCAL_REGISTRATION_ENABLED": "true",
        "AUTH_ENABLED": "true",
        "AUTH_ISSUER": origin,
        "AUTH_JWKS_URL": origin + "/api/auth/jwks",
        "ALLOWED_ORIGINS": json.dumps([origin]),
        "BETTER_AUTH_URL": origin,
        "FRONTEND_ORIGIN": origin,
        "AUTH_DATABASE_URL": os.environ["TEST_AUTH_DATABASE_URL"],
        "BETTER_AUTH_SECRET": "synthetic-browser-auth-secret-longer-than-32-characters",
        "AUTH_RATE_LIMIT_KEY": "synthetic-browser-limit-secret-longer-than-32-characters",
        "BACKEND_INTERNAL_URL": f"http://127.0.0.1:{api_port}",
        "AUTH_BROWSER_TEST": "true",
        "E2E_BROWSER_CHANNEL": os.environ.get("E2E_BROWSER_CHANNEL", "chrome"),
        "FRONTEND_URL": origin,
        "NODE_ENV": "development",
        "INTERVIEW_WORKER_ENABLED": "true",
        "NODE_OPTIONS": "--max-old-space-size=1536",
    }
    if demo:
        environment.update(
            {
                "AUTH_PROVIDER": "clerk",
                "AUTH_ENABLED": "false",
                "AUTH_BROWSER_TEST": "false",
                "AUTH_LOCAL_REGISTRATION_ENABLED": "false",
                "BETTER_AUTH_SECRET": "",
                "AUTH_DATABASE_URL": "",
                "NODE_ENV": "production",
            }
        )
        subprocess.run(
            [sys.executable, "-m", "interview_prep.modules.questions.seed", "--apply"],
            env=environment,
            cwd=ROOT,
            check=True,
            timeout=60,
        )
    else:
        if android or social:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "interview_prep.modules.questions.seed",
                    "--apply",
                ],
                env=environment,
                cwd=ROOT,
                check=True,
                timeout=60,
            )
            environment["AUTH_LOCAL_REGISTRATION_ENABLED"] = "false"
        auth_url, api_url = asyncio.run(runtime_urls(target, cache.name))
        environment.update({"AUTH_DATABASE_URL": auth_url, "DATABASE_URL": api_url})
    if social:
        environment.update(
            {
                "AUTH_LOCAL_REGISTRATION_ENABLED": "false",
                "GOOGLE_AUTH_ENABLED": "true",
                "GOOGLE_CLIENT_ID": "synthetic-google-client.apps.googleusercontent.com",
                "GOOGLE_CLIENT_SECRET": "synthetic-google-secret",
                "GOOGLE_ALLOWED_SUBJECTS": '["synthetic-google-alice","synthetic-google-bob"]',
                "GITHUB_AUTH_ENABLED": "true",
                "GITHUB_CLIENT_ID": "synthetic-github-client",
                "GITHUB_CLIENT_SECRET": "synthetic-github-secret",
                "GITHUB_ALLOWED_SUBJECTS": '["10001","10002"]',
            }
        )
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node is required")
    next_cli = str(ROOT / "frontend/node_modules/next/dist/bin/next")
    # Compile in a separate source-only snapshot: no .env files or active .next tree.
    build_environment = {
        **environment,
        "NODE_ENV": "production",
        "NODE_OPTIONS": "--max-old-space-size=1024",
        "AUTH_LOCAL_REGISTRATION_ENABLED": "false",
        "BETTER_AUTH_URL": "https://auth.example.test",
        "FRONTEND_ORIGIN": "https://auth.example.test",
        "AUTH_DATABASE_URL": environment["AUTH_DATABASE_URL"] + "?sslmode=verify-full",
    }
    subprocess.run(
        [node, next_cli, "build"],
        cwd=frontend,
        env=build_environment,
        check=True,
        timeout=300,
    )
    if social:
        environment["SOCIAL_TEST_ORIGIN"] = origin
        environment["SOCIAL_TEST_ARTIFACTS"] = str(cache)
    android_failure: subprocess.CalledProcessError | None = None
    with ExitStack() as resources:
        for name, command, working_directory, ready in (
            (
                "api",
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "interview_prep.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                    "--no-proxy-headers",
                    "--no-access-log",
                ],
                ROOT,
                f"http://127.0.0.1:{api_port}/api/v1/health/ready",
            ),
            (
                "frontend",
                [
                    node,
                    next_cli,
                    "start" if demo else "dev",
                    *([] if demo else ["--webpack"]),
                    "--hostname",
                    "127.0.0.1" if android else "localhost",
                    "--port",
                    str(frontend_port),
                ],
                frontend,
                origin,
            ),
        ):
            log = resources.enter_context((cache / f"{name}.log").open("wb"))
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                env={
                    **environment,
                    "NODE_OPTIONS": environment["NODE_OPTIONS"]
                    + (
                        " --import="
                        + (ROOT / "frontend/scripts/oauth-browser-preload.mjs").as_uri()
                        if social and name == "frontend"
                        else ""
                    ),
                },
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            resources.callback(stop_owned_process, process)
            wait_for_server(process, ready)
        # Dev compilation is test provisioning, not an application response-time
        # assertion. Warm the dynamic auth/app routes before Playwright's normal
        # 15-second navigation deadline; keep that test deadline unchanged.
        import httpx

        with httpx.Client(follow_redirects=True, timeout=45, trust_env=False) as http:
            warm_routes = [
                "/sign-in",
                "/sign-up",
                "/app/dashboard",
                "/app/settings",
                "/app/resume",
            ]
            if android:
                warm_routes.extend(["/app/questions", "/app/assessments", "/app/interviews"])
            for route in warm_routes:
                if http.get(origin + route).status_code != 200:
                    raise RuntimeError("Local auth route warm-up failed; see owned snapshot logs")
            if not demo:
                for route in ("/api/auth/get-session", "/api/auth/jwks"):
                    if http.get(origin + route).status_code != 200:
                        raise RuntimeError("Local auth endpoint warm-up failed")
                # Compile the mutation entry point without creating a user or
                # changing a session. A no-session logout is idempotent.
                if (
                    http.post(
                        origin + "/api/auth/sign-out",
                        json={},
                        headers={"Origin": origin},
                    ).status_code
                    != 200
                ):
                    raise RuntimeError("Local auth mutation warm-up failed")
        environment["AUTH_SCREENSHOT_DIR"] = str(cache)
        if android:
            from android_test_support import run_android

            try:
                run_android(
                    {**environment, "ANDROID_SOCIAL_TEST": str(social).lower()},
                    origin,
                    cache,
                )
            except subprocess.CalledProcessError as error:
                android_failure = error
        elif social:
            subprocess.run(
                [node, "scripts/social-browser.mjs"],
                cwd=ROOT / "frontend",
                env=environment,
                check=True,
                timeout=600,
            )
        else:
            subprocess.run(
                [
                    node,
                    str(ROOT / "frontend/node_modules/@playwright/test/cli.js"),
                    "test",
                    "--project=chromium",
                    *(["--grep-invert", "Better Auth local"] if demo else ["better-auth.spec.ts"]),
                    "--workers=1",
                ],
                cwd=ROOT / "frontend",
                env=environment,
                check=True,
                timeout=600,
            )
            shutil.copy2(ROOT / ".cache/playwright-junit.xml", cache / "playwright-junit.xml")
    # Check only synthetic test credentials; never read persistent .env secrets.
    forbidden = [
        environment[key].encode()
        for key in (
            "BETTER_AUTH_SECRET",
            "AUTH_RATE_LIMIT_KEY",
            "AUTH_DATABASE_URL",
            "DATABASE_URL",
            "TEST_AUTH_DATABASE_URL",
            "GOOGLE_CLIENT_SECRET",
            "GITHUB_CLIENT_SECRET",
        )
        if environment.get(key)
    ]
    for key in ("AUTH_DATABASE_URL", "DATABASE_URL", "TEST_AUTH_DATABASE_URL"):
        password = urlsplit(environment.get(key, "")).password
        if password:
            forbidden.append(unquote(password).encode())
    forbidden.extend([b"Synthetic-password-0001", b"Synthetic-password-0002"])
    bundles = [
        file
        for directory in (".next/static", ".next/dev/static")
        for file in (frontend / directory).rglob("*.js")
    ]
    for file in [*bundles, cache / "api.log", cache / "frontend.log"]:
        payload = file.read_bytes()
        if contains_server_credential(payload, forbidden):
            raise RuntimeError("Credential scan failed; raw data withheld")
    (cache / "credential-scan.json").write_text(
        json.dumps(
            {
                "browser_files": len(bundles),
                "server_secret_matches": 0,
                "log_secret_matches": 0,
            }
        ),
        encoding="utf-8",
    )
    print("Local Better Auth browser/build artifacts: " + str(cache))
    if android_failure is not None:
        raise android_failure


if __name__ == "__main__":
    main()
