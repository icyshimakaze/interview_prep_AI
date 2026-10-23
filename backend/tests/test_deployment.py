import ssl
from typing import Literal
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from interview_prep.ai.factory import create_provider
from interview_prep.ai.mock import MockAIProvider
from interview_prep.core.config import Settings
from interview_prep.core.gateway import GatewayMiddleware
from interview_prep.db.session import create_engine
from interview_prep.serve import listen_port

GATEWAY_SECRET = "unit-test-gateway-credential-longer-than-32-characters"


def production_settings(
    provider: Literal["mock", "xkiro", "ollama", "openai"] = "mock",
    auth: bool = False,
    secret: str = GATEWAY_SECRET,
    tls: Literal["disable", "verify-full"] = "verify-full",
    database_url: str = "postgresql+asyncpg://runtime:unit-only@localhost/unit_test",
) -> Settings:
    return Settings(
        _env_file=None,
        app_env="production",
        public_demo_only=True,
        database_url=SecretStr(database_url),
        database_ssl_mode=tls,
        backend_proxy_secret=SecretStr(secret),
        demo_rate_limit_key=SecretStr("unit-test-quota-key-longer-than-32-characters"),
        allowed_origins=["https://app.example.test"],
        auth_enabled=auth,
        ai_provider=provider,
        openai_api_key=SecretStr(""),
        openai_model="",
        interview_worker_enabled=False,
    )


async def test_public_production_demo_needs_no_ai_or_clerk_credentials() -> None:
    settings = production_settings()
    assert settings.secure_cookies
    assert settings.openai_api_key.get_secret_value() == ""
    async with httpx.AsyncClient() as client:
        assert isinstance(create_provider(settings, client), MockAIProvider)


@pytest.mark.parametrize("provider", ["xkiro", "ollama", "openai"])
def test_public_demo_rejects_remote_provider(
    provider: Literal["xkiro", "ollama", "openai"],
) -> None:
    with pytest.raises(ValidationError, match="PUBLIC_DEMO_ONLY"):
        production_settings(provider=provider)


def test_public_demo_rejects_account_authentication() -> None:
    with pytest.raises(ValidationError, match="PUBLIC_DEMO_ONLY"):
        production_settings(auth=True)


@pytest.mark.parametrize("secret", ["", "short", "x" * 257])
def test_production_requires_bounded_proxy_secret(secret: str) -> None:
    with pytest.raises(ValidationError, match="BACKEND_PROXY_SECRET"):
        production_settings(secret=secret)


def test_production_requires_verified_database_tls() -> None:
    with pytest.raises(ValidationError, match="DATABASE_SSL_MODE"):
        production_settings(tls="disable")


@pytest.mark.parametrize("parameter", ["sslmode=require", "channel_binding=require", "ssl=false"])
def test_rejects_libpq_tls_options_without_leaking_database_password(parameter: str) -> None:
    with pytest.raises(ValidationError) as error:
        production_settings(
            database_url=f"postgresql+asyncpg://x:private-sentinel@localhost/db?{parameter}"
        )
    assert "private-sentinel" not in str(error.value)


def test_database_engine_verifies_hostname_and_uses_bounded_pool() -> None:
    with patch("interview_prep.db.session.create_async_engine") as factory:
        create_engine(production_settings())
    arguments = factory.call_args.kwargs
    context = arguments["connect_args"]["ssl"]
    assert isinstance(context, ssl.SSLContext)
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    assert arguments["pool_size"] == 3 and arguments["max_overflow"] == 2


@pytest.mark.parametrize("port, expected", [(None, 8000), ("10000", 10000), ("65535", 65535)])
def test_platform_port(port: str | None, expected: int) -> None:
    assert listen_port(port) == expected


@pytest.mark.parametrize("port", ["", "0", "65536", "-1", "eight", " 8000", "１２３"])
def test_invalid_platform_port(port: str) -> None:
    with pytest.raises(ValueError, match="PORT"):
        listen_port(port)


async def inspect_request(request: Request) -> JSONResponse:
    return JSONResponse({"client": request.client.host if request.client else None})


def gateway_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/api/v1/demo/check", inspect_request, methods=["GET", "POST"]),
            Route("/api/v1/account/check", inspect_request),
            Route("/api/v1/health/ready", inspect_request),
            Route("/health", inspect_request),
        ]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://app.example.test"],
        allow_credentials=True,
        allow_methods=["POST"],
    )
    app.add_middleware(GatewayMiddleware, settings=production_settings())
    return app


@pytest.mark.parametrize(
    "secret, address",
    [
        ("", "192.0.2.1"),
        ("forged", "192.0.2.1"),
        (GATEWAY_SECRET, "192.0.2.1, 192.0.2.2"),
        (GATEWAY_SECRET, "invalid"),
        (GATEWAY_SECRET, ""),
    ],
)
async def test_gateway_rejects_direct_or_spoofed_calls(secret: str, address: str) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=gateway_app()), base_url="https://backend.example.test"
    ) as client:
        response = await client.get(
            "/api/v1/demo/check",
            headers={
                "x-interview-prep-gateway": secret,
                "x-interview-prep-client-ip": address,
                "x-forwarded-for": "192.0.2.99",
            },
        )
    assert response.status_code == 403
    assert response.json()["code"] == "gateway_required"
    assert GATEWAY_SECRET not in response.text


def account_production_settings(**updates: object) -> Settings:
    values = production_settings().model_dump()
    values.update(
        public_demo_only=False,
        auth_enabled=True,
        auth_issuer="https://clerk.example.test",
        ai_provider="xkiro",
        xkiro_api_key="fictional-production-test-key",
        backend_proxy_secret=GATEWAY_SECRET,
    )
    values.update(updates)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    "updates,message",
    [
        ({"xkiro_api_key": ""}, "XKIRO_API_KEY"),
        ({"auth_enabled": False}, "AUTH_ENABLED"),
        ({"auth_issuer": ""}, "trusted HTTPS issuer"),
        ({"backend_proxy_secret": "replace-with-a-generated-production-secret"}, "generated"),
        ({"database_url": "postgresql+asyncpg://runtime@localhost/db"}, "host, role and password"),
        (
            {"database_url": "postgresql+asyncpg://runtime:URL_ENCODED_PASSWORD@localhost/db"},
            "placeholder",
        ),
        ({"ai_provider": "openai", "openai_api_key": "", "openai_model": ""}, "OPENAI_API_KEY"),
        ({"ai_provider": "ollama", "ollama_model": ""}, "OLLAMA_MODEL"),
    ],
)
def test_production_selected_profile_requires_mandatory_settings(
    updates: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        account_production_settings(**updates)


async def test_production_real_account_provider_keeps_recruiter_demo_zero_key() -> None:
    from interview_prep.ai.xkiro import XkiroProvider

    configured = account_production_settings()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: pytest.fail("Provider selection must not send HTTP")
        )
    ) as client:
        assert isinstance(create_provider(configured, client), XkiroProvider)
        assert isinstance(create_provider(configured, client, demo=True), MockAIProvider)


async def test_gateway_uses_only_authenticated_client_address_and_keeps_accounts_closed() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=gateway_app()), base_url="https://backend.example.test"
    ) as client:
        headers = {
            "x-interview-prep-gateway": GATEWAY_SECRET,
            "x-interview-prep-client-ip": "2001:db8::1",
            "x-forwarded-for": "192.0.2.99",
        }
        response = await client.get("/api/v1/demo/check", headers=headers)
        assert response.status_code == 200 and response.json()["client"] == "2001:db8::1"
        assert (await client.get("/api/v1/account/check", headers=headers)).status_code == 403
        for path in ("/health", "/api/v1/health/ready"):
            assert (await client.get(path)).status_code == 200


async def test_production_preflight_allows_only_exact_frontend_origin() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=gateway_app()), base_url="https://backend.example.test"
    ) as client:
        for origin, status in [
            ("https://app.example.test", 200),
            ("https://other.example.test", 400),
        ]:
            response = await client.options(
                "/api/v1/demo/check",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert response.status_code == status
            assert response.headers.get("access-control-allow-origin") == (
                origin if status == 200 else None
            )
