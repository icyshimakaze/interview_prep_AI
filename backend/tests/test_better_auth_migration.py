"""Data-preserving auth migration and compatibility readiness, disposable DB only."""

import httpx
import pytest
from conftest import test_settings as make_settings
from database_tools import disposable_database, migrate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from test_auth import ISSUER, jwk, signed_token

from interview_prep.db.readiness import verify_schema
from interview_prep.main import create_app
from interview_prep.modules.identity.accounts import bootstrap_account, find_account
from interview_prep.modules.identity.verification import TokenVerifier, VerifiedIdentity


@pytest.mark.asyncio
@pytest.mark.parametrize("revision", ["0012_ai_context_reviews", "0013_better_auth"])
async def test_clerk_compatibility_and_demo_ownership(database: AsyncEngine, revision: str) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", revision)).returncode == 0
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                demo = await connection.scalar(
                    text(
                        "INSERT INTO principals(kind,expires_at) VALUES "
                        "('demo',CURRENT_TIMESTAMP + interval '1 day') RETURNING id"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO candidate_profiles(owner_id,target_role,"
                        "experience_band,timezone,weekly_minutes,revision) VALUES "
                        "(:owner,'Demo only','entry','UTC',300,1)"
                    ),
                    {"owner": demo},
                )
            settings = make_settings(url).model_copy(
                update={"auth_enabled": True, "auth_issuer": ISSUER}
            )
            app = create_app(settings)
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.MockTransport(
                        lambda _: httpx.Response(200, json={"keys": [jwk()]})
                    )
                ) as keys:
                    app.state.token_verifier = TokenVerifier(settings, keys)
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app),
                        base_url="http://test",
                        headers={"Authorization": "Bearer " + signed_token()},
                    ) as client:
                        assert (
                            await client.post("/api/v1/account/session", json={})
                        ).status_code == 200
                        dashboard = await client.get("/api/v1/account/dashboard")
                        assert dashboard.status_code == 200 and dashboard.json()["profile"] is None
                        assert (await client.get("/api/v1/demo/dashboard")).status_code == 403
            async with async_sessionmaker(engine)() as session:
                if revision == "0013_better_auth":
                    identity = VerifiedIdentity(
                        "https://new.example.test", "synthetic-new", "session"
                    )
                    user = await bootstrap_account(session, identity, bindings=True)
                    assert user and user.id != demo
                    assert await find_account(session, identity, bindings=True) is user
                    await session.commit()
                row = (
                    await session.execute(
                        text(
                            "SELECT p.kind,c.owner_id,c.target_role,c.revision "
                            "FROM principals p JOIN candidate_profiles c ON c.owner_id=p.id "
                            "WHERE p.id=:demo"
                        ),
                        {"demo": demo},
                    )
                ).one()
                assert tuple(row) == ("demo", demo, "Demo only", 1)
                if revision == "0013_better_auth":
                    assert (
                        await session.scalar(
                            text(
                                "SELECT count(*) FROM principal_identities WHERE principal_id=:demo"
                            ),
                            {"demo": demo},
                        )
                        == 0
                    )
        finally:
            await engine.dispose()


@pytest.mark.asyncio
async def test_auth_migration_backfill_and_safe_rollback(database: AsyncEngine) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0012_ai_context_reviews")).returncode == 0
        engine = create_async_engine(url)
        try:
            async with async_sessionmaker(engine)() as session:
                assert await verify_schema(session) == "0012_ai_context_reviews"
                with pytest.raises(ValueError, match="schema mismatch"):
                    await verify_schema(session, require_auth=True)
            async with engine.begin() as connection:
                owner = await connection.scalar(
                    text(
                        "INSERT INTO principals(kind,issuer,subject) VALUES "
                        "('account','https://legacy.example.test','original') RETURNING id"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO candidate_profiles(owner_id,target_role,experience_band,"
                        "timezone,weekly_minutes,revision) VALUES (:owner,'Original role','entry',"
                        "'UTC',300,5)"
                    ),
                    {"owner": owner},
                )
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT principal_id FROM principal_identities"))
                    == owner
                )
                row = (
                    await connection.execute(
                        text("SELECT owner_id,target_role,revision FROM candidate_profiles")
                    )
                ).one()
                assert tuple(row) == (owner, "Original role", 5)
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        'INSERT INTO auth."user"(id,name,email,"emailVerified") VALUES '
                        "('synthetic','Synthetic','synthetic@example.test',false)"
                    )
                )
            assert (await migrate(url, "downgrade", "0012_ai_context_reviews")).returncode != 0
            async with engine.begin() as connection:
                assert await connection.scalar(text('SELECT count(*) FROM auth."user"')) == 1
                await connection.execute(text("DELETE FROM auth.\"user\" WHERE id='synthetic'"))
            assert (await migrate(url, "downgrade", "0012_ai_context_reviews")).returncode == 0
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(text("SELECT owner_id FROM candidate_profiles"))
                    == owner
                )
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            assert (await migrate(url, "check")).returncode == 0
        finally:
            await engine.dispose()
