import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import staging_window_watchdog as coordinator
from staging_stop_watchdog import GuardError
from staging_window_watchdog import (
    PROJECT_ID,
    PROJECT_NAME,
    ROLLBACK_ID,
    TEAM_ID,
    cli_arguments,
    validate_link,
)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("projectId", "prj_wsxEcvVC17paXs5pco4K9eHwWKgd"),
        ("orgId", "other-team"),
        ("projectName", "production"),
    ],
)
def test_wrong_vercel_scope_is_rejected(key: str, value: str) -> None:
    link = {"projectId": PROJECT_ID, "orgId": TEAM_ID, "projectName": PROJECT_NAME}
    link[key] = value
    with pytest.raises(GuardError, match="link mismatch"):
        validate_link(link)


def test_rollback_uses_fixed_scope_and_no_credential_arguments() -> None:
    validate_link({"projectId": PROJECT_ID, "orgId": TEAM_ID, "projectName": PROJECT_NAME})
    command = cli_arguments(["rollback", ROLLBACK_ID, "--yes"])
    assert command[2:5] == ["rollback", ROLLBACK_ID, "--yes"]
    assert command[command.index("--scope") + 1] == "icy-shimakaze"
    assert "--global-config" in command
    assert "--token" not in command
    assert "prj_wsxEcvVC17paXs5pco4K9eHwWKgd" not in command


def test_locked_monitor_file_does_not_cancel_frontend_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(coordinator, "CACHE", tmp_path)
    monkeypatch.setattr(
        Path, "replace", Mock(side_effect=PermissionError(13, "synthetic-sensitive-payload"))
    )

    def valid_context() -> None:
        return None

    monkeypatch.setattr(coordinator, "check_context", valid_context)
    rollback = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
    flags = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(coordinator, "cli_call", rollback)
    monkeypatch.setattr(subprocess, "run", flags)
    early = threading.Event()
    early.set()
    coordinator.restore_frontend(datetime.now(UTC), time.monotonic(), early)
    rollback.assert_called_once_with(
        ["rollback", ROLLBACK_ID, "--yes", "--timeout", "60s"], timeout=70
    )
    assert flags.call_count == 2
    assert all(call.kwargs["input"] == "false" for call in flags.call_args_list)
    assert "synthetic-sensitive-payload" not in capsys.readouterr().out
