import socket

import httpx
import pytest
from test_support import mock_environment, require_free_port


def test_test_environment_overrides_inherited_provider_and_identity_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "CLERK_SECRET_KEY",
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
    ):
        monkeypatch.setenv(name, "private-sentinel-not-a-real-credential")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    environment = mock_environment()
    assert environment["AI_PROVIDER"] == "mock"
    assert environment["APP_ENV"] == "test"
    assert environment["AUTH_ENABLED"] == "false"
    assert "private-sentinel-not-a-real-credential" not in environment.values()


def test_real_sync_http_is_blocked_before_network_access() -> None:
    with httpx.Client(trust_env=False) as client:
        with pytest.raises(AssertionError, match="Live HTTP is forbidden"):
            client.get("https://api.openai.com/v1/responses")


async def test_real_async_http_is_blocked_but_in_memory_adapter_tests_work() -> None:
    async with httpx.AsyncClient(trust_env=False) as client:
        with pytest.raises(AssertionError, match="Live HTTP is forbidden"):
            await client.post("https://api.openai.com/v1/responses", json={})
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"mock": True}))
    ) as local:
        assert (await local.get("https://provider.invalid")).json() == {"mock": True}


def test_browser_setup_refuses_occupied_ports_without_disrupting_listener() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(RuntimeError, match="unavailable"):
            require_free_port(port)
        assert listener.getsockname()[1] == port


@pytest.mark.parametrize("port", [0, 1023, 65536])
def test_browser_setup_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValueError, match="between"):
        require_free_port(port)
