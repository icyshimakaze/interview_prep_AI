import httpx
from conftest import test_settings as make_settings
from sqlalchemy.ext.asyncio import AsyncEngine
from test_auth import ISSUER, jwk, signed_token
from test_deployment import account_production_settings

from interview_prep.ai.xkiro import XkiroProvider
from interview_prep.main import create_app
from interview_prep.modules.identity.verification import TokenVerifier


async def test_production_signed_account_failure_preserves_demo_and_owned_context(
    database: AsyncEngine,
) -> None:
    # Test-only DB TLS override: the separate container harness verifies real TLS.
    settings = account_production_settings(auth_issuer=ISSUER, ai_max_retries=0).model_copy(
        update={
            "database_url": make_settings(
                database.url.render_as_string(hide_password=False)
            ).database_url,
            "database_ssl_mode": "disable",
        }
    )
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        if request.url.path == "/.well-known/jwks.json":
            return httpx.Response(200, json={"keys": [jwk()]})
        calls += 1
        return httpx.Response(503, text="private-upstream-content")

    app = create_app(settings)
    gateway = {
        "x-interview-prep-gateway": settings.backend_proxy_secret.get_secret_value(),
        "x-interview-prep-client-ip": "192.0.2.60",
        "Origin": "https://app.example.test",
    }
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as upstream:
            app.state.token_verifier = TokenVerifier(settings, upstream)
            app.state.ai_provider = XkiroProvider(upstream, settings)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="https://app.example.test",
                headers={
                    **gateway,
                    "Authorization": "Bearer "
                    + signed_token(
                        overrides={"azp": "https://app.example.test"},
                    ),
                },
            ) as account:
                assert (await account.post("/api/v1/account/session", json={})).status_code == 200
                target = await account.post(
                    "/api/v1/account/targets",
                    json={
                        "title": "Synthetic role",
                        "description": "Python required; SQL preferred.",
                    },
                )
                assert target.status_code == 201
                options = (await account.get("/api/v1/account/ai/options")).json()
                path = f"/api/v1/account/ai/targets/{target.json()['id']}"
                failed = await account.post(
                    path,
                    json={
                        "consent": True,
                        "provider_version": options["version"],
                    },
                )
                assert failed.status_code == 503 and calls == 1
                assert "private-upstream-content" not in failed.text
                assert (
                    await account.get(f"/api/v1/account/targets/{target.json()['id']}")
                ).status_code == 200
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="https://app.example.test",
                headers=gateway,
            ) as demo:
                assert (await demo.post("/api/v1/demo/sessions", json={})).status_code == 200
                options_response = await demo.get("/api/v1/demo/assessments/options")
                assert options_response.status_code == 200
                assert options_response.json()["conceptual_provider"] == "MockAIProvider"
                assert (await demo.get("/api/v1/account/dashboard")).status_code == 401
                assert calls == 1  # A real-provider outage never dispatches demo AI.
