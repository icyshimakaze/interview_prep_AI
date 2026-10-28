"""Stop-guard acceptance checks use synthetic metadata, clocks and HTTP responses."""

import io
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from email.message import Message
from unittest.mock import Mock, patch

import pytest
from staging_stop_watchdog import (
    BRANCH,
    REPOSITORY,
    SERVICE_ID,
    SERVICE_URL,
    STOP_MARGIN_SECONDS,
    WORKSPACE_ID,
    GuardError,
    NoRedirect,
    RenderAPI,
    run_guard,
    validate_service,
)


def staging_metadata() -> dict[str, object]:
    return {
        "id": SERVICE_ID,
        "ownerId": WORKSPACE_ID,
        "repo": REPOSITORY,
        "branch": BRANCH,
        "type": "web_service",
        "autoDeploy": "no",
        "serviceDetails": {"plan": "free"},
        "suspended": "suspended",
    }


class FakeClock:
    def __init__(self, rollback: bool = False) -> None:
        self.start = datetime(2026, 10, 28, tzinfo=UTC)
        self.elapsed = 0.0
        self.rollback = rollback

    def now(self) -> datetime:
        offset = min(self.elapsed, 600) if self.rollback else 0
        return self.start + timedelta(seconds=self.elapsed - offset)

    def monotonic(self) -> float:
        return self.elapsed

    def sleep(self, seconds: float) -> None:
        assert 0 < seconds <= 5
        self.elapsed += seconds


class FakeAPI:
    def __init__(self, clock: FakeClock, transient_failure: bool = False) -> None:
        self.clock = clock
        self.reads = 0
        self.suspensions: list[float] = []
        self.transient_failure = transient_failure

    def service(self) -> dict[str, object]:
        self.reads += 1
        if self.transient_failure and self.reads == 2:
            raise GuardError("Render network request failed")
        value = staging_metadata()
        if self.reads > 1 and not self.suspensions:
            value["suspended"] = "not_suspended"
        return value

    def suspend(self) -> None:
        self.suspensions.append(self.clock.elapsed)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("id", "srv-dbdrrr9srm7s73cpdt6g"),
        ("ownerId", "another-workspace"),
        ("repo", "https://github.com/icyshimakaze/interview_prep_AI"),
        ("branch", "rebuild/professional-v2"),
        ("type", "cron_job"),
        ("autoDeploy", "yes"),
        ("serviceDetails", {"plan": "starter"}),
        ("suspended", "unrecognized"),
        ("suspended", {}),
    ],
)
def test_rejects_wrong_target_or_paid_plan(key: str, value: object) -> None:
    metadata = staging_metadata()
    metadata[key] = value
    with pytest.raises(GuardError):
        validate_service(metadata)


@pytest.mark.parametrize("rollback", [False, True])
def test_stops_early_verifies_state_and_clock_rollback_cannot_extend_window(rollback: bool) -> None:
    clock = FakeClock(rollback=rollback)
    api = FakeAPI(clock)
    states: list[dict[str, object]] = []
    run_guard(
        api,
        clock.start + timedelta(minutes=30),
        now=clock.now,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        report=states.append,
    )
    assert api.suspensions == [1800 - STOP_MARGIN_SECONDS]
    assert states[0]["state"] == "armed"
    assert states[-1]["state"] == "suspended"
    assert clock.elapsed < 1800


@pytest.mark.parametrize("permanent", [False, True])
def test_status_file_lock_cannot_prevent_suspension_or_expose_error_payload(
    permanent: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    reports: list[dict[str, object]] = []
    attempts = 0

    def locked_report(status: dict[str, object]) -> None:
        nonlocal attempts
        attempts += 1
        if permanent or attempts == 1:
            raise PermissionError(13, "synthetic-sensitive-payload-never-log")
        reports.append(status)

    run_guard(
        api,
        clock.start + timedelta(minutes=30),
        now=clock.now,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        report=locked_report,
    )
    assert api.suspensions == [1800 - STOP_MARGIN_SECONDS]
    assert api.reads >= 3
    assert clock.elapsed < 1800
    if not permanent:
        assert reports[-1]["state"] == "suspended"
    output = capsys.readouterr().out
    assert "status_write_unavailable" in output
    assert "synthetic-sensitive-payload-never-log" not in output


def test_recovers_from_transient_api_failure_without_claiming_success_early() -> None:
    clock = FakeClock()
    api = FakeAPI(clock, transient_failure=True)
    states: list[dict[str, object]] = []
    run_guard(
        api,
        clock.start + timedelta(minutes=30),
        now=clock.now,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        report=states.append,
    )
    assert any(state["state"] == "retrying" for state in states)
    assert api.suspensions == [1800 - STOP_MARGIN_SECONDS + 2]
    assert states[-1]["state"] == "suspended"


@pytest.mark.parametrize("seconds", [-1, 0, 120, 1801])
def test_rejects_invalid_window_before_any_api_access(seconds: int) -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    with pytest.raises(GuardError, match="Deadline"):
        run_guard(api, clock.start + timedelta(seconds=seconds), now=clock.now)
    assert api.reads == 0
    assert api.suspensions == []


def test_refuses_to_arm_on_an_already_running_service() -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    api.reads = 1
    with pytest.raises(GuardError, match="Arm only"):
        run_guard(api, clock.start + timedelta(minutes=30), now=clock.now)
    assert api.suspensions == []


def test_only_fixed_service_api_endpoints_are_used() -> None:
    api = RenderAPI("synthetic-render-credential-for-tests")
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.status = 200
    response.read.return_value = json.dumps(staging_metadata()).encode()
    with patch.object(api._opener, "open", return_value=response) as request:
        assert api.service()["id"] == SERVICE_ID
        assert request.call_args.args[0].full_url == SERVICE_URL
        assert request.call_args.args[0].method == "GET"
        assert request.call_args.kwargs == {"timeout": 10}
        response.status = 202
        response.read.return_value = b""
        api.suspend()
        assert request.call_args.args[0].full_url == f"{SERVICE_URL}/suspend"
        assert request.call_args.args[0].method == "POST"


def test_http_error_does_not_include_provider_body_or_credential() -> None:
    secret = "synthetic-render-credential-for-tests"
    api = RenderAPI(secret)
    error = urllib.error.HTTPError(SERVICE_URL, 401, secret, Message(), io.BytesIO(secret.encode()))
    with patch.object(api._opener, "open", side_effect=error):
        with pytest.raises(GuardError, match="^Render HTTP 401$") as caught:
            api.service()
    assert secret not in str(caught.value)


def test_redirect_cannot_forward_authorization_to_another_host() -> None:
    redirect = NoRedirect()
    with pytest.raises(GuardError, match="redirect refused"):
        redirect.redirect_request(
            urllib.request.Request(SERVICE_URL), None, 302, "", {}, "https://untrusted.invalid/"
        )


def test_failed_stop_is_reported_as_failure_at_the_hard_deadline() -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    states: list[dict[str, object]] = []
    with patch.object(api, "suspend", side_effect=GuardError("Render HTTP 503")):
        with pytest.raises(GuardError, match="503"):
            run_guard(
                api,
                clock.start + timedelta(minutes=30),
                now=clock.now,
                monotonic=clock.monotonic,
                sleep=clock.sleep,
                report=states.append,
            )
    assert clock.elapsed == 1800
    assert states[-1]["state"] == "failed"
    assert not any(state["state"] == "suspended" for state in states)


def test_changed_identity_never_receives_a_suspend_request() -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    changed = staging_metadata()
    changed["ownerId"] = "another-workspace"
    states: list[dict[str, object]] = []
    with patch.object(api, "service", side_effect=[staging_metadata(), changed]):
        with pytest.raises(GuardError, match="identity mismatch"):
            run_guard(
                api,
                clock.start + timedelta(minutes=30),
                now=clock.now,
                monotonic=clock.monotonic,
                sleep=clock.sleep,
                report=states.append,
            )
    assert api.suspensions == []
    assert states[-1]["state"] == "failed"


@pytest.mark.parametrize("status", [200, 204])
def test_idempotent_success_statuses_are_accepted(status: int) -> None:
    api = RenderAPI("synthetic-render-credential-for-tests")
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.status = status
    response.read.return_value = b""
    with patch.object(api._opener, "open", return_value=response):
        api.suspend()


def test_accepted_post_without_confirmed_suspension_is_not_success() -> None:
    clock = FakeClock()
    api = FakeAPI(clock)
    states: list[dict[str, object]] = []
    with patch.object(api, "suspend", return_value=None):
        with pytest.raises(GuardError, match="Suspension not confirmed"):
            run_guard(
                api,
                clock.start + timedelta(minutes=30),
                now=clock.now,
                monotonic=clock.monotonic,
                sleep=clock.sleep,
                report=states.append,
            )
    assert states[-1]["state"] == "failed"
    assert not any(state["state"] == "suspended" for state in states)
