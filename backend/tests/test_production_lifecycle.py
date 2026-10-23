import asyncio
import json
import logging
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest
from conftest import test_settings as make_settings
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from interview_prep.cleanup import periodic_cleanup
from interview_prep.db.readiness import SCHEMA_REVISION, require_production_database
from interview_prep.db.session import create_engine
from interview_prep.main import create_app
from interview_prep.modules.interviews.worker import InterviewRunner


async def test_production_startup_refuses_old_schema_without_changing_data(
    database: AsyncEngine,
) -> None:
    settings = make_settings(database.url.render_as_string(hide_password=False)).model_copy(
        update={"app_env": "production"}
    )
    async with database.begin() as connection:
        await connection.execute(text("UPDATE alembic_version SET version_num='old_schema'"))
    try:
        app = create_app(settings)
        with pytest.raises(RuntimeError, match=SCHEMA_REVISION):
            async with app.router.lifespan_context(app):
                pytest.fail("An outdated production schema must not start serving")
        async with database.connect() as connection:
            assert (
                await connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "old_schema"
            )
            assert await connection.scalar(text("SELECT count(*) FROM principals")) == 0
    finally:
        async with database.begin() as connection:
            await connection.execute(
                text("UPDATE alembic_version SET version_num=:revision"),
                {"revision": SCHEMA_REVISION},
            )


async def test_production_database_failure_has_only_safe_startup_message() -> None:
    engine = create_engine(make_settings())
    try:
        with patch(
            "interview_prep.db.readiness.verify_schema",
            side_effect=RuntimeError("private-database-sentinel"),
        ):
            with pytest.raises(RuntimeError) as error:
                await require_production_database(async_sessionmaker(engine))
        assert "private-database-sentinel" not in str(error.value)
        assert error.value.__suppress_context__
        assert "Apply reviewed migrations separately" in str(error.value)
    finally:
        await engine.dispose()


async def test_cleanup_lifecycle_and_shared_file_capacity() -> None:
    started, cancelled = asyncio.Event(), asyncio.Event()

    async def maintenance(factory: async_sessionmaker[AsyncSession]) -> None:
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    settings = make_settings().model_copy(update={"cleanup_enabled": True, "file_worker_slots": 1})
    app = create_app(settings)
    with patch("interview_prep.main.periodic_cleanup", side_effect=maintenance):
        async with app.router.lifespan_context(app):
            await asyncio.wait_for(started.wait(), 1)
            assert app.state.pdf_parser.slots is app.state.project_importer.slots
            async with app.state.project_importer.slot():
                with pytest.raises(HTTPException) as error:
                    await app.state.pdf_parser.parse(b"not executed")
                assert error.value.status_code == 503 and error.value.detail == "pdf_busy"
    assert cancelled.is_set()


async def test_periodic_cleanup_recovers_safely_without_busy_retry(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = create_engine(make_settings())
    delays: list[float] = []

    async def sleep(seconds: float) -> None:
        delays.append(seconds)
        if len(delays) == 2:
            raise asyncio.CancelledError()

    try:
        with patch(
            "interview_prep.cleanup.delete_expired",
            new=AsyncMock(side_effect=[RuntimeError("private-sentinel"), None]),
        ) as erase:
            with patch("interview_prep.cleanup.asyncio.sleep", side_effect=sleep):
                with pytest.raises(asyncio.CancelledError):
                    await periodic_cleanup(async_sessionmaker(engine))
        assert erase.await_count == 2 and delays == [3600, 3600]
        assert "private-sentinel" not in caplog.text
        assert "temporarily unavailable" in caplog.text
    finally:
        await engine.dispose()


async def test_long_idle_worker_does_not_lose_a_wakeup_during_its_tick() -> None:
    engine = create_engine(make_settings())
    first, release, second = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls = 0

    async def tick() -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            first.set()
            await release.wait()
        else:
            second.set()
        return False

    try:
        async with httpx.AsyncClient() as http:
            runner = InterviewRunner(
                async_sessionmaker(engine),
                make_settings().model_copy(update={"interview_poll_seconds": 600}),
                http,
            )
            with patch.object(runner, "tick", side_effect=tick):
                task = asyncio.create_task(runner.loop())
                try:
                    await asyncio.wait_for(first.wait(), 1)
                    runner.wake.set()
                    release.set()
                    await asyncio.wait_for(second.wait(), 1)
                finally:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
    finally:
        await engine.dispose()


async def test_request_logs_exclude_private_paths_queries_bodies_and_headers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app(make_settings())
    identifier = str(uuid4())
    with caplog.at_level(logging.INFO, logger="interview_prep.requests"):
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url="http://test"
            ) as client:
                assert (
                    await client.get(
                        "/health?secret=private-query",
                        headers={"Authorization": "Bearer private-token"},
                    )
                ).status_code == 200
                await client.get("/private-personal-path?resume=private-content")
                await client.post(
                    f"/api/v1/account/ai/resumes/{identifier}", json={"private": "private-body"}
                )
    rows = [
        json.loads(row.message) for row in caplog.records if row.name == "interview_prep.requests"
    ]
    assert len(rows) == 3
    assert {row["route"] for row in rows} == {
        "/health",
        "unmatched",
        "/api/v1/account/ai/resumes/{identifier}",
    }
    assert all(
        set(row) == {"event", "method", "route", "status", "duration_ms", "request_id"}
        for row in rows
    )
    assert all(
        "private-" not in json.dumps(row) and identifier not in json.dumps(row) for row in rows
    )


def test_production_disables_api_debug_surfaces() -> None:
    app = create_app(make_settings().model_copy(update={"app_env": "production"}))
    assert (
        not app.debug and app.docs_url is None and app.redoc_url is None and app.openapi_url is None
    )
