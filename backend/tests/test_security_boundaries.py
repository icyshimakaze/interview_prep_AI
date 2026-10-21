import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest
from conftest import test_settings as make_settings
from cryptography import x509
from cryptography.x509.oid import NameOID
from fastapi import FastAPI
from starlette.types import Message, Receive, Scope, Send
from test_auth import ISSUER, signed_token

from interview_prep.ai.errors import InvalidProviderOutput
from interview_prep.ai.transport import request_json
from interview_prep.core import request_security
from interview_prep.core.request_security import JSON_BYTES, RequestSecurityMiddleware
from interview_prep.modules.identity.verification import AuthenticationUnavailable, TokenVerifier


def test_outbound_tls_does_not_trust_compromised_emsign_root() -> None:
    # GHSA-6q48-6c7w-9gw2: validate the actual trust store used by outbound HTTP,
    # not merely a package version string. Environment CA overrides are disabled.
    certificates = httpx.create_ssl_context(trust_env=False).get_ca_certs(binary_form=True)
    assert len(certificates) > 100
    common_names = {
        attribute.value
        for certificate in certificates
        for attribute in x509.load_der_x509_certificate(certificate).subject.get_attributes_for_oid(
            NameOID.COMMON_NAME
        )
    }
    assert "emSign ECC Root CA - G3" not in common_names


@pytest.mark.parametrize("mime", ["application/json", "text/plain", "application/octet-stream"])
async def test_oversized_unauthenticated_body_rejected_before_json(
    client: httpx.AsyncClient, mime: str
) -> None:
    result = await client.post(
        "/api/v1/account/session",
        content=b"x" * (JSON_BYTES + 1),
        headers={"Content-Type": mime},
    )
    assert result.status_code == 413
    assert result.json()["code"] == "request_size"
    assert result.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("length", [None, "1"])
async def test_chunked_or_understated_body_cannot_bypass_limit(
    client: httpx.AsyncClient, length: str | None
) -> None:
    async def stream() -> AsyncIterator[bytes]:
        yield b" " * JSON_BYTES
        yield b"{}"

    result = await client.post(
        "/api/v1/account/session",
        content=stream(),
        headers={"Content-Length": length} if length else {},
    )
    assert result.status_code == 413


async def test_body_deadline_and_busy_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(request_security, "READ_SECONDS", 0.01)
    entered = False

    async def target(scope: Scope, receive: Receive, send: Send) -> None:
        nonlocal entered
        entered = True

    middleware = RequestSecurityMiddleware(target)
    messages: list[Message] = []

    async def slow() -> Message:
        await asyncio.sleep(0.1)
        return {"type": "http.request", "body": b"{}", "more_body": False}

    async def send(message: Message) -> None:
        messages.append(message)

    scope = {"type": "http", "method": "POST", "path": "/api/v1/demo/sessions", "headers": []}
    await middleware(scope, slow, send)
    assert messages[0]["status"] == 408 and not entered
    messages.clear()
    for _ in range(32):
        await middleware.slots.acquire()
    await middleware(scope, slow, send)
    assert messages[0]["status"] == 503 and not entered


async def test_compressed_requests_rejected_including_upload_routes(
    client: httpx.AsyncClient,
) -> None:
    for path in ("/api/v1/account/session", "/api/v1/account/resumes", "/api/v1/demo/projects/zip"):
        response = await client.post(path, content=b"encoded", headers={"Content-Encoding": "gzip"})
        assert response.status_code == 415


async def test_unhandled_exception_cannot_escape_to_server_logs(
    app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    @app.get("/private-failure")
    async def failure() -> None:
        raise RuntimeError("PRIVATE_RESUME_TEXT_AND_PROVIDER_SECRET")

    # Default raise_app_exceptions=True would reveal Starlette's re-raise.
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as http:
        response = await http.get("/private-failure")
    assert response.status_code == 500
    assert "PRIVATE_RESUME" not in response.text + caplog.text
    assert response.json()["request_id"] in caplog.text


class UnreadableBody(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        raise AssertionError("Encoded content must be rejected before reading/decompression")
        yield b""  # Marks this method as an async iterator.


async def test_provider_and_jwks_reject_encoding_before_consuming_body() -> None:
    def transport(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=UnreadableBody())

    settings = make_settings().model_copy(update={"auth_enabled": True, "auth_issuer": ISSUER})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        with pytest.raises(InvalidProviderOutput):
            await request_json(http, "https://provider.test", {}, {}, 1, 0)
        with pytest.raises(AuthenticationUnavailable):
            await TokenVerifier(settings, http).verify(signed_token())


async def test_jwks_total_deadline_covers_slow_drip() -> None:
    class SlowBody(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            for _ in range(20):
                await asyncio.sleep(0.2)
                yield b" "

    settings = make_settings().model_copy(update={"auth_enabled": True, "auth_issuer": ISSUER})
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=SlowBody()))
    ) as http:
        verifier = TokenVerifier(settings, http)
        with pytest.raises(AuthenticationUnavailable):
            async with asyncio.timeout(3.8):
                await verifier.verify(signed_token())
        assert verifier.keys == {}
