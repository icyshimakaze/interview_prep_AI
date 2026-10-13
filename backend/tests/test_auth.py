import json
import time
from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import jwt
import pytest
import pytest_asyncio
from conftest import test_settings as make_settings
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.main import create_app
from interview_prep.modules.context.models import Resume
from interview_prep.modules.identity.models import PrincipalStatus, User
from interview_prep.modules.identity.verification import (
    AuthenticationError,
    AuthenticationUnavailable,
    TokenVerifier,
)

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISSUER = "https://trusted-auth.example.test"


def jwk(key: rsa.RSAPrivateKey = KEY, kid: str = "trusted-1") -> dict[str, object]:
    data: dict[str, object] = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    return {**data, "kid": kid, "alg": "RS256", "use": "sig"}


def signed_token(
    subject: str = "alice",
    overrides: dict[str, object] | None = None,
    key: rsa.RSAPrivateKey = KEY,
    headers: dict[str, object] | None = None,
) -> str:
    now = int(time.time())
    claims: dict[str, object] = {
        "iss": ISSUER,
        "sub": subject,
        "aud": "interview-prep-api",
        "azp": "http://localhost:3000",
        "iat": now,
        "nbf": now,
        "exp": now + 60,
    }
    claims.update(overrides or {})
    return jwt.encode(
        claims, key, algorithm="RS256", headers={"kid": "trusted-1", **(headers or {})}
    )


@pytest_asyncio.fixture
async def account_client(database: AsyncEngine) -> AsyncIterator[httpx.AsyncClient]:
    settings = make_settings(database.url.render_as_string(hide_password=False)).model_copy(
        update={"auth_enabled": True, "auth_issuer": ISSUER}
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"keys": [jwk()]})
            )
        ) as trusted_http:
            app.state.token_verifier = TokenVerifier(settings, trusted_http)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield client


async def test_valid_signed_account_session_and_owner_scoped_profile(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    account_client.headers["Authorization"] = "Bearer " + signed_token()
    assert (await account_client.post("/api/v1/account/session", json={})).status_code == 200
    assert (await account_client.post("/api/v1/account/session", json={})).status_code == 200
    initial = await account_client.get("/api/v1/account/dashboard")
    assert initial.status_code == 200 and initial.json()["profile"] is None
    body = {
        "target_role": "Backend Engineer",
        "experience_band": "entry",
        "timezone": "Asia/Kolkata",
        "weekly_minutes": 240,
    }
    assert (
        await account_client.put("/api/v1/account/profile", json={**body, "user_id": str(uuid4())})
    ).status_code == 422
    assert (
        await account_client.put("/api/v1/account/profile", json={**body, "target_role": "   "})
    ).status_code == 422
    saved = await account_client.put("/api/v1/account/profile", json=body)
    assert saved.status_code == 200 and saved.json()["revision"] == 1
    assert (await account_client.put("/api/v1/account/profile", json=body)).status_code == 409
    assert (
        await account_client.put("/api/v1/account/profile", json={**body, "expected_revision": 1})
    ).json()["revision"] == 2
    async with async_sessionmaker(database)() as session:
        users = (await session.scalars(select(User).where(User.kind == "account"))).all()
        assert len(users) == 1 and users[0].subject == "alice"


async def test_unauthenticated_requests_have_safe_structured_401(
    account_client: httpx.AsyncClient,
) -> None:
    response = await account_client.get("/api/v1/account/dashboard")
    assert response.status_code == 401
    assert (
        response.json()["code"] == "unauthorized"
        and response.headers["WWW-Authenticate"] == "Bearer"
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["request_id"] == response.headers["x-request-id"]


async def test_account_ownership_and_demo_account_confusion(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    for subject in ["alice", "bob"]:
        account_client.headers["Authorization"] = "Bearer " + signed_token(subject)
        assert (await account_client.post("/api/v1/account/session", json={})).status_code == 200
    async with async_sessionmaker(database)() as session:
        alice = await session.scalar(select(User).where(User.subject == "alice"))
        assert alice is not None
        resume = Resume(owner_id=alice.id, label="Private Alice resume")
        session.add(resume)
        await session.flush()
        resource_id = resume.id
        await session.commit()
    assert (await account_client.get(f"/api/v1/account/resumes/{resource_id}")).status_code == 404
    assert (await account_client.get("/api/v1/account/dashboard")).json()["resumes"] == []
    account_client.headers["Authorization"] = "Bearer " + signed_token("alice")
    assert (await account_client.get(f"/api/v1/account/resumes/{resource_id}")).status_code == 200
    assert (await account_client.get("/api/v1/demo/dashboard")).status_code == 403
    account_client.headers["Authorization"] = "Bearer invalid"
    assert (await account_client.get("/api/v1/demo/dashboard")).status_code == 403
    assert (await account_client.get("/api/v1/account/dashboard")).status_code == 401
    del account_client.headers["Authorization"]
    created = await account_client.post(
        "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
    )
    assert created.status_code == 200
    assert (await account_client.get(f"/api/v1/demo/resumes/{resource_id}")).status_code == 404
    assert (await account_client.get("/api/v1/account/dashboard")).status_code == 401


async def test_suspended_accounts_remain_forbidden_after_bootstrap(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    account_client.headers["Authorization"] = "Bearer " + signed_token()
    await account_client.post("/api/v1/account/session", json={})
    async with async_sessionmaker(database)() as session:
        user = await session.scalar(select(User).where(User.subject == "alice"))
        assert user is not None
        user.status = PrincipalStatus.SUSPENDED
        await session.commit()
    for method, path in [("GET", "/api/v1/account/dashboard"), ("POST", "/api/v1/account/session")]:
        response = await account_client.request(method, path, json={} if method == "POST" else None)
        assert response.status_code == 403 and response.json()["code"] == "forbidden"


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "https://attacker.example"},
        {"aud": "wrong-audience"},
        {"azp": "https://attacker.example"},
        {"exp": 1},
        {"nbf": int(time.time()) + 600},
        {"iat": int(time.time()) + 600},
        {"exp": int(time.time()) + 3600},
        {"sub": ""},
        {"sub": None},
        {"azp": None},
        {"aud": ["interview-prep-api", "other"]},
        {"sts": "pending"},
    ],
)
async def test_reject_untrusted_or_invalid_claims(
    account_client: httpx.AsyncClient, claims: dict[str, object]
) -> None:
    response = await account_client.post(
        "/api/v1/account/session",
        json={},
        headers={"Authorization": "Bearer " + signed_token(overrides=claims)},
    )
    assert response.status_code == 401
    assert "attacker" not in response.text and "jwt" not in response.text


async def test_signature_and_token_key_urls_are_rejected(account_client: httpx.AsyncClient) -> None:
    for token in [
        signed_token(key=OTHER_KEY),
        signed_token(headers={"jku": "https://attacker.example/keys"}),
        jwt.encode({"sub": "alice"}, "fake-key" * 8, algorithm="HS256"),
        "x" * 9000,
    ]:
        assert (
            await account_client.post(
                "/api/v1/account/session", json={}, headers={"Authorization": "Bearer " + token}
            )
        ).status_code == 401


async def test_trusted_jwks_cache_rotation_and_expiry_failure() -> None:
    settings = make_settings().model_copy(update={"auth_enabled": True, "auth_issuer": ISSUER})
    calls: list[str] = []
    rotated = False
    unavailable = False

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if unavailable:
            return httpx.Response(503)
        return httpx.Response(
            200, json={"keys": [jwk(), *([jwk(OTHER_KEY, "rotated")] if rotated else [])]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        verifier = TokenVerifier(settings, http)
        assert (await verifier.verify(signed_token())).subject == "alice"
        await verifier.verify(signed_token())
        assert len(calls) == 1 and calls[0] == ISSUER + "/.well-known/jwks.json"
        rotated = True
        await verifier.verify(signed_token(key=OTHER_KEY, headers={"kid": "rotated"}))
        assert len(calls) == 2
        with pytest.raises(AuthenticationError):
            await verifier.verify(signed_token(headers={"kid": "missing"}))
        assert len(calls) == 2
        unavailable = True
        verifier.expires_at = 0
        with pytest.raises(AuthenticationUnavailable):
            await verifier.verify(signed_token())
        assert len(calls) == 3
