from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from interview_prep.db.session import get_session


async def test_liveness_does_not_require_database(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "interview-prep-api"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


async def test_unavailable_database_returns_safe_503(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "unavailable"
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "postgresql" not in response.text
    assert "test:test" not in response.text


async def test_postgres_and_migration_readiness(integration_client: AsyncClient) -> None:
    response = await integration_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"
    assert response.json()["schema_revision"] == "0004_resume_evidence"


async def test_foreign_origin_has_no_cors_permission(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


async def test_unexpected_failure_is_sanitized_and_never_cached(app: FastAPI) -> None:
    async def broken_session() -> AsyncSession:
        raise RuntimeError("sensitive-database-password")

    app.dependency_overrides[get_session] = broken_session
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
        ) as http:
            response = await http.get("/api/v1/health/ready")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "sensitive-database-password" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"] == response.json()["request_id"]


async def test_schema_mismatch_returns_503(
    integration_client: AsyncClient, database: AsyncEngine
) -> None:
    async with database.begin() as connection:
        await connection.execute(text("UPDATE alembic_version SET version_num = 'wrong_revision'"))
    try:
        response = await integration_client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert "wrong_revision" not in response.text
    finally:
        async with database.begin() as connection:
            await connection.execute(
                text("UPDATE alembic_version SET version_num = '0004_resume_evidence'")
            )


async def test_database_timeout_is_recoverable_without_exposing_details(app: FastAPI) -> None:
    async def timed_out_session() -> AsyncSession:
        raise TimeoutError("sensitive connection details")

    app.dependency_overrides[get_session] = timed_out_session
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            response = await http.get("/api/v1/health/ready")
    assert response.status_code == 503 and response.json()["code"] == "unavailable"
    assert "sensitive" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"] == response.json()["request_id"]
