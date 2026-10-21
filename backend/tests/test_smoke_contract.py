import httpx
import pytest
import smoke_stack

from interview_prep.api.health import SCHEMA_REVISION


@pytest.mark.parametrize("fault", [None, "landing", "schema", "forwarding"])
def test_connectivity_smoke_checks_landing_current_schema_and_same_origin_forwarding(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], fault: str | None
) -> None:
    seen: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if request.url.path == "/":
            return httpx.Response(
                200,
                text="<h1>Practice</h1>"
                + ("" if fault == "landing" else '<a href="/demo">Demo</a>'),
            )
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "service": "interview-prep-api"})
        if request.url.port == 13100 and fault == "forwarding":
            return httpx.Response(503, json={"code": "unavailable"})
        return httpx.Response(
            200,
            json={
                "database": "connected",
                "schema_revision": "obsolete" if fault == "schema" else SCHEMA_REVISION,
            },
        )

    original = httpx.Client

    def client(*, timeout: float, trust_env: bool) -> httpx.Client:
        assert timeout > 0 and not trust_env
        return original(transport=httpx.MockTransport(response))

    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:13100")
    monkeypatch.setenv("BACKEND_URL", "http://127.0.0.1:18100")
    monkeypatch.setattr(httpx, "Client", client)
    if fault:
        with pytest.raises((ValueError, httpx.HTTPStatusError)):
            smoke_stack.main()
        assert "PASS:" not in capsys.readouterr().out
    else:
        smoke_stack.main()
        assert "PASS:" in capsys.readouterr().out
        assert seen == [
            "http://127.0.0.1:13100",
            "http://127.0.0.1:18100/health",
            "http://127.0.0.1:18100/api/v1/health/ready",
            "http://127.0.0.1:13100/api/v1/health/ready",
        ]
