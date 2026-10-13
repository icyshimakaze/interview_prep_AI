from datetime import UTC, datetime, timedelta
from uuid import uuid4

from database_tools import disposable_database, migrate
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from test_seeding import MANIFEST

from interview_prep.db.models import Base
from interview_prep.seeding import load_legacy_seed


async def test_clean_upgrade_rollback_upgrade_and_drift(database: AsyncEngine) -> None:
    async with disposable_database(database.url) as url:
        result = await migrate(url, "upgrade", "head")
        assert result.returncode == 0, result.stderr
        engine = create_async_engine(url)
        try:
            async with engine.connect() as connection:
                tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
                assert set(tables) == set(Base.metadata.tables) | {"alembic_version"}
                assert await connection.scalar(text("SELECT count(*) FROM principals")) == 0
            assert (await migrate(url, "check")).returncode == 0
            result = await migrate(url, "downgrade", "base")
            assert result.returncode == 0, result.stderr
            async with engine.connect() as connection:
                assert await connection.run_sync(lambda sync: inspect(sync).get_table_names()) == [
                    "alembic_version"
                ]
                assert (
                    await connection.scalar(
                        text("SELECT count(*) FROM pg_proc WHERE proname LIKE 'relational_%'")
                    )
                    == 0
                )
            assert (await migrate(url, "upgrade", "head")).returncode == 0
            assert (await migrate(url, "check")).returncode == 0
        finally:
            await engine.dispose()


async def test_migration_preserves_existing_demo_ids_and_hashes(database: AsyncEngine) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "0001_demo_foundation")).returncode == 0
        engine = create_async_engine(url)
        owner = uuid4()
        now = datetime.now(UTC)
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text("INSERT INTO demo_workspaces VALUES (:id, :created, :expiry)"),
                    {"id": owner, "created": now, "expiry": now + timedelta(hours=24)},
                )
                await connection.execute(
                    text("INSERT INTO demo_sessions VALUES (:token, :csrf, :id)"),
                    {"id": owner, "token": "a" * 64, "csrf": "b" * 64},
                )
            for command in [
                ("upgrade", "head"),
                ("downgrade", "0001_demo_foundation"),
                ("upgrade", "head"),
            ]:
                result = await migrate(url, *command)
                assert result.returncode == 0, result.stderr
            async with engine.connect() as connection:
                assert (
                    await connection.scalar(
                        text("SELECT kind FROM principals WHERE id = :id"), {"id": owner}
                    )
                    == "demo"
                )
                assert (
                    await connection.scalar(
                        text("SELECT token_hash FROM demo_sessions WHERE workspace_id = :id"),
                        {"id": owner},
                    )
                    == "a" * 64
                )
        finally:
            await engine.dispose()


async def test_downgrade_refuses_domain_data_without_losing_it(database: AsyncEngine) -> None:
    async with disposable_database(database.url) as url:
        assert (await migrate(url, "upgrade", "head")).returncode == 0
        engine = create_async_engine(url)
        try:
            async with async_sessionmaker(engine)() as session, session.begin():
                await load_legacy_seed(session, MANIFEST)
            result = await migrate(url, "downgrade", "0001_demo_foundation")
            assert result.returncode != 0 and "Unsafe downgrade" in result.stderr
            async with engine.connect() as connection:
                assert await connection.scalar(text("SELECT count(*) FROM questions")) == 15
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0002_relational_model"
                )
        finally:
            await engine.dispose()
