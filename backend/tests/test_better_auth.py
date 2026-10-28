"""Real pinned-library issuance; independent Python signature/session/owner checks."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import jwt
import pytest
import pytest_asyncio
from conftest import test_settings as make_settings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.main import create_app
from interview_prep.modules.identity.models import PrincipalIdentity, PrincipalStatus, User
from interview_prep.modules.identity.verification import AuthenticationError, TokenVerifier

ISSUER = "https://auth.example.test"
ROOT = Path(__file__).resolve().parents[2]


async def bridge(
    database: AsyncEngine,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, object] | None = None,
    cookie: str = "",
    headers: dict[str, str] | None = None,
    peer: str = "192.0.2.10",
    sign: dict[str, object] | None = None,
    registration_enabled: bool = True,
    omit_origin: bool = False,
    direct_handler: bool = False,
    registration_emails: list[str] | None = None,
    social: dict[str, object] | None = None,
    oauth_fixture: dict[str, object] | None = None,
) -> dict[str, object]:
    url = database.url.set(drivername="postgresql")
    process = await asyncio.create_subprocess_exec(
        "node",
        str(ROOT / "frontend/scripts/auth-bridge.mjs"),
        cwd=ROOT / "frontend",
        env={**os.environ, "TEST_AUTH_DATABASE_URL": url.render_as_string(hide_password=False)},
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(
        process.communicate(
            json.dumps(
                {
                    "path": path,
                    "method": method,
                    "body": body,
                    "cookie": cookie,
                    "headers": headers,
                    "peer": peer,
                    "sign": sign,
                    "registrationEnabled": registration_enabled,
                    "omitOrigin": omit_origin,
                    "directHandler": direct_handler,
                    "registrationEmails": registration_emails,
                    "social": social,
                    "oauthFixture": oauth_fixture,
                }
            ).encode()
        ),
        timeout=30,
    )
    if process.returncode != 0:
        raise AssertionError("Pinned auth bridge failed; raw credentials/diagnostics withheld")
    data: object = json.loads(stdout)
    assert isinstance(data, dict)
    return data


def object_body(result: dict[str, object]) -> dict[str, object]:
    value = result["body"]
    assert isinstance(value, dict)
    return value


def session_cookie(result: dict[str, object]) -> str:
    value = result["cookies"]
    assert isinstance(value, list)
    return "; ".join(str(item).split(";")[0] for item in value)


@pytest_asyncio.fixture
async def auth_database(database: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    async with database.begin() as connection:
        await connection.execute(
            text('TRUNCATE auth."user", auth.jwks, auth.request_limits CASCADE')
        )
    yield database
    async with database.begin() as connection:
        await connection.execute(
            text('TRUNCATE auth."user", auth.jwks, auth.request_limits CASCADE')
        )


async def register(database: AsyncEngine) -> tuple[str, str]:
    response = await bridge(
        database,
        "/sign-up/email",
        method="POST",
        body={
            "name": "Synthetic Candidate",
            "email": f"{uuid4().hex}@example.test",
            "password": "Synthetic-password-0001",
        },
    )
    assert response["status"] == 200, "Real library registration failed"
    cookie = session_cookie(response)
    result = object_body(await bridge(database, "/token", cookie=cookie))
    token = result.get("token")
    assert isinstance(token, str)
    return cookie, token


async def jwks(database: AsyncEngine) -> dict[str, object]:
    return object_body(await bridge(database, "/jwks"))


@pytest.mark.asyncio
async def test_actual_pinned_claims_signature_active_session_and_revocation(
    auth_database: AsyncEngine,
) -> None:
    database = auth_database
    cookie, token = await register(database)
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
    trusted_requests: list[str] = []

    def public_keys(request: httpx.Request) -> httpx.Response:
        trusted_requests.append(str(request.url))
        return httpx.Response(200, json=public)

    async with httpx.AsyncClient(transport=httpx.MockTransport(public_keys)) as transport:
        verifier = TokenVerifier(settings, transport)
        identity = await verifier.verify(token)
        claims = jwt.decode(token, options={"verify_signature": False})
        assert set(claims) == {"iss", "sub", "aud", "iat", "nbf", "exp", "azp", "sid"}
        assert jwt.get_unverified_header(token)["alg"] == "RS256"
        assert claims["iss"] == claims["azp"] == ISSUER
        assert claims["aud"] == "interview-prep-api"
        assert claims["exp"] - claims["iat"] == 60
        assert claims["nbf"] == claims["iat"]
        assert identity.session_id and identity.subject == claims["sub"]
        assert trusted_requests == [ISSUER + "/api/auth/jwks"]
        # Alter the signature, keeping all claims intact.
        parts = token.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        with pytest.raises(AuthenticationError):
            await verifier.verify(".".join(parts))
        app = create_app(settings)
        async with app.router.lifespan_context(app):
            app.state.token_verifier = verifier
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://api.example.test",
                headers={"Authorization": "Bearer " + token},
            ) as client:
                assert (await client.post("/api/v1/account/session", json={})).status_code == 200
                assert (await client.get("/api/v1/account/dashboard")).status_code == 200
                logout = await bridge(database, "/sign-out", method="POST", cookie=cookie)
                assert logout["status"] == 200
                # Signature is still valid: the independently checked DB session blocks replay.
                await verifier.verify(token)
                assert (await client.get("/api/v1/account/dashboard")).status_code == 401
                assert (await client.post("/api/v1/account/session", json={})).status_code == 401


@pytest.mark.asyncio
async def test_real_cookie_security_and_disabled_flows(auth_database: AsyncEngine) -> None:
    database = auth_database
    registered = await bridge(
        database,
        "/sign-up/email",
        method="POST",
        body={
            "name": "Synthetic",
            "email": "cookie@example.test",
            "password": "Synthetic-password-0001",
        },
    )
    assert registered["status"] == 200
    cookies = registered["cookies"]
    assert isinstance(cookies, list)
    session = next(str(c) for c in cookies if "session_token=" in str(c))
    for attribute in ("Secure", "HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=604800"):
        assert attribute.lower() in session.lower()
    assert "Domain=" not in session
    # Pinned Better Auth prepends __Secure- itself; Domain must remain absent.
    assert session.startswith("__Secure-interview-auth.session_token=")
    user = object_body(registered).get("user")
    assert "token" not in object_body(registered)
    current = object_body(await bridge(database, "/get-session", cookie=session_cookie(registered)))
    current_session = current.get("session")
    assert isinstance(current_session, dict) and "token" not in current_session
    assert isinstance(user, dict) and user["emailVerified"] is False
    for path in (
        "/request-password-reset",
        "/send-verification-email",
        "/sign-in/social",
        "/change-email",
        "/delete-user",
        "/link-social",
        "/sign-jwt",
        "/verify-jwt",
    ):
        response = await bridge(database, path, method="POST", body={})
        assert response["status"] == 404
    foreign = await bridge(
        database,
        "/sign-in/email",
        method="POST",
        body={"email": "cookie@example.test", "password": "Synthetic-password-0001"},
        headers={"origin": "https://foreign.example.test"},
    )
    assert foreign["status"] == 403


@pytest.mark.asyncio
async def test_registration_closed_in_handler_and_library(auth_database: AsyncEngine) -> None:
    body: dict[str, object] = {
        "email": "closed@example.test",
        "password": "Synthetic-password-0001",
        "name": "Synthetic",
    }
    for direct in (False, True):
        result = await bridge(
            auth_database,
            "/sign-up/email",
            method="POST",
            body=body,
            registration_enabled=False,
            direct_handler=direct,
        )
        assert result["status"] in {400, 404}
    async with auth_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
    # Closing registration does not disable authentication for an existing tester.
    await bridge(auth_database, "/sign-up/email", method="POST", body=body)
    login = await bridge(
        auth_database, "/sign-in/email", method="POST", body=body, registration_enabled=False
    )
    assert login["status"] == 200
    assert "token" not in object_body(login)


@pytest.mark.asyncio
async def test_private_registration_allowlist_preserves_public_closure(
    auth_database: AsyncEngine,
) -> None:
    email = "phase3-000000000001-alice@example.invalid"
    allowed = [email, "phase3-000000000001-bob@example.invalid"]
    body: dict[str, object] = {
        "email": "outsider@example.invalid",
        "password": "Synthetic-password-0001",
        "name": "Synthetic",
    }
    denied = await bridge(
        auth_database,
        "/sign-up/email",
        method="POST",
        body=body,
        registration_emails=allowed,
    )
    assert denied["status"] == 404
    async with auth_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 0
    body["email"] = email
    created = await bridge(
        auth_database,
        "/sign-up/email",
        method="POST",
        body=body,
        registration_emails=allowed,
    )
    assert created["status"] == 200
    assert "token" not in object_body(created)
    body["email"] = allowed[1]
    closed = await bridge(
        auth_database,
        "/sign-up/email",
        method="POST",
        body=body,
        registration_enabled=False,
        registration_emails=allowed,
    )
    assert closed["status"] == 404
    async with auth_database.connect() as connection:
        assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1


@pytest.mark.asyncio
async def test_csrf_fetch_metadata_and_public_jwks(auth_database: AsyncEngine) -> None:
    cookie, _ = await register(auth_database)
    for headers, omit in (
        ({}, True),
        ({"origin": "null"}, False),
        ({"sec-fetch-site": "cross-site"}, False),
        ({"content-type": "text/plain"}, False),
    ):
        result = await bridge(
            auth_database,
            "/sign-out",
            method="POST",
            cookie=cookie,
            headers=headers,
            omit_origin=omit,
        )
        assert result["status"] == 403
    assert (await bridge(auth_database, "/token", cookie=cookie))["status"] == 200
    public = await bridge(auth_database, "/jwks", omit_origin=True)
    assert public["status"] == 200 and public["cacheControl"] == "no-store"
    keys = object_body(public).get("keys")
    assert isinstance(keys, list) and keys
    for key in keys:
        assert isinstance(key, dict) and key["kty"] == "RSA"
        assert not {"d", "p", "q", "dp", "dq", "qi"}.intersection(key)


@pytest.mark.asyncio
async def test_expired_session_rejects_bootstrap(auth_database: AsyncEngine) -> None:
    database = auth_database
    cookie, token = await register(database)
    async with database.begin() as connection:
        await connection.execute(text('UPDATE auth.session SET "expiresAt"=CURRENT_TIMESTAMP'))
    assert (await bridge(database, "/token", cookie=cookie))["status"] == 401
    assert (await bridge(database, "/get-session", cookie=cookie))["body"] is None
    settings = make_settings(database.url.render_as_string(hide_password=False)).model_copy(
        update={
            "auth_enabled": True,
            "auth_provider": "better_auth",
            "auth_issuer": ISSUER,
            "auth_jwks_endpoint": ISSUER + "/api/auth/jwks",
            "allowed_origins": [ISSUER],
        }
    )
    keys = await jwks(database)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=keys))
        ) as public:
            app.state.token_verifier = TokenVerifier(settings, public)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://api.example.test"
            ) as client:
                response = await client.post(
                    "/api/v1/account/session", json={}, headers={"Authorization": "Bearer " + token}
                )
                assert response.status_code == 401
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(User)) is None


@pytest.mark.asyncio
async def test_atomic_durable_limits_across_processes(auth_database: AsyncEngine) -> None:
    results = await asyncio.gather(
        *[
            bridge(
                auth_database,
                "/sign-in/email",
                method="POST",
                body={"email": "missing@example.test", "password": "Synthetic-password-0001"},
            )
            for _ in range(9)
        ]
    )
    assert sum(result["status"] == 429 for result in results) >= 4
    async with auth_database.connect() as connection:
        hashes = (
            await connection.execute(text("SELECT key_hash FROM auth.request_limits"))
        ).scalars()
        assert all(len(value) == 64 and "@" not in value for value in hashes)


@pytest.mark.asyncio
async def test_bindings_preserve_owner_and_suspension(auth_database: AsyncEngine) -> None:
    from sqlalchemy.dialects.postgresql import insert

    from interview_prep.modules.identity.accounts import bootstrap_account, find_account
    from interview_prep.modules.identity.verification import VerifiedIdentity

    async with async_sessionmaker(auth_database, expire_on_commit=False)() as session:
        user = User(
            kind="account",
            issuer="https://legacy.example.test",
            subject="legacy-user",
            status=PrincipalStatus.SUSPENDED,
        )
        session.add(user)
        await session.flush()
        owner = user.id
        identity = VerifiedIdentity(ISSUER, "new-verified-user", "session-id")
        await session.execute(
            insert(PrincipalIdentity).values(
                principal_id=owner, issuer=identity.issuer, subject=identity.subject
            )
        )
        await session.commit()
        mapped = await find_account(session, identity, bindings=True)
        assert mapped and mapped.id == owner and mapped.status == PrincipalStatus.SUSPENDED
        bootstrapped = await bootstrap_account(session, identity, bindings=True)
        assert bootstrapped and bootstrapped.id == owner


@pytest.mark.asyncio
async def test_real_signer_invalid_claims_are_rejected(auth_database: AsyncEngine) -> None:
    _, token = await register(auth_database)
    original = jwt.decode(token, options={"verify_signature": False})
    keys = await jwks(auth_database)
    settings = make_settings(auth_database.url.render_as_string(hide_password=False)).model_copy(
        update={
            "auth_enabled": True,
            "auth_provider": "better_auth",
            "auth_issuer": ISSUER,
            "auth_jwks_endpoint": ISSUER + "/api/auth/jwks",
            "allowed_origins": [ISSUER],
        }
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=keys))
    ) as public:
        verifier = TokenVerifier(settings, public)
        cases: list[dict[str, object]] = [
            {"aud": "another-api"},
            {"iss": "https://attacker.example.test"},
            {"azp": "https://attacker.example.test"},
            {"sid": ""},
            {"exp": original["iat"] + 3600},
            {
                "exp": original["iat"] - 60,
                "iat": original["iat"] - 120,
                "nbf": original["iat"] - 120,
            },
            {"nbf": original["iat"] + 120},
        ]
        for overrides in cases:
            response = await bridge(auth_database, "/unused", sign={**original, **overrides})
            candidate = object_body(response).get("token")
            assert isinstance(candidate, str)
            with pytest.raises(AuthenticationError):
                await verifier.verify(candidate)
        without_session = {k: v for k, v in original.items() if k != "sid"}
        candidate = object_body(await bridge(auth_database, "/unused", sign=without_session)).get(
            "token"
        )
        assert isinstance(candidate, str)
        with pytest.raises(AuthenticationError):
            await verifier.verify(candidate)


@pytest.mark.asyncio
async def test_real_accounts_isolation_and_mismatched_session(auth_database: AsyncEngine) -> None:
    from interview_prep.modules.context.models import Resume

    database = auth_database
    _, alice_token = await register(database)
    _, bob_token = await register(database)
    alice = jwt.decode(alice_token, options={"verify_signature": False})
    bob = jwt.decode(bob_token, options={"verify_signature": False})
    keys = await jwks(database)
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
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=keys))
        ) as public:
            app.state.token_verifier = TokenVerifier(settings, public)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://api.example.test"
            ) as client:
                for token in (alice_token, bob_token):
                    client.headers["Authorization"] = "Bearer " + token
                    assert (
                        await client.post("/api/v1/account/session", json={})
                    ).status_code == 200
                async with async_sessionmaker(database, expire_on_commit=False)() as session:
                    user = await session.scalar(select(User).where(User.subject == alice["sub"]))
                    assert user
                    resume = Resume(owner_id=user.id, label="Synthetic private resume")
                    session.add(resume)
                    await session.commit()
                    resource = resume.id
                assert (await client.get(f"/api/v1/account/resumes/{resource}")).status_code == 404
                assert (
                    await client.delete(f"/api/v1/account/resumes/{resource}?expected_revision=1")
                ).status_code == 404
                client.headers["Authorization"] = "Bearer " + alice_token
                assert (await client.get(f"/api/v1/account/resumes/{resource}")).status_code == 200
                assert (await client.get("/api/v1/demo/dashboard")).status_code == 403
                mixed = object_body(
                    await bridge(database, "/unused", sign={**alice, "sid": bob["sid"]})
                ).get("token")
                assert isinstance(mixed, str)
                client.headers["Authorization"] = "Bearer " + mixed
                assert (await client.get("/api/v1/account/dashboard")).status_code == 401
                # Every registered account operation remains server-protected, not UI-only.
                client.headers.pop("Authorization")
                count = 0
                for path, operations in app.openapi()["paths"].items():
                    if not path.startswith("/api/v1/account/"):
                        continue
                    import re

                    concrete = re.sub(
                        r"\{([^}]+)\}", lambda m: "1" if m[1] == "position" else str(uuid4()), path
                    )
                    for method in operations:
                        if method not in {"get", "post", "put", "patch", "delete"}:
                            continue
                        response = await client.request(method, concrete, json={})
                        assert response.status_code == 401, (method, path, response.status_code)
                        count += 1
                assert count == 70


@pytest.mark.asyncio
async def test_runtime_privilege_separation_and_schema_drift(auth_database: AsyncEngine) -> None:
    from secrets import token_hex

    database = auth_database
    suffix = uuid4().hex[:12]
    auth_role = "auth_test_" + suffix
    api_role = "api_test_" + suffix
    password = token_hex(24)
    grants = (ROOT / "deploy/better-auth-grants.sql").read_text()
    grants = grants.replace("interview_prep_auth", auth_role).replace(
        "interview_prep_runtime", api_role
    )
    async with database.begin() as connection:
        for role in (auth_role, api_role):
            await connection.execute(text(f"CREATE ROLE \"{role}\" LOGIN PASSWORD '{password}'"))
        for sql in grants.split(";"):
            if sql.strip():
                await connection.execute(text(sql))
        assert await connection.scalar(
            text("SELECT has_table_privilege(:role, 'auth.api_sessions', 'SELECT')"),
            {"role": api_role},
        )
        for table in ("auth.account", "auth.session", "auth.jwks", 'auth."user"'):
            assert not await connection.scalar(
                text("SELECT has_table_privilege(:role, :table, 'SELECT')"),
                {"role": api_role, "table": table},
            )
        assert not await connection.scalar(
            text("SELECT has_table_privilege(:role,'public.principals','SELECT')"),
            {"role": auth_role},
        )
        assert not await connection.scalar(
            text("SELECT has_schema_privilege(:role,'auth','CREATE')"), {"role": auth_role}
        )
    # Real library operations also work under the restricted auth runtime role.
    from sqlalchemy.ext.asyncio import create_async_engine

    runtime = create_async_engine(database.url.set(username=auth_role, password=password))
    try:
        async with runtime.connect() as connection:
            assert await connection.scalar(text("SHOW search_path")) == "auth"
            assert await connection.scalar(text("SHOW statement_timeout")) == "10s"
            assert await connection.scalar(text("SHOW timezone")) == "UTC"
        cookie, token = await register(runtime)
        assert cookie and token
    finally:
        await runtime.dispose()
    result = await bridge(database, "/unused", body={"schemaCheck": True})
    # The bridge checks the official generator plan, not a hand-copied schema assertion.
    assert result["status"] == 200
    assert object_body(result) == {"missing": 0, "problems": 0}
