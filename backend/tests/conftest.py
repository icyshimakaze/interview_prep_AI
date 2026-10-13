import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine

from interview_prep.core.config import Settings
from interview_prep.db.models import Base
from interview_prep.db.session import create_engine
from interview_prep.main import create_app


def test_settings(
    database_url: str = "postgresql+asyncpg://test:test@127.0.0.1:1/unit_test",
) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr(database_url),
        demo_rate_limit_key=SecretStr("test-only-rate-limit-key-at-least-32-characters"),
        allowed_origins=["http://localhost:3000"],
    )


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http


@pytest.fixture
def app() -> FastAPI:
    return create_app(test_settings())


@pytest_asyncio.fixture
async def database() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail(
            "Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database ending _test"
        )
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("Refusing to clear a database whose name does not end _test")
    engine = create_engine(test_settings(url))
    tables = ", ".join(f'"{table}"' for table in Base.metadata.tables)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} CASCADE"))
    yield engine
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} CASCADE"))
    await engine.dispose()


@pytest_asyncio.fixture
async def integration_client(database: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app(test_settings(database.url.render_as_string(hide_password=False)))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http
