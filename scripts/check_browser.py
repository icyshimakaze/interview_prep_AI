"""Build and test the real app with an owned database and temporary local servers."""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

from check_backend import drop_created_database, prepare_test_database
from sqlalchemy.engine import make_url
from test_support import (
    mock_environment,
    require_free_port,
    stop_owned_process,
    wait_for_server,
)

from interview_prep.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=3000)
    parser.add_argument("--skip-build", action="store_true", help="Use a matching production build")
    parser.add_argument("playwright_args", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if arguments.api_port == arguments.frontend_port:
        parser.error("API and frontend must use different ports")
    for port in (arguments.api_port, arguments.frontend_port):
        require_free_port(port)
    pnpm, node = shutil.which("pnpm"), shutil.which("node")
    if pnpm is None or node is None:
        raise SystemExit("node and pnpm must be installed")
    os.environ.update(mock_environment())
    get_settings.cache_clear()
    api = f"http://127.0.0.1:{arguments.api_port}"
    frontend = f"http://127.0.0.1:{arguments.frontend_port}"
    environment = {
        **os.environ,
        "INTERVIEW_WORKER_ENABLED": "true",
        "BACKEND_INTERNAL_URL": api,
        "BACKEND_URL": api,
        "FRONTEND_URL": frontend,
        "FRONTEND_ORIGIN": frontend,
        "PORT": str(arguments.frontend_port),
        "FRONTEND_HOSTNAME": "127.0.0.1",
        "ALLOWED_ORIGINS": json.dumps([frontend]),
    }
    if not arguments.skip_build:
        subprocess.run([pnpm, "build"], cwd=ROOT, env=environment, check=True, timeout=300)
    # Next rewrites are fixed at build time; never silently use a different API.
    manifest = ROOT / "frontend/.next/routes-manifest.json"
    routes = json.loads(manifest.read_text(encoding="utf-8"))
    expected = f"{api}/api/v1/:path*"
    if not any(r["destination"] == expected for r in routes["rewrites"]["afterFiles"]):
        raise SystemExit("Production build uses another backend origin; rerun without --skip-build")
    settings = get_settings()
    test_url = (
        make_url(settings.database_url.get_secret_value())
        .set(database=f"interview_prep_{uuid4().hex[:12]}_test")
        .render_as_string(hide_password=False)
    )
    asyncio.run(prepare_test_database(test_url))
    environment["DATABASE_URL"] = test_url
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    try:
        with ExitStack() as resources:
            for command in (
                [
                    sys.executable,
                    "-m",
                    "alembic",
                    "-c",
                    "backend/alembic.ini",
                    "upgrade",
                    "head",
                ],
                [
                    sys.executable,
                    "-m",
                    "interview_prep.modules.questions.seed",
                    "--apply",
                ],
            ):
                subprocess.run(command, cwd=ROOT, env=environment, check=True, timeout=60)
            for name, command, readiness in (
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
                        str(arguments.api_port),
                        "--no-proxy-headers",
                        "--no-access-log",
                    ],
                    f"{api}/api/v1/health/ready",
                ),
                ("frontend", [node, "scripts/start_frontend.mjs"], frontend),
            ):
                log = resources.enter_context((cache / f"browser-{name}.log").open("wb"))
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = subprocess.CREATE_NO_WINDOW
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=environment,
                    stdout=log,
                    stderr=log,
                    creationflags=creation_flags,
                )
                resources.callback(stop_owned_process, process)
                wait_for_server(process, readiness)
            subprocess.run(
                [sys.executable, "scripts/smoke_stack.py"],
                cwd=ROOT,
                env=environment,
                check=True,
                timeout=45,
            )
            extras = arguments.playwright_args
            if extras[:1] == ["--"]:
                extras = extras[1:]
            print(
                "Browser checks: fresh PostgreSQL, production frontend, MockAIProvider.",
                flush=True,
            )
            subprocess.run(
                [pnpm, "test:e2e", *extras],
                cwd=ROOT,
                env=environment,
                check=True,
                timeout=600,
            )
    finally:
        asyncio.run(drop_created_database(test_url))
    print("Browser checks passed; owned servers stopped and disposable database removed.")


if __name__ == "__main__":
    main()
