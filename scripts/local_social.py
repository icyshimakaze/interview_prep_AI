"""Bounded manual OAuth fixture: existing provider credentials, owned disposable DB only."""

import asyncio
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

from better_auth_browser import free_port, junction, runtime_urls
from credential_scan import contains_server_credential
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from test_support import mock_environment, require_free_port, stop_owned_process, wait_for_server

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / ".cache/phase-4-2-github"


def local_credentials() -> dict[str, str]:
    """Read only four names from an ignored, untracked file; never reuse DB settings."""
    path = ROOT / "frontend/.env.local"
    if subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=ROOT).returncode != 0:
        raise ValueError("Credentials file must be Git-ignored")
    if subprocess.check_output(["git", "ls-files", "--", str(path)], cwd=ROOT).strip():
        raise ValueError("Credentials file must be untracked")
    values = dotenv_values(path, interpolate=False)
    result: dict[str, str] = {}
    for provider in ("GOOGLE", "GITHUB"):
        for suffix in ("CLIENT_ID", "CLIENT_SECRET"):
            name = provider + "_" + suffix
            value = values.get(name)
            if not value or re.search(r"\s|REPLACE|YOUR_", value):
                raise ValueError("Complete local provider credentials required")
            result[name] = value
    cohort = json.loads((CONTROL / "cohort.json").read_text(encoding="utf-8"))
    if not isinstance(cohort, dict):
        raise ValueError("Verified operator cohort required")
    for provider, pattern in (("google", r"[A-Za-z0-9_-]{1,255}"), ("github", r"[1-9][0-9]{0,19}")):
        subjects = cohort.get(provider)
        if (
            not isinstance(subjects, list)
            or not 1 <= len(subjects) <= 32
            or not all(isinstance(item, str) and re.fullmatch(pattern, item) for item in subjects)
        ):
            raise ValueError("Verified stable provider subjects required")
        result[provider.upper() + "_ALLOWED_SUBJECTS"] = json.dumps(subjects)
        result[provider.upper() + "_AUTH_ENABLED"] = "true"
    return result


def redact_output(process: subprocess.Popen[bytes], path: Path, forbidden: list[bytes]) -> None:
    """Discard callback queries and credentials before logs reach disk."""
    assert process.stdout is not None
    with path.open("wb") as log:
        for line in process.stdout:
            line = re.sub(
                rb"(/api/auth/callback/(?:google|github))\?[^\s]*", rb"\1?[REDACTED]", line
            )
            for secret in forbidden:
                line = line.replace(secret, b"[REDACTED]")
            line = re.sub(rb"eyJ[A-Za-z0-9_.-]{30,}", b"[REDACTED-TOKEN]", line)
            log.write(line)
            log.flush()


def main() -> None:
    target = make_url(os.environ.get("TEST_DATABASE_URL", ""))
    if target.host not in {"127.0.0.1", "localhost"} or not (target.database or "").endswith(
        "_test"
    ):
        raise ValueError("Use only the disposable auth-test runner")
    require_free_port(3001)
    credentials = local_credentials()
    cache = CONTROL / ("live-" + uuid4().hex[:12])
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
    for name in ("package.json", "pnpm-workspace.yaml", "pnpm-lock.yaml", "prettier.config.mjs"):
        shutil.copy2(ROOT / name, cache / name)
    junction(frontend / "node_modules", ROOT / "frontend/node_modules")
    junction(cache / "node_modules", ROOT / "node_modules")
    config = frontend / "next.config.ts"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            'const workspaceRoot = fileURLToPath(new URL("..", import.meta.url));',
            "const workspaceRoot = " + json.dumps(str(ROOT)) + ";",
        ),
        encoding="utf-8",
    )
    # Instrument only this disposable snapshot. Keep the application's generic
    # callback UI; record a fixed diagnostic enum without claims, URLs or tokens.
    handler = frontend / "src/lib/better-auth/http.ts"
    anchor = "    const outgoing = new Headers(response.headers);"
    diagnostic = """    if (callback) {
      const code = new URL(response.headers.get("location") ?? "/", settings.origin)
        .searchParams.get("error");
      const known = ["social_admission_closed", "social_provider_state_mismatch",
        "state_mismatch", "state_not_found", "invalid_code", "unable_to_get_user_info",
        "account_not_linked", "email_not_found", "unable_to_link_account"];
      console.info(JSON.stringify({local_oauth_callback: callbackProvider,
        result: code ? (known.includes(code) ? code : "other_failure") : "success"}));
    }
"""
    source = handler.read_text(encoding="utf-8")
    if source.count(anchor) != 1:
        raise ValueError("Local diagnostic anchor changed; review fixture")
    handler.write_text(source.replace(anchor, diagnostic + anchor), encoding="utf-8")
    auth_url, api_url = asyncio.run(runtime_urls(target, cache.name.replace("-", "")))
    origin, api_port = "http://localhost:3001", free_port()
    environment = {
        **mock_environment(),
        "AUTH_PROVIDER": "better_auth",
        "AUTH_ENABLED": "true",
        "AUTH_LOCAL_REGISTRATION_ENABLED": "false",
        "AUTH_ISSUER": origin,
        "AUTH_JWKS_URL": origin + "/api/auth/jwks",
        "ALLOWED_ORIGINS": json.dumps([origin]),
        "FRONTEND_ORIGIN": origin,
        "BETTER_AUTH_URL": origin,
        "DATABASE_URL": api_url,
        "AUTH_DATABASE_URL": auth_url,
        "BETTER_AUTH_SECRET": secrets.token_hex(32),
        "AUTH_RATE_LIMIT_KEY": secrets.token_hex(32),
        "BACKEND_PROXY_SECRET": secrets.token_hex(32),
        "BACKEND_INTERNAL_URL": f"http://127.0.0.1:{api_port}",
        "NODE_ENV": "development",
        "NODE_OPTIONS": "--max-old-space-size=1536",
        "INTERVIEW_WORKER_ENABLED": "true",
    }
    # Provider credentials go only to Next; the API sees no provider credentials.
    frontend_environment = {**environment, **credentials}
    forbidden = [
        value.encode()
        for key, value in frontend_environment.items()
        if (
            "SECRET" in key
            or key.endswith("DATABASE_URL")
            or key.endswith("CLIENT_ID")
            or key == "AUTH_RATE_LIMIT_KEY"
        )
        and value
    ]
    threads: list[threading.Thread] = []
    stop = CONTROL / "stop-live"
    stop.unlink(missing_ok=True)
    try:
        with ExitStack() as resources:
            for name, command, cwd, env, ready in (
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
                        "--no-access-log",
                        "--no-proxy-headers",
                    ],
                    ROOT,
                    environment,
                    f"http://127.0.0.1:{api_port}/api/v1/health/ready",
                ),
                (
                    "frontend",
                    [
                        "node",
                        str(ROOT / "frontend/node_modules/next/dist/bin/next"),
                        "dev",
                        "--webpack",
                        "--hostname",
                        "127.0.0.1",
                        "--port",
                        "3001",
                    ],
                    frontend,
                    frontend_environment,
                    origin,
                ),
            ):
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                resources.callback(stop_owned_process, process)
                thread = threading.Thread(
                    target=redact_output,
                    args=(process, cache / (name + ".log"), forbidden),
                    daemon=True,
                )
                thread.start()
                threads.append(thread)
                wait_for_server(process, ready)
            (CONTROL / "live-ready.json").write_text(
                json.dumps(
                    {
                        "origin": origin,
                        "artifacts": str(cache),
                        "synthetic_provider_transport": False,
                        "public_registration": False,
                    }
                ),
                encoding="utf-8",
            )
            print(
                "Manual real-provider fixture ready at http://localhost:3001/sign-in; "
                "30-minute limit.",
                flush=True,
            )
            deadline = time.monotonic() + 1800
            while time.monotonic() < deadline and not stop.exists():
                time.sleep(1)
    finally:
        for thread in threads:
            thread.join(timeout=5)
        files = [*frontend.glob(".next/dev/static/**/*.js"), *cache.glob("*.log")]
        matches = sum(contains_server_credential(path.read_bytes(), forbidden) for path in files)
        (cache / "credential-scan.json").write_text(
            json.dumps({"files": len(files), "matches": matches}), encoding="utf-8"
        )
        (CONTROL / "live-ready.json").unlink(missing_ok=True)
        print("Owned manual fixture stopped; existing environments unchanged.", flush=True)
        if matches:
            raise RuntimeError("Local credential scan failed; raw data withheld")


if __name__ == "__main__":
    main()
