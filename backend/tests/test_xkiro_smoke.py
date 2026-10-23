from unittest.mock import patch

import check_xkiro
import httpx
import pytest
from test_xkiro import settings, wire


@pytest.mark.parametrize(
    "payload,expected",
    [('{"status":"ok"}', "passed"), ('{"status":"wrong"}', "failed"), ("", "failed")],
)
async def test_opt_in_smoke_uses_one_small_synthetic_free_request(
    payload: str,
    expected: str,
) -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        import json

        body = json.loads(request.content)
        assert body["model"] == check_xkiro.FREE_MODEL
        assert body["max_tokens"] == 128
        assert body["response_format"] == {"type": "json_object"}
        assert body["messages"] == [
            {"role": "user", "content": 'Return only JSON: {"status":"ok"}'}
        ]
        return httpx.Response(200, json=wire(payload))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    with (
        patch.object(check_xkiro, "get_settings", return_value=settings()),
        patch.object(
            httpx,
            "AsyncClient",
            return_value=client,
        ),
    ):
        result = await check_xkiro.check()
    assert result["result"] == expected and calls == 1
    assert "fictional-unit-test-credential" not in str(result)


async def test_smoke_skips_without_configured_key() -> None:
    with patch.object(check_xkiro, "get_settings", return_value=settings(xkiro_api_key="")):
        assert (await check_xkiro.check())["result"] == "skipped"
