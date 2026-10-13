import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.modules.demo.models import DemoSession, DemoWorkspace
from interview_prep.modules.demo.router import COOKIE_NAME, CSRF_COOKIE_NAME
from interview_prep.modules.demo.service import delete_expired, hash_token

ORIGIN = {"Origin": "http://localhost:3000"}


async def test_creation_rejects_missing_or_foreign_origin(client: AsyncClient) -> None:
    for headers in ({}, {"Origin": "https://evil.example"}):
        response = await client.post("/api/v1/demo/sessions", json={}, headers=headers)
        assert response.status_code == 403


async def test_demo_rejects_account_bearer(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/demo/workspace", headers={"Authorization": "Bearer invalid-account-token"}
    )
    assert response.status_code == 403


async def test_untrusted_owner_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/demo/sessions", json={"owner_id": "forged"}, headers=ORIGIN
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("token", [None, "forged", "a" * 43, "é" * 43, "x" * 10000])
async def test_invalid_credentials(integration_client: AsyncClient, token: str | None) -> None:
    if token is not None:
        # Use ASCII-safe escaped values for the non-ASCII malformed credential case.
        integration_client.cookies.set(
            COOKIE_NAME, token.encode("ascii", errors="backslashreplace").decode()
        )
    assert (await integration_client.get("/api/v1/demo/workspace")).status_code == 401


async def test_two_visitors_are_isolated_and_tokens_are_hashed(
    integration_client: AsyncClient, database: AsyncEngine
) -> None:
    first = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert first.status_code == 200
    first_token = integration_client.cookies[COOKIE_NAME]
    assert "HttpOnly" in first.headers.get_list("set-cookie")[0]
    assert "SameSite=lax" in first.headers.get_list("set-cookie")[0]
    assert (await integration_client.get("/api/v1/demo/workspace")).json()["id"] == first.json()[
        "id"
    ]

    integration_client.cookies.clear()
    second = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert (await integration_client.get("/api/v1/demo/workspace")).json()["id"] == second.json()[
        "id"
    ]
    assert (
        await integration_client.get(f"/api/v1/demo/workspace/{first.json()['id']}")
    ).status_code == 404

    async with async_sessionmaker(database)() as session:
        hashes = (await session.scalars(select(DemoSession.token_hash))).all()
        assert hash_token(first_token) in hashes
        assert first_token not in hashes
        assert len(hashes) == 2


async def test_repeated_creation_requires_csrf_and_reuses_workspace(
    integration_client: AsyncClient,
) -> None:
    created = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    forbidden = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert forbidden.status_code == 403
    repeated = await integration_client.post(
        "/api/v1/demo/sessions",
        json={},
        headers={**ORIGIN, "X-CSRF-Token": integration_client.cookies[CSRF_COOKIE_NAME]},
    )
    assert repeated.status_code == 200
    assert created.json()["id"] == repeated.json()["id"]


async def test_demo_creation_quota(integration_client: AsyncClient) -> None:
    for _ in range(2):
        integration_client.cookies.clear()
        assert (
            await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
        ).status_code == 200
    integration_client.cookies.clear()
    response = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert response.status_code == 429


async def test_concurrent_creation_cannot_exceed_quota(integration_client: AsyncClient) -> None:
    responses = await asyncio.gather(
        *[
            integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
            for _ in range(4)
        ]
    )
    assert sorted(response.status_code for response in responses) == [200, 200, 429, 429]


async def test_expired_workspace_denied_then_cleanup_cascades(
    integration_client: AsyncClient, database: AsyncEngine
) -> None:
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    past = datetime.now(UTC) - timedelta(days=2)
    async with async_sessionmaker(database)() as session:
        await session.execute(
            update(DemoWorkspace).values(created_at=past, expires_at=past + timedelta(days=1))
        )
        await session.commit()
    assert (await integration_client.get("/api/v1/demo/workspace")).status_code == 401
    async with async_sessionmaker(database)() as session:
        await delete_expired(session)
        assert await session.scalar(text("SELECT count(*) FROM demo_workspaces")) == 0
        assert await session.scalar(text("SELECT count(*) FROM demo_sessions")) == 0
