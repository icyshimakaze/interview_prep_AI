"""Fixed staging frontend rollback plus the independent Render stop guard."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from staging_stop_watchdog import KEY_FILE, GuardError, RenderAPI, run_guard

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/phase-4-3"
SOURCE = CACHE / "release-source"
CLI = CACHE / "tooling/node_modules/vercel/dist/vc.js"
AUTH = CACHE / "vercel-auth"
PROJECT_ID = "prj_kQtaYbGd25ulIufNKnenHw7MG2bN"
TEAM_ID = "team_vyOtLBqMjk5sQ9DTmzCcbwiN"
TEAM_SLUG = "icy-shimakaze"
PROJECT_NAME = "interview-prep-ai-auth-staging"
ROLLBACK_ID = "dpl_5AdLnFE7p2eKzrVJ7sbVNEYJcHTX"
FRONTEND_MARGIN_SECONDS = 180
WINDOW = CACHE / "window.json"


def validate_link(value: object) -> None:
    if not isinstance(value, dict) or any(
        value.get(key) != expected
        for key, expected in {
            "projectId": PROJECT_ID,
            "orgId": TEAM_ID,
            "projectName": PROJECT_NAME,
        }.items()
    ):
        raise GuardError("Staging Vercel link mismatch")


def cli_arguments(arguments: list[str]) -> list[str]:
    return [
        "node",
        str(CLI),
        *arguments,
        "--cwd",
        str(SOURCE),
        "--global-config",
        str(AUTH),
        "--scope",
        TEAM_SLUG,
        "--non-interactive",
    ]


def cli_call(arguments: list[str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cli_arguments(arguments),
            cwd=ROOT,
            env={**os.environ, "VERCEL_TELEMETRY_DISABLED": "1"},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise GuardError("Staging Vercel command failed") from None


def check_context() -> None:
    for path in (
        SOURCE / ".vercel/project.json",
        SOURCE / "frontend/.vercel/project.json",
    ):
        validate_link(json.loads(path.read_text(encoding="utf-8")))
    identity = cli_call(["whoami", "--format", "json"])
    if identity.returncode:
        raise GuardError("Staging Vercel login unavailable")
    account = json.loads(identity.stdout)
    if account.get("team", {}).get("id") != TEAM_ID or account.get("plan") != "hobby":
        raise GuardError("Staging Hobby team mismatch")
    project = cli_call(["project", "inspect"])
    if project.returncode or PROJECT_ID not in project.stdout + project.stderr:
        raise GuardError("Staging Vercel project not verified")


def frontend_status(state: str) -> None:
    path = CACHE / "frontend-rollback-status.json"
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(
            json.dumps({"state": state, "project_id": PROJECT_ID, "rollback_id": ROLLBACK_ID}),
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError as error:
        # A monitor holding this file must not prevent the rollback itself.
        print(
            json.dumps(
                {
                    "event": "frontend_status_write_unavailable",
                    "error_type": type(error).__name__,
                    "errno": error.errno,
                    "rollback_continues": True,
                }
            ),
            flush=True,
        )


def restore_frontend(deadline: datetime, stop_clock: float, early: threading.Event) -> None:
    frontend_status("scheduled")
    while True:
        left = min(
            (deadline - datetime.now(UTC)).total_seconds(),
            stop_clock - time.monotonic(),
        )
        if left <= FRONTEND_MARGIN_SECONDS or early.is_set():
            break
        early.wait(min(5, left - FRONTEND_MARGIN_SECONDS))
    try:
        check_context()
        result = cli_call(["rollback", ROLLBACK_ID, "--yes", "--timeout", "60s"], timeout=70)
        if result.returncode:
            raise GuardError("Frontend rollback command failed")
        # Close future builds as well as restoring the retained canonical alias.
        for key in ("GOOGLE_AUTH_ENABLED", "GITHUB_AUTH_ENABLED"):
            result = subprocess.run(
                cli_arguments(
                    [
                        "env",
                        "add",
                        key,
                        "--environment",
                        "production",
                        "--type",
                        "config",
                        "--force",
                        "--yes",
                        "--project",
                        PROJECT_ID,
                    ]
                ),
                input="false",
                capture_output=True,
                text=True,
                cwd=ROOT,
                env={**os.environ, "VERCEL_TELEMETRY_DISABLED": "1"},
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                check=False,
            )
            if result.returncode:
                raise GuardError("Future social admission closure failed")
        frontend_status("rollback_command_completed_and_future_social_flags_disabled")
    except (GuardError, OSError, ValueError, subprocess.TimeoutExpired):
        frontend_status("failed_requires_operator_follow_up")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--arm", action="store_true")
    parser.add_argument("--deadline")
    args = parser.parse_args()
    try:
        check_context()
        api = RenderAPI(KEY_FILE.read_text(encoding="utf-8").strip())
        service = api.service()
        if service["suspended"] != "suspended":
            raise GuardError("Stage must be suspended before arming")
        if args.check:
            print(
                json.dumps(
                    {
                        "state": "verified_read_only",
                        "project_id": PROJECT_ID,
                        "render_state": "suspended",
                        "plan": "hobby",
                    }
                )
            )
            return 0
        if not args.deadline:
            raise GuardError("Absolute deadline required")
        deadline = datetime.fromisoformat(args.deadline)
        if deadline.tzinfo is None:
            raise GuardError("Timezone-aware deadline required")
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        if not FRONTEND_MARGIN_SECONDS < remaining <= 1800:
            raise GuardError("Invalid bounded window")
        early = threading.Event()
        stop_clock = time.monotonic() + remaining
        WINDOW.write_text(
            json.dumps(
                {
                    "started_at_utc": datetime.now(UTC).isoformat(),
                    "deadline_utc": deadline.isoformat(),
                    "pid": os.getpid(),
                    "test_cleanup_margin_seconds": 240,
                    "frontend_rollback_margin_seconds": FRONTEND_MARGIN_SECONDS,
                    "render_stop_margin_seconds": 120,
                }
            ),
            encoding="utf-8",
        )
        thread = threading.Thread(target=restore_frontend, args=(deadline, stop_clock, early))
        thread.start()
        try:
            run_guard(api, deadline)
        finally:
            early.set()
            thread.join(timeout=150)
        return 0
    except (GuardError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "state": "failed",
                    "error": "Fixed staging window guard check failed",
                    "error_type": type(error).__name__,
                    "errno": error.errno if isinstance(error, OSError) else None,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
