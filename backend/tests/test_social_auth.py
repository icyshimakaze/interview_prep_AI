"""Pinned OAuth/state/PKCE with signed SYNTHETIC provider HTTP, never live Google/GitHub."""

import base64
import hashlib
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
import jwt
import pytest
import pytest_asyncio
from conftest import test_settings as make_settings
from interview_prep.main import create_app
from interview_prep.modules.identity.models import User
from interview_prep.modules.identity.verification import TokenVerifier
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_better_auth import ISSUER, bridge, jwks, object_body
from test_better_auth import auth_database as auth_database
from test_candidate_context import PROFILE
from test_interviews import BASE, command, create, read, runner, seed

SOCIAL: dict[str, object] = {
    "google": {
        "clientId": "synthetic-google-client.apps.googleusercontent.com",
        "clientSecret": "synthetic-google-secret",
        "allowedSubjects": ["synthetic-google-alice", "synthetic-google-bob"],
    },
    "github": {
        "clientId": "synthetic-github-client",
        "clientSecret": "synthetic-github-secret",
        "allowedSubjects": ["10001", "10002"],
    },
}


@pytest.fixture(params=[False, True], ids=["invited", "public"])
def registration_policy(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> bool:
    public = request.param is True
    if public:
        for name, value in tuple(SOCIAL.items()):
            assert isinstance(value, dict)
            monkeypatch.setitem(
                SOCIAL, name, {**value, "allowedSubjects": [], "publicRegistration": True}
            )
    return public


def require_status(result: dict[str, object], expected: int) -> None:
    if result["status"] != expected:
        raise AssertionError(f"Synthetic auth status: expected {expected}, got {result['status']}")


def cookies(previous: str, response: dict[str, object]) -> str:
    jar = SimpleCookie()
    jar.load(previous)
    values = response.get("cookies")
    assert isinstance(values, list)
    for value in values:
        incoming = SimpleCookie()
        incoming.load(str(value))
        for name, cookie in incoming.items():
            if cookie["max-age"] == "0":
                jar.pop(name, None)
            else:
                jar[name] = cookie.value
    return "; ".join(f"{name}={cookie.value}" for name, cookie in jar.items())


async def request(
    database: AsyncEngine,
    path: str,
    *,
    cookie: str = "",
    body: dict[str, object] | None = None,
    fixture: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    return await bridge(
        database,
        path,
        method="POST" if body is not None else "GET",
        body=body,
        cookie=cookie,
        social=SOCIAL,
        oauth_fixture=fixture,
        headers=headers,
        registration_enabled=False,
    )


async def begin(
    database: AsyncEngine, provider: str, cookie: str = "", *, link: bool = False
) -> tuple[str, str]:
    response = await request(
        database,
        "/link-social" if link else "/sign-in/social",
        cookie=cookie,
        body={"provider": provider, "disableRedirect": True},
    )
    require_status(response, 200)
    url = object_body(response).get("url")
    assert isinstance(url, str)
    query = parse_qs(urlsplit(url).query)
    assert query["scope"][0].split() == (
        ["openid", "profile", "email"] if provider == "google" else ["user:email"]
    )
    assert query["prompt"] == ["select_account"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == [ISSUER + "/api/auth/callback/" + provider]
    async with database.connect() as connection:
        values = (await connection.execute(text("SELECT value FROM auth.verification"))).scalars()
        state = next(
            json.loads(str(value))
            for value in values
            if json.loads(str(value)).get("oauthState") == query["state"][0]
        )
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(state["codeVerifier"].encode()).digest())
        .decode()
        .rstrip("=")
    )
    assert query["code_challenge"] == [challenge]
    metadata = (
        {"scope": "openid profile email", "authuser": "0", "prompt": "consent"}
        if provider == "google"
        else {}
    )
    path = (
        "/callback/"
        + provider
        + "?"
        + urlencode({"state": query["state"][0], "code": "synthetic-code", **metadata})
    )
    return path, cookies(cookie, response)


async def login(
    database: AsyncEngine, provider: str, *, fixture: dict[str, object] | None = None
) -> str:
    path, cookie = await begin(database, provider)
    response = await request(database, path, cookie=cookie, fixture=fixture)
    require_status(response, 302)
    if response["location"] != ISSUER + "/app/dashboard":
        raise AssertionError("Synthetic OAuth callback did not reach its fixed success destination")
    assert response["oauthCalls"] == (
        ["google_token", "jwks"]
        if provider == "google"
        else ["github_token", "github_user", "github_emails"]
    )
    return cookies(cookie, response)


async def token(database: AsyncEngine, cookie: str) -> str:
    response = await bridge(database, "/token", cookie=cookie)
    require_status(response, 200)
    value = object_body(response).get("token")
    assert isinstance(value, str)
    return value


@pytest_asyncio.fixture
async def social_database(auth_database: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    async with auth_database.begin() as connection:
        await connection.execute(text("TRUNCATE auth.verification"))
    yield auth_database
    async with auth_database.begin() as connection:
        await connection.execute(text("TRUNCATE auth.verification"))


@asynccontextmanager
async def account_api(database: AsyncEngine) -> AsyncIterator[httpx.AsyncClient]:
    public = await jwks(database)
    settings = make_settings(database.url.render_as_string(hide_password=False)).model_copy(
        update={
            "auth_enabled": True,
            "auth_provider": "better_auth",
            "auth_issuer": ISSUER,
            "auth_jwks_endpoint": ISSUER + "/api/auth/jwks",
            "allowed_origins": [ISSUER],
        }
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=public))
        ) as keys:
            app.state.token_verifier = TokenVerifier(settings, keys)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://api.example.test"
            ) as client:
                yield client


@pytest.mark.parametrize("provider", ["google", "github"])
async def test_new_returning_social_user_same_principal_and_revocation(
    social_database: AsyncEngine, provider: str, registration_policy: bool
) -> None:
    database = social_database
    cookie = await login(database, provider)
    issued = await token(database, cookie)
    claims = jwt.decode(issued, options={"verify_signature": False})
    assert claims["exp"] - claims["iat"] == 60
    assert claims["iss"] == claims["azp"] == ISSUER
    async with account_api(database) as client:
        client.headers["Authorization"] = "Bearer " + issued
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.put("/api/v1/account/profile", json=PROFILE)).status_code == 200
        async with async_sessionmaker(database)() as session:
            owner = await session.scalar(select(User.id).where(User.subject == claims["sub"]))
            assert owner is not None
        await request(database, "/sign-out", cookie=cookie, body={})
        assert (await client.get("/api/v1/account/profile")).status_code == 401
        returning = await login(database, provider, fixture={"email": "changed@example.invalid"})
        fresh = await token(database, returning)
        assert jwt.decode(fresh, options={"verify_signature": False})["sub"] == claims["sub"]
        client.headers["Authorization"] = "Bearer " + fresh
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.get("/api/v1/account/profile")).json()["target_role"] == PROFILE[
            "target_role"
        ]
        async with async_sessionmaker(database)() as session:
            assert (
                await session.scalar(select(User.id).where(User.subject == claims["sub"])) == owner
            )
            assert await session.scalar(select(func.count()).select_from(User)) == 1
    async with database.connect() as connection:
        row = (
            await connection.execute(
                text('SELECT "accessToken", "refreshToken", "idToken" FROM auth.account')
            )
        ).one()
        assert tuple(row) == (None, None, None)
        assert await connection.scalar(text('SELECT "emailVerified" FROM auth."user"')) is True


@pytest.mark.parametrize("provider", ["google", "github"])
async def test_unknown_eligible_public_identity_registers_without_test_allowlist(
    social_database: AsyncEngine, provider: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = SOCIAL[provider]
    assert isinstance(settings, dict)
    old_subjects = settings["allowedSubjects"]
    unknown = "previously-unknown-google-identity" if provider == "google" else "30003"
    assert isinstance(old_subjects, list) and unknown not in old_subjects
    monkeypatch.setitem(
        SOCIAL, provider, {**settings, "allowedSubjects": [], "publicRegistration": True}
    )
    fixture: dict[str, object] = {
        "sub": unknown,
        "githubId": 30003,
        "email": "independent-public@example.invalid",
        "privateEmail": True,
    }
    path, cookie = await begin(social_database, provider)
    first = await request(social_database, path, cookie=cookie, fixture=fixture)
    assert first["location"] == ISSUER + "/app/dashboard"
    reference = first["callbackRequestId"]
    assert isinstance(reference, str) and len(reference) == 36
    assert first["callbackDiagnostics"] == [
        {
            "event": "oauth_callback_result",
            "requestId": reference,
            "provider": provider,
            "admission": "public",
            "status": 302,
            "reason": "completed",
        }
    ]
    signed_in = cookies(cookie, first)
    original_token = await token(social_database, signed_in)
    subject = jwt.decode(original_token, options={"verify_signature": False})["sub"]
    async with account_api(social_database) as client:
        client.headers["Authorization"] = "Bearer " + original_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
    async with social_database.connect() as connection:
        principal = await connection.scalar(text("SELECT id FROM public.principals"))
        assert principal is not None
        assert await connection.scalar(text('SELECT "accountId" FROM auth.account')) == unknown
        assert await connection.scalar(text('SELECT "emailVerified" FROM auth."user"')) is True
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
    await request(social_database, "/sign-out", cookie=signed_in, body={})
    returning = await login(social_database, provider, fixture=fixture)
    returned_subject = jwt.decode(
        await token(social_database, returning), options={"verify_signature": False}
    )["sub"]
    assert returned_subject == subject
    async with social_database.connect() as connection:
        assert await connection.scalar(text("SELECT id FROM public.principals")) == principal
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
    denied = await request(social_database, "/sign-up/email", body={})
    assert denied["status"] == 404


async def test_public_google_email_collision_with_github_fails_closed_then_distinct_email_enrolls(
    social_database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    for provider, settings in tuple(SOCIAL.items()):
        assert isinstance(settings, dict)
        monkeypatch.setitem(
            SOCIAL, provider, {**settings, "allowedSubjects": [], "publicRegistration": True}
        )
    await login(social_database, "google", fixture={"email": "existing-google@example.invalid"})
    github_cookie = await login(social_database, "github")
    github_token = await token(social_database, github_cookie)
    async with account_api(social_database) as client:
        client.headers["Authorization"] = "Bearer " + github_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.put("/api/v1/account/profile", json=PROFILE)).status_code == 200
        async with social_database.connect() as connection:
            original_principal = await connection.scalar(text("SELECT id FROM public.principals"))
        path, state_cookie = await begin(social_database, "google")
        rejected = await request(
            social_database,
            path,
            cookie=state_cookie,
            fixture={"sub": "unknown-google-with-github-email"},
        )
        assert rejected["location"] == ISSUER + "/sign-in?social_error=1"
        events = rejected["callbackDiagnostics"]
        assert isinstance(events, list) and len(events) == 1
        assert events[0]["reason"] == "account_not_linked"
        assert events[0]["admission"] == "public"
        async with social_database.connect() as connection:
            assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 2
            assert await connection.scalar(text("SELECT count(*) FROM auth.account")) == 2
            assert (
                await connection.scalar(text("SELECT id FROM public.principals"))
                == original_principal
            )
        assert (await client.get("/api/v1/account/profile")).json()["target_role"] == PROFILE[
            "target_role"
        ]
        enrolled = await login(
            social_database,
            "google",
            fixture={
                "sub": "unknown-google-distinct-email",
                "email": "independent-google@example.invalid",
            },
        )
        new_token = await token(social_database, enrolled)
        assert (
            jwt.decode(new_token, options={"verify_signature": False})["sub"]
            != jwt.decode(github_token, options={"verify_signature": False})["sub"]
        )
        client.headers["Authorization"] = "Bearer " + new_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        async with social_database.connect() as connection:
            assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 3
            assert await connection.scalar(text("SELECT count(*) FROM public.principals")) == 2


async def test_github_only_public_release_unknown_user_saved_work_isolation_and_revocation(
    social_database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    github = SOCIAL["github"]
    assert isinstance(github, dict)
    monkeypatch.delitem(SOCIAL, "google")
    monkeypatch.setitem(
        SOCIAL, "github", {**github, "allowedSubjects": [], "publicRegistration": True}
    )
    disabled = await request(social_database, "/sign-in/social", body={"provider": "google"})
    assert disabled["status"] == 400
    assert not disabled["oauthCalls"]
    for path in ["/sign-up/email", "/request-password-reset", "/send-verification-email"]:
        assert (await request(social_database, path, body={}))["status"] == 404
    old_cookie = await login(
        social_database, "github", fixture={"email": "existing-github@example.invalid"}
    )
    old_token = await token(social_database, old_cookie)
    fixture: dict[str, object] = {
        "githubId": 30003,
        "email": "independent-github@example.invalid",
        "privateEmail": True,
    }
    new_cookie = await login(social_database, "github", fixture=fixture)
    new_token = await token(social_database, new_cookie)
    old_claims = jwt.decode(old_token, options={"verify_signature": False})
    new_claims = jwt.decode(new_token, options={"verify_signature": False})
    assert old_claims["sub"] != new_claims["sub"]
    assert jwt.get_unverified_header(new_token)["alg"] == "RS256"
    assert new_claims["exp"] - new_claims["iat"] == 60
    async with account_api(social_database) as client:
        client.headers["Authorization"] = "Bearer " + old_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        old = await client.post(
            "/api/v1/account/targets",
            json={"title": "Existing test work", "description": "Synthetic only"},
        )
        assert old.status_code == 201
        old_path = "/api/v1/account/targets/" + old.json()["id"]
        client.headers["Authorization"] = "Bearer " + new_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.put("/api/v1/account/profile", json=PROFILE)).status_code == 200
        assert (await client.get(old_path)).status_code == 404
        assert (
            await client.put(
                old_path,
                json={
                    "title": "Forbidden edit",
                    "description": "Synthetic only",
                    "expected_revision": 1,
                },
            )
        ).status_code == 404
        owned = await client.post(
            "/api/v1/account/targets",
            json={"title": "Independent saved work", "description": "Synthetic only"},
        )
        assert owned.status_code == 201
        owned_path = "/api/v1/account/targets/" + owned.json()["id"]
        assert (await client.get(owned_path)).status_code == 200
        assert new_claims["exp"] > time.time()
        await request(social_database, "/sign-out", cookie=new_cookie, body={})
        assert (await client.get(owned_path)).status_code == 401
        returning = await login(social_database, "github", fixture=fixture)
        returning_token = await token(social_database, returning)
        assert (
            jwt.decode(returning_token, options={"verify_signature": False})["sub"]
            == new_claims["sub"]
        )
        client.headers["Authorization"] = "Bearer " + returning_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.get(owned_path)).status_code == 200
        assert (await client.get(old_path)).status_code == 404
        assert (await client.get("/api/v1/account/profile")).status_code == 200
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 2
        assert await connection.scalar(text("SELECT count(*) FROM public.principals")) == 2
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM auth.account WHERE \"providerId\"='google'")
            )
            == 0
        )
        row = (
            await connection.execute(
                text('SELECT "accessToken","refreshToken","idToken" FROM auth.account LIMIT 1')
            )
        ).one()
        assert tuple(row) == (None, None, None)


async def test_same_email_requires_explicit_link_and_retains_completed_history(
    social_database: AsyncEngine,
    registration_policy: bool,
) -> None:
    database = social_database
    await seed(database)
    alice_cookie = await login(database, "google")
    alice_token = await token(database, alice_cookie)
    path, github_cookie = await begin(database, "github")
    denied = await request(database, path, cookie=github_cookie)
    assert denied["location"] == ISSUER + "/sign-in?social_error=1"
    async with database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
        assert await connection.scalar(text("SELECT count(*) FROM auth.account")) == 1
    async with account_api(database) as client:
        client.headers["Authorization"] = "Bearer " + alice_token
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        interview = await command(client, await create(client, 1), "start")
        assert interview.current_turn
        interview = await command(
            client,
            interview,
            f"turns/{interview.current_turn.id}/submit",
            {"answer_text": "Synthetic OAuth continuity answer retained after explicit linking."},
        )
        worker = runner(client)
        assert await worker.tick()
        interview = await command(client, await read(client, interview), "complete")
        await worker.maintenance()
        review_path = f"{BASE}/{interview.id}/review"
        before = (await client.get(review_path)).json()
        path, link_cookie = await begin(database, "github", alice_cookie, link=True)
        linked = await request(database, path, cookie=link_cookie)
        assert linked["location"] == ISSUER + "/app/account-access"
        github = await login(database, "github")
        github_token = await token(database, github)
        assert (
            jwt.decode(github_token, options={"verify_signature": False})["sub"]
            == jwt.decode(alice_token, options={"verify_signature": False})["sub"]
        )
        client.headers["Authorization"] = "Bearer " + github_token
        after = (await client.get(review_path)).json()
        assert after["turns"] == before["turns"]
        assert after["session"]["id"] == before["session"]["id"]
        bob = await login(
            database,
            "google",
            fixture={"sub": "synthetic-google-bob", "email": "social-bob@example.invalid"},
        )
        client.headers["Authorization"] = "Bearer " + await token(database, bob)
        assert (await client.post("/api/v1/account/session", json={})).status_code == 200
        assert (await client.get(review_path)).status_code == 404
        assert (await client.get(BASE)).json()["items"] == []
        taken_path, taken_cookie = await begin(database, "google", bob, link=True)
        taken = await request(database, taken_path, cookie=taken_cookie)
        assert taken["location"] == ISSUER + "/sign-in?social_error=1"
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text(
                    'SELECT count(*) FROM auth.account WHERE "accessToken" IS NOT NULL '
                    'OR "refreshToken" IS NOT NULL OR "idToken" IS NOT NULL'
                )
            )
            == 0
        )


@pytest.mark.parametrize(
    "fixture",
    [
        {"badSignature": True},
        {"wrongAudience": True},
        {"wrongIssuer": True},
        {"expired": True},
        {"sub": "not-admitted"},
        {"invalidCode": True},
    ],
)
@pytest.mark.parametrize("provider", ["google"])
async def test_invalid_provider_evidence_cannot_create_session(
    social_database: AsyncEngine, fixture: dict[str, object], provider: str
) -> None:
    path, cookie = await begin(social_database, provider)
    response = await request(social_database, path, cookie=cookie, fixture=fixture)
    assert response["location"] == ISSUER + "/sign-in?social_error=1"
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
        assert await connection.scalar(text("SELECT count(*) FROM auth.session")) == 0


async def test_state_cookie_replay_consent_and_login_csrf(
    social_database: AsyncEngine, registration_policy: bool
) -> None:
    database = social_database
    path, cookie = await begin(database, "google")
    unbound = await request(database, path)
    assert unbound["location"] == ISSUER + "/sign-in?social_error=1"
    assert unbound["oauthCalls"] == []
    denied_path = path.replace(
        "code=synthetic-code", "error=access_denied&error_description=private-provider-description"
    )
    denied = await request(database, denied_path, cookie=cookie)
    assert denied["location"] == ISSUER + "/sign-in?social_error=1"
    replay = await request(database, path, cookie=cookie)
    assert replay["location"] == ISSUER + "/sign-in?social_error=1"
    assert replay["oauthCalls"] == []
    expired_path, expired_cookie = await begin(database, "google")
    async with database.begin() as connection:
        await connection.execute(
            text(
                "UPDATE auth.verification SET \"expiresAt\"=CURRENT_TIMESTAMP-interval '1 minute', "
                "value=jsonb_set(value::jsonb, '{expiresAt}', '0')::text"
            )
        )
    expired = await request(database, expired_path, cookie=expired_cookie)
    assert expired["location"] == ISSUER + "/sign-in?social_error=1"
    assert expired["oauthCalls"] == []
    require_status(
        await request(
            database,
            "/sign-in/social",
            body={"provider": "google"},
            headers={"origin": "https://foreign.example"},
        ),
        403,
    )
    invalid_bodies: tuple[dict[str, object], ...] = (
        {"provider": "google", "callbackURL": "https://foreign.example"},
        {"provider": "google", "idToken": {"token": "untrusted"}},
        {"provider": "google", "requestSignUp": True},
    )
    for body in invalid_bodies:
        require_status(await request(database, "/sign-in/social", body=body), 400)


async def test_explicit_link_rejects_missing_stale_and_switched_session(
    social_database: AsyncEngine,
) -> None:
    database = social_database
    require_status(await request(database, "/link-social", body={"provider": "github"}), 401)
    alice = await login(database, "google")
    path, pending = await begin(database, "github", alice, link=True)
    bob = await login(
        database, "google", fixture={"sub": "synthetic-google-bob", "email": "bob@example.invalid"}
    )
    state_only = "; ".join(part for part in pending.split("; ") if ".state=" in part)
    switched = await request(database, path, cookie=bob + "; " + state_only)
    assert switched["location"] == ISSUER + "/sign-in?social_error=1"
    async with database.begin() as connection:
        await connection.execute(
            text("UPDATE auth.session SET \"createdAt\"=CURRENT_TIMESTAMP-interval '10 minutes'")
        )
    require_status(
        await request(database, "/link-social", cookie=alice, body={"provider": "github"}), 403
    )
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM auth.account WHERE \"providerId\"='github'")
            )
            == 0
        )


@pytest.mark.parametrize(
    "fixture",
    [
        {"githubId": 99999},
        {"githubId": "mutable-login"},
        {"invalidCode": True},
        {"missingEmail": True},
        {"userApiFailure": True},
        {"privateEmail": True, "emailApiFailure": True},
    ],
)
async def test_invalid_github_evidence_fails_closed(
    social_database: AsyncEngine, fixture: dict[str, object]
) -> None:
    path, cookie = await begin(social_database, "github")
    response = await request(social_database, path, cookie=cookie, fixture=fixture)
    assert response["location"] == ISSUER + "/sign-in?social_error=1"
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
        assert await connection.scalar(text("SELECT count(*) FROM auth.session")) == 0


@pytest.mark.parametrize("verified", [True, False])
async def test_github_private_email_preserves_provider_verification(
    social_database: AsyncEngine, verified: bool
) -> None:
    cookie = await login(
        social_database, "github", fixture={"privateEmail": True, "unverifiedEmail": not verified}
    )
    require_status(await bridge(social_database, "/token", cookie=cookie), 200)
    async with social_database.connect() as connection:
        assert (
            await connection.scalar(text('SELECT email FROM auth."user"'))
            == "social-alice@example.invalid"
        )
        assert await connection.scalar(text('SELECT "emailVerified" FROM auth."user"')) is verified


@pytest.mark.parametrize("provider", ["google", "github"])
@pytest.mark.parametrize("fixture", [{"unverifiedEmail": True}, {"missingEmail": True}])
async def test_public_registration_requires_verified_provider_email(
    social_database: AsyncEngine,
    provider: str,
    fixture: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in tuple(SOCIAL.items()):
        assert isinstance(value, dict)
        monkeypatch.setitem(
            SOCIAL, name, {**value, "allowedSubjects": [], "publicRegistration": True}
        )
    path, cookie = await begin(social_database, provider)
    response = await request(social_database, path, cookie=cookie, fixture=fixture)
    assert response["location"] == ISSUER + "/sign-in?social_error=1"
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
        assert await connection.scalar(text("SELECT count(*) FROM auth.session")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM auth.account")) == 0


async def test_password_account_requires_explicit_google_link_and_keeps_credentials(
    social_database: AsyncEngine,
) -> None:
    database = social_database
    registered = await bridge(
        database,
        "/sign-up/email",
        method="POST",
        body={
            "name": "Synthetic Password Candidate",
            "email": "social-alice@example.invalid",
            "password": "Synthetic-password-0001",
        },
    )
    require_status(registered, 200)
    password_cookie = cookies("", registered)
    password_token = await token(database, password_cookie)
    owner = jwt.decode(password_token, options={"verify_signature": False})["sub"]
    path, state_cookie = await begin(database, "google")
    denied = await request(database, path, cookie=state_cookie)
    assert denied["location"] == ISSUER + "/sign-in?social_error=1"
    path, pending = await begin(database, "google", password_cookie, link=True)
    linked = await request(database, path, cookie=pending)
    assert linked["location"] == ISSUER + "/app/account-access"
    google_cookie = await login(database, "google")
    assert (
        jwt.decode(await token(database, google_cookie), options={"verify_signature": False})["sub"]
        == owner
    )
    signed_in = await bridge(
        database,
        "/sign-in/email",
        method="POST",
        body={
            "email": "social-alice@example.invalid",
            "password": "Synthetic-password-0001",
        },
        registration_enabled=False,
    )
    require_status(signed_in, 200)
    assert (
        jwt.decode(
            await token(database, cookies("", signed_in)), options={"verify_signature": False}
        )["sub"]
        == owner
    )
    async with database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
        # Explicit Google proof can verify this same email; password and owner survive.
        # Recovery/verification-email endpoints remain unavailable independently.
        assert await connection.scalar(text('SELECT "emailVerified" FROM auth."user"')) is True


async def test_callback_cannot_switch_the_server_bound_provider(
    social_database: AsyncEngine,
) -> None:
    path, cookie = await begin(social_database, "google")
    swapped = await request(
        social_database, path.replace("/callback/google", "/callback/github"), cookie=cookie
    )
    assert swapped["location"] == ISSUER + "/sign-in?social_error=1"
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
        assert await connection.scalar(text("SELECT count(*) FROM auth.session")) == 0


async def test_github_renamed_login_keeps_stable_id_and_owner(
    social_database: AsyncEngine,
    registration_policy: bool,
) -> None:
    first = await login(social_database, "github")
    first_owner = jwt.decode(
        await token(social_database, first), options={"verify_signature": False}
    )["sub"]
    returning = await login(
        social_database,
        "github",
        fixture={"githubLogin": "renamed-candidate", "privateEmail": True},
    )
    assert (
        jwt.decode(await token(social_database, returning), options={"verify_signature": False})[
            "sub"
        ]
        == first_owner
    )
    async with social_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
        assert await connection.scalar(text('SELECT "accountId" FROM auth.account')) == "10001"


@pytest.mark.parametrize("provider", ["google", "github"])
async def test_occupied_provider_cannot_be_reassigned(
    social_database: AsyncEngine, provider: str, registration_policy: bool
) -> None:
    database = social_database
    original = await login(database, provider)
    original_subject = jwt.decode(
        await token(database, original), options={"verify_signature": False}
    )["sub"]
    other = await login(
        database,
        "google",
        fixture={"sub": "synthetic-google-bob", "email": "other@example.invalid"},
    )
    path, pending = await begin(database, provider, other, link=True)
    denied = await request(database, path, cookie=pending)
    assert denied["location"] == ISSUER + "/sign-in?social_error=1"
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text(
                    'SELECT "userId" FROM auth.account '
                    'WHERE "providerId"=:provider AND "accountId"=:account'
                ),
                {
                    "provider": provider,
                    "account": "synthetic-google-alice" if provider == "google" else "10001",
                },
            )
            == original_subject
        )
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 2
