"""Synthetic Clerk-to-Better-Auth continuity and operational rollback at schema 0013."""

import httpx
import pytest
from conftest import test_settings as make_settings
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_better_auth import ISSUER, bridge, jwks, register
from test_better_auth import auth_database as auth_database
from test_candidate_context import sign_in
from test_interviews import BASE, command, create, read, runner, seed

from interview_prep.main import create_app
from interview_prep.modules.identity.accounts import bootstrap_account
from interview_prep.modules.identity.models import PrincipalIdentity, PrincipalStatus, User
from interview_prep.modules.identity.verification import TokenVerifier, VerifiedIdentity
from interview_prep.modules.interviews.schemas import InterviewReview


async def assert_retained_review(
    client: httpx.AsyncClient, path: str, expected: InterviewReview
) -> None:
    response = await client.get(path)
    assert response.status_code == 200
    actual = InterviewReview.model_validate(response.json())
    assert actual.session.server_time >= expected.session.server_time
    # The response clock advances; every stored history field must stay identical.
    exclude = {"session": {"server_time"}}
    assert actual.model_dump(exclude=exclude) == expected.model_dump(exclude=exclude)


async def test_completed_history_survives_explicit_binding_and_provider_rollback(
    account_client: httpx.AsyncClient, auth_database: AsyncEngine
) -> None:
    database = auth_database
    await seed(database)
    await sign_in(account_client, "legacy-alice")
    interview = await command(account_client, await create(account_client, 1), "start")
    assert interview.current_turn
    answer = "Synthetic continuity answer retained across the authentication change."
    interview = await command(
        account_client,
        interview,
        f"turns/{interview.current_turn.id}/submit",
        {"answer_text": answer},
    )
    worker = runner(account_client)
    assert await worker.tick()
    interview = await read(account_client, interview)
    interview = await command(account_client, interview, "complete")
    await worker.maintenance()
    review_path = f"{BASE}/{interview.id}/review"
    original = InterviewReview.model_validate((await account_client.get(review_path)).json())
    assert original.session.status == "completed"
    assert original.turns[0].turn.answer_text == answer

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
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=public))
        ) as keys:
            verifier = TokenVerifier(settings, keys)
            identity = await verifier.verify(token)
            app.state.token_verifier = verifier
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://api.example.test",
                headers={"Authorization": "Bearer " + token},
            ) as candidate:
                # Owning a new credential does not prove ownership of a legacy principal.
                assert (await candidate.get(review_path)).status_code == 403
                async with async_sessionmaker(database)() as session, session.begin():
                    legacy = await session.scalar(
                        select(User).where(User.subject == "legacy-alice")
                    )
                    assert legacy
                    owner = legacy.id
                    # Explicit trusted synthetic mapping: neither email nor client owner input.
                    session.add(
                        PrincipalIdentity(
                            principal_id=owner, issuer=identity.issuer, subject=identity.subject
                        )
                    )
                for _ in range(2):
                    assert (
                        await candidate.post("/api/v1/account/session", json={})
                    ).status_code == 200
                await assert_retained_review(candidate, review_path, original)
                async with async_sessionmaker(database)() as session, session.begin():
                    assert await session.scalar(select(func.count()).select_from(User)) == 1
                    legacy = await session.get(User, owner)
                    assert legacy and legacy.subject == "legacy-alice"
                    legacy.status = PrincipalStatus.SUSPENDED
                assert (await candidate.get(review_path)).status_code == 403
                assert (await candidate.post("/api/v1/account/session", json={})).status_code == 403
                # Suspension is the same canonical state when operationally rolling back.
                await sign_in_suspended(account_client)
                async with async_sessionmaker(database)() as session, session.begin():
                    legacy = await session.get(User, owner)
                    assert legacy
                    legacy.status = PrincipalStatus.ACTIVE
                await assert_retained_review(candidate, review_path, original)
                assert (await bridge(database, "/sign-out", method="POST", cookie=cookie))[
                    "status"
                ] == 200
                assert (await candidate.get(review_path)).status_code == 401
                # Original Clerk identity can still read unchanged history at additive 0013.
                await sign_in(account_client, "legacy-alice")
                await assert_retained_review(account_client, review_path, original)
                await sign_in(account_client, "legacy-bob")
                assert (await account_client.get(review_path)).status_code == 404


async def sign_in_suspended(client: httpx.AsyncClient) -> None:
    from test_auth import signed_token

    client.headers["Authorization"] = "Bearer " + signed_token("legacy-alice")
    assert (await client.post("/api/v1/account/session", json={})).status_code == 403


async def test_binding_conflicts_fail_without_reassigning_principals(database: AsyncEngine) -> None:
    identity = VerifiedIdentity(ISSUER, "explicit-subject", "synthetic-session")
    async with async_sessionmaker(database, expire_on_commit=False)() as session, session.begin():
        first = User(kind="account", issuer="https://legacy.example.test", subject="first")
        second = User(kind="account", issuer="https://legacy.example.test", subject="second")
        session.add_all([first, second])
        await session.flush()
        first_id, second_id = first.id, second.id
        session.add(
            PrincipalIdentity(principal_id=first_id, issuer=ISSUER, subject=identity.subject)
        )
    async with async_sessionmaker(database)() as session:
        for principal, subject in ((second_id, identity.subject), (first_id, "different-subject")):
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    session.add(
                        PrincipalIdentity(principal_id=principal, issuer=ISSUER, subject=subject)
                    )
                    await session.flush()
        resolved = await bootstrap_account(session, identity, bindings=True)
        assert resolved and resolved.id == first_id
        assert await session.scalar(select(func.count()).select_from(User)) == 2
        assert await session.scalar(select(func.count()).select_from(PrincipalIdentity)) == 1
        await session.commit()
