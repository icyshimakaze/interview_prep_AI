"""Run browser checks with a fresh database and a temporary localhost API."""

import argparse
import asyncio
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
from check_backend import drop_created_database, prepare_test_database
from sqlalchemy.engine import make_url

from interview_prep.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def stop_owned_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # The Windows virtualenv launcher has a Python child. Terminate only this
        # process tree created by us, not an existing listener or unrelated Python.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def wait_for_api(process: subprocess.Popen[bytes], port: int) -> None:
    deadline = time.monotonic() + 45
    with httpx.Client(timeout=2, trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Temporary API failed to start; see .cache/browser-api.log")
            try:
                if client.get(f"http://127.0.0.1:{port}/api/v1/health/ready").is_success:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
    raise RuntimeError("Temporary API did not become ready")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=3000)
    arguments = parser.parse_args()
    if not all(1024 <= port <= 65535 for port in (arguments.api_port, arguments.frontend_port)):
        parser.error("Ports must be between 1024 and 65535")
    # Build/start the frontend with BACKEND_INTERNAL_URL matching the API port.
    # Refuse an existing API rather than silently test against its database.
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", arguments.api_port))
        except OSError:
            raise SystemExit(
                "Stop the existing local API before running isolated browser checks"
            ) from None
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise SystemExit("pnpm must be installed")
    settings = get_settings()
    test_url = (
        make_url(settings.database_url.get_secret_value())
        .set(database=f"interview_prep_{uuid4().hex[:12]}_test")
        .render_as_string(hide_password=False)
    )
    asyncio.run(prepare_test_database(test_url))
    environment = {
        **os.environ,
        "DATABASE_URL": test_url,
        "APP_ENV": "test",
        "AUTH_ENABLED": "false",
        "FRONTEND_URL": f"http://127.0.0.1:{arguments.frontend_port}",
        "FRONTEND_ORIGIN": f"http://127.0.0.1:{arguments.frontend_port}",
        "ALLOWED_ORIGINS": f'["http://127.0.0.1:{arguments.frontend_port}"]',
    }
    process: subprocess.Popen[bytes] | None = None
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                "backend/alembic.ini",
                "upgrade",
                "head",
            ],
            cwd=ROOT,
            env=environment,
            check=True,
            timeout=60,
        )
        subprocess.run(
            [sys.executable, "-m", "interview_prep.modules.questions.seed", "--apply"],
            cwd=ROOT,
            env=environment,
            check=True,
            timeout=60,
        )
        cache = ROOT / ".cache"
        cache.mkdir(exist_ok=True)
        with (cache / "browser-api.log").open("wb") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "interview_prep.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(arguments.api_port),
                    "--no-proxy-headers",
                    "--no-access-log",
                ],
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=log,
            )
            wait_for_api(process, arguments.api_port)
            print(
                "Running browser checks with a fresh isolated PostgreSQL database.",
                flush=True,
            )
            subprocess.run([pnpm, "test:e2e"], cwd=ROOT, env=environment, check=True, timeout=180)
    finally:
        if process is not None:
            stop_owned_process(process)
        asyncio.run(drop_created_database(test_url))


if __name__ == "__main__":
    main()
