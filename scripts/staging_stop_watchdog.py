"""Independent, fixed-target Render stop guard. Never resumes or deploys a service."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

SERVICE_ID = "srv-dbf34mbrjlhs739d2grg"
WORKSPACE_ID = "tea-da7fkouk1f9s73d90ln0"
REPOSITORY = "https://github.com/icyshimakaze/interview-prep-ai-auth-staging"
BRANCH = "phase3/isolated-staging"
SERVICE_URL = f"https://api.render.com/v1/services/{SERVICE_ID}"
STOP_MARGIN_SECONDS = 120
ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRECTORY = ROOT / ".cache" / "phase-4-3"
KEY_FILE = PRIVATE_DIRECTORY / "render-api-key.local"
STATUS_FILE = PRIVATE_DIRECTORY / "watchdog-status.json"


class GuardError(Exception):
    """Messages are fixed local labels; provider bodies and credentials are omitted."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        raise GuardError("API redirect refused")


def validate_service(service: object) -> dict[str, object]:
    if not isinstance(service, dict):
        raise GuardError("Unexpected service metadata")
    metadata = cast(dict[str, object], service)
    expected = {
        "id": SERVICE_ID,
        "ownerId": WORKSPACE_ID,
        "repo": REPOSITORY,
        "branch": BRANCH,
        "type": "web_service",
        "autoDeploy": "no",
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise GuardError("Staging identity mismatch")
    details = metadata.get("serviceDetails")
    if not isinstance(details, dict) or details.get("plan") != "free":
        raise GuardError("Free staging plan not verified")
    state = metadata.get("suspended")
    if not isinstance(state, str) or state not in {"suspended", "not_suspended"}:
        raise GuardError("Unknown suspension state")
    return metadata


class StopAPI(Protocol):
    def service(self) -> dict[str, object]: ...

    def suspend(self) -> None: ...


class RenderAPI:
    def __init__(self, key: str) -> None:
        if len(key) < 20 or any(character.isspace() for character in key):
            raise GuardError("API credential missing or malformed")
        self._key = key
        self._opener = urllib.request.build_opener(NoRedirect())

    def _request(self, method: str) -> bytes:
        # No caller-controlled host, path, service ID, headers, or redirects.
        url = SERVICE_URL if method == "GET" else f"{SERVICE_URL}/suspend"
        request = urllib.request.Request(
            url,
            method=method,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Accept": "application/json",
            },
        )
        try:
            with self._opener.open(request, timeout=10) as response:
                # Render also returns 200 for an idempotent stop of a paused
                # service. The guard still requires a separate state readback.
                expected = {200} if method == "GET" else {200, 202, 204}
                if response.status not in expected:
                    raise GuardError("Unexpected Render response status")
                content = response.read(1_048_577)
                if len(content) > 1_048_576:
                    raise GuardError("Render response size limit exceeded")
                return cast(bytes, content)
        except urllib.error.HTTPError as error:
            raise GuardError(f"Render HTTP {error.code}") from None
        except (OSError, urllib.error.URLError):
            raise GuardError("Render network request failed") from None

    def service(self) -> dict[str, object]:
        try:
            data: object = json.loads(self._request("GET"))
        except (ValueError, UnicodeError):
            raise GuardError("Invalid Render JSON response") from None
        return validate_service(data)

    def suspend(self) -> None:
        self._request("POST")


def utc_now() -> datetime:
    return datetime.now(UTC)


def write_status(status: dict[str, object]) -> None:
    PRIVATE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    temporary = STATUS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATUS_FILE)


def run_guard(
    api: StopAPI,
    deadline: datetime,
    *,
    now: Callable[[], datetime] = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    report: Callable[[dict[str, object]], None] = write_status,
) -> None:
    if deadline.tzinfo is None:
        raise GuardError("Deadline must include a timezone")
    remaining = (deadline - now()).total_seconds()
    if not STOP_MARGIN_SECONDS < remaining <= 1800:
        raise GuardError("Deadline must be within 30 minutes with a stop margin")
    hard_stop = monotonic() + remaining
    initial = validate_service(api.service())
    if initial["suspended"] != "suspended":
        raise GuardError("Arm only while staging is suspended")
    base: dict[str, object] = {
        "service_id": SERVICE_ID,
        "workspace_id": WORKSPACE_ID,
        "deadline_utc": deadline.astimezone(UTC).isoformat(),
        "stop_margin_seconds": STOP_MARGIN_SECONDS,
        "pid": os.getpid(),
    }

    status_warning_emitted = False

    def publish(status: dict[str, object]) -> None:
        nonlocal status_warning_emitted
        # A Windows reader may deny atomic replacement while holding this file.
        # Monitoring must never interrupt the independent suspension deadline.
        try:
            report(status)
            status_warning_emitted = False
        except OSError as error:
            if status_warning_emitted:
                return
            status_warning_emitted = True
            print(
                json.dumps(
                    {
                        "event": "status_write_unavailable",
                        "error_type": type(error).__name__,
                        "errno": error.errno,
                        "suspension_guard_continues": True,
                    }
                ),
                flush=True,
            )

    try:
        while True:
            # Either clock reaching the boundary triggers stop; clock rollback
            # cannot lengthen the window. Heartbeats contain no credentials.
            left = min((deadline - now()).total_seconds(), hard_stop - monotonic())
            if left <= STOP_MARGIN_SECONDS:
                break
            publish({**base, "state": "armed", "heartbeat_utc": now().isoformat()})
            sleep(min(5, left - STOP_MARGIN_SECONDS))
        last_error = "Suspension not confirmed"
        while True:
            try:
                service = validate_service(api.service())
                if service["suspended"] == "suspended":
                    publish(
                        {
                            **base,
                            "state": "suspended",
                            "verified_at_utc": now().isoformat(),
                        }
                    )
                    return
                api.suspend()
                publish({**base, "state": "suspend_requested"})
            except GuardError as error:
                # Error labels come only from this module; no provider bodies.
                last_error = str(error)
                publish({**base, "state": "retrying", "error": last_error})
                if last_error in {
                    "Staging identity mismatch",
                    "Free staging plan not verified",
                }:
                    raise
            if min((deadline - now()).total_seconds(), hard_stop - monotonic()) <= 0:
                raise GuardError(last_error)
            sleep(2)
    except BaseException:
        publish(
            {
                **base,
                "state": "failed",
                "error": "Stop guard did not confirm suspension",
            }
        )
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only identity/auth check")
    mode.add_argument("--arm", action="store_true", help="Wait independently, then suspend staging")
    parser.add_argument(
        "--deadline", help="Absolute timezone-aware ISO deadline, at most 30 min away"
    )
    args = parser.parse_args()
    try:
        key = os.environ.get("RENDER_API_KEY", "")
        if not key and KEY_FILE.is_file():
            key = KEY_FILE.read_text(encoding="utf-8").strip()
        api = RenderAPI(key)
        if args.check:
            service = api.service()
            print(json.dumps({"verified_service": SERVICE_ID, "state": service["suspended"]}))
        else:
            if not args.deadline:
                raise GuardError("An absolute deadline is required")
            try:
                deadline = datetime.fromisoformat(args.deadline)
            except ValueError:
                raise GuardError("Invalid deadline format") from None
            run_guard(api, deadline)
    except GuardError as error:
        print(json.dumps({"state": "failed", "error": str(error)}))
        return 1
    except (OSError, ValueError):
        print(json.dumps({"state": "failed", "error": "Local guard configuration failed"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
