"""Run auth/backend checks only on newly created throwaway PostgreSQL containers."""

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "postgres:18-bookworm@sha256:afc7e2d441324c0388fa80c3d24f733b4194a4eb7f47dd8ee2b08eb1a24a647c"
)


def docker(*arguments: str) -> str:
    result = subprocess.run(
        ["docker", *arguments], capture_output=True, text=True, timeout=180, check=False
    )
    if result.returncode:
        raise RuntimeError("Disposable auth-test Docker operation failed; raw diagnostics withheld")
    return result.stdout.strip()


def run(arguments: list[str], environment: dict[str, str], cwd: Path = ROOT) -> None:
    print("Running: " + " ".join(arguments), flush=True)
    subprocess.run(arguments, env=environment, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=(
            "generate",
            "proof",
            "backend",
            "browser",
            "android",
            "demo",
            "continuity",
            "social",
            "social-browser",
            "social-android",
            "live-social",
            "recovery",
            "all",
        ),
        default="proof",
    )
    phase = parser.parse_args().phase
    suffix = uuid4().hex[:12]
    name = f"interview-prep-auth-{suffix}"
    database = f"interview_prep_{suffix}_test"
    password = secrets.token_hex(24)
    if not re.fullmatch(r"interview-prep-auth-[a-f0-9]{12}", name):
        raise ValueError("Invalid owned test resource")
    started = False
    try:
        docker(
            "run",
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
            "/tmp:rw,noexec,nosuid,size=32m",
            "-p",
            "127.0.0.1::5432",
            "-e",
            f"POSTGRES_PASSWORD={password}",
            "-e",
            f"POSTGRES_DB={database}",
            IMAGE,
            "-c",
            "shared_buffers=16MB",
            "-c",
            "max_connections=50",
            "-c",
            "work_mem=1MB",
            "-c",
            "maintenance_work_mem=16MB",
        )
        started = True
        address = docker("port", name, "5432/tcp")
        match = re.fullmatch(r"127\.0\.0\.1:(\d+)", address)
        if not match:
            raise RuntimeError("Disposable database must be loopback-only")
        port = match.group(1)
        for _ in range(60):
            result = subprocess.run(
                ["docker", "exec", name, "pg_isready", "-U", "postgres"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Disposable PostgreSQL did not become ready")
        # Explicit targets override dotenv; never read or connect to an existing application DB.
        from test_support import mock_environment

        environment = {
            **mock_environment(),
            "AUTH_PROVIDER": "clerk",
            "AUTH_ISSUER": "",
            "AUTH_JWKS_ENDPOINT": "",
            "BETTER_AUTH_SECRET": "",
            "AUTH_DATABASE_URL": "",
            "AUTH_RATE_LIMIT_KEY": "",
            "BETTER_AUTH_URL": "",
            "DATABASE_URL": f"postgresql+asyncpg://postgres:{password}@127.0.0.1:{port}/{database}",
            "TEST_DATABASE_URL": f"postgresql+asyncpg://postgres:{password}@127.0.0.1:{port}/{database}",
            "TEST_AUTH_DATABASE_URL": f"postgresql://postgres:{password}@127.0.0.1:{port}/{database}",
            "AUTH_RECOVERY_TEST_CONTAINER": name,
        }
        python = (
            str(ROOT / "backend/.venv/Scripts/python.exe") if os.name == "nt" else sys.executable
        )
        if phase == "generate":
            run(
                ["node", "scripts/auth-bridge.mjs", "--generate"],
                environment,
                ROOT / "frontend",
            )
        else:
            run(
                [python, "-m", "alembic", "upgrade", "head"],
                environment,
                ROOT / "backend",
            )
            if phase == "recovery":
                run([python, "scripts/check_auth_recovery.py"], environment)
            if phase not in {
                "browser",
                "android",
                "demo",
                "recovery",
                "social-browser",
                "social-android",
                "live-social",
            }:
                run(
                    [
                        python,
                        "-m",
                        "pytest",
                        "-q",
                        *(
                            ["tests/test_auth_continuity.py", "tests/test_auth_recovery_guards.py"]
                            if phase == "continuity"
                            else ["tests/test_social_auth.py"]
                            if phase == "social"
                            else ["tests/test_better_auth.py"]
                        ),
                    ],
                    environment,
                    ROOT / "backend",
                )
            if phase in {"browser", "all"}:
                run([python, "scripts/better_auth_browser.py"], environment)
            if phase == "android":
                run([python, "scripts/better_auth_browser.py", "--android"], environment)
            if phase in {"social-browser", "social-android"}:
                run(
                    [
                        python,
                        "scripts/better_auth_browser.py",
                        "--social",
                        *(["--android"] if phase == "social-android" else []),
                    ],
                    environment,
                )
            if phase == "demo":
                run([python, "scripts/better_auth_browser.py", "--demo"], environment)
            if phase == "live-social":
                run([python, "scripts/local_social.py"], environment)
            if phase in {"backend", "all"}:
                failures: list[str] = []
                for check in ("lint", "tests", "migrations"):
                    try:
                        run(
                            [python, "scripts/check_backend.py", "--phase", check],
                            environment,
                        )
                    except subprocess.CalledProcessError:
                        failures.append(check)
                if failures:
                    raise RuntimeError("Backend gates failed: " + ", ".join(failures))
        print(json.dumps({"phase": phase, "result": "passed", "existing_databases_used": False}))
    finally:
        if started:
            docker("rm", "-f", name)
            print("Removed owned disposable auth-test container.", flush=True)


if __name__ == "__main__":
    main()
