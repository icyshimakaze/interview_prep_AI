from datetime import UTC, datetime, timedelta
from urllib.parse import quote
from uuid import UUID

import httpx
import pytest
from fastapi import HTTPException
from pdf_helpers import pdf_bytes
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.modules.context.models import Resume, ResumeSkillEvidence, ResumeVersion
from interview_prep.modules.demo.models import DemoWorkspace
from interview_prep.modules.demo.router import CSRF_COOKIE_NAME
from interview_prep.modules.identity.models import PrincipalStatus, User
from interview_prep.modules.resumes.service import save_upload
from interview_prep.modules.resumes.upload import ParsedPdf

BASE = "/api/v1/demo/resume-library"
ORIGIN = {"Origin": "http://localhost:3000"}


async def enter(client: httpx.AsyncClient) -> dict[str, str]:
    assert (await client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)).status_code == 200
    return {**ORIGIN, "X-CSRF-Token": client.cookies[CSRF_COOKIE_NAME]}


async def upload(client: httpx.AsyncClient, headers: dict[str, str]) -> httpx.Response:
    return await client.post(
        BASE,
        headers={
            **headers,
            "Content-Type": "application/pdf",
            "X-Resume-Filename": quote("my resume.pdf"),
        },
        content=pdf_bytes("Private contact sentinel\nPython FastAPI PostgreSQL Docker"),
    )


async def test_guest_upload_review_delete_and_exit_erases_retained_evidence(
    integration_client: httpx.AsyncClient, database: AsyncEngine, caplog: pytest.LogCaptureFixture
) -> None:
    headers = await enter(integration_client)
    original = (await integration_client.get(BASE)).json()["items"]
    assert len(original) == 1 and original[0]["is_sample"] is True
    response = await upload(integration_client, headers)
    assert response.status_code == 201, response.text
    resume = response.json()
    assert resume["is_sample"] is False and resume["label"] == "my resume.pdf"
    assert resume["page_count"] == 1 and len(resume["evidence"]) == 4
    assert "Private contact sentinel" not in response.text + caplog.text
    path = f"{BASE}/{resume['id']}"
    assert (await integration_client.get(path)).json() == resume
    assert len((await integration_client.get(BASE)).json()["items"]) == 2
    evidence = resume["evidence"][0]
    corrected = await integration_client.put(
        f"{path}/evidence/{evidence['id']}",
        headers=headers,
        json={
            "category": evidence["category"],
            "claim": "My corrected claim",
            "review_status": "confirmed",
            "expected_revision": 1,
        },
    )
    assert corrected.status_code == 200 and corrected.json()["revision"] == 2
    assert (
        await integration_client.delete(f"{path}?expected_revision=1", headers=headers)
    ).status_code == 409
    assert (
        await integration_client.delete(f"{path}?expected_revision=2", headers=headers)
    ).status_code == 204
    assert (await integration_client.get(path)).status_code == 404
    assert (await upload(integration_client, headers)).status_code == 201
    async with async_sessionmaker(database)() as session:
        versions = (
            await session.scalars(
                select(ResumeVersion).where(ResumeVersion.extraction_version != "fictional-text-v1")
            )
        ).all()
        assert versions and all(
            v.storage_key is None and v.upload_deleted_at is not None for v in versions
        )
    assert (
        await integration_client.delete("/api/v1/demo/session", headers=headers)
    ).status_code == 204
    assert (await integration_client.get(BASE)).status_code == 401
    async with async_sessionmaker(database)() as session:
        for model in (Resume, ResumeVersion, ResumeSkillEvidence):
            assert await session.scalar(select(func.count()).select_from(model)) == 0


async def test_uploads_require_capability_origin_csrf_and_reject_foreign_resources(
    integration_client: httpx.AsyncClient,
) -> None:
    assert (await upload(integration_client, ORIGIN)).status_code == 401
    first_headers = await enter(integration_client)
    assert (await upload(integration_client, ORIGIN)).status_code == 403
    assert (
        await upload(integration_client, {**first_headers, "Origin": "https://foreign.example"})
    ).status_code == 403
    first = (await upload(integration_client, first_headers)).json()
    integration_client.cookies.clear()
    headers = await enter(integration_client)
    path = f"{BASE}/{first['id']}"
    assert (await integration_client.get(path)).status_code == 404
    assert (
        await integration_client.delete(f"{path}?expected_revision=1", headers=headers)
    ).status_code == 404
    body = {"category": "tool", "claim": "Foreign claim", "expected_revision": 1}
    assert (
        await integration_client.post(f"{path}/evidence", json=body, headers=headers)
    ).status_code == 404
    evidence_path = f"{path}/evidence/{first['evidence'][0]['id']}"
    assert (
        await integration_client.put(evidence_path, json=body, headers=headers)
    ).status_code == 404
    assert (
        await integration_client.delete(f"{evidence_path}?expected_revision=1", headers=headers)
    ).status_code == 404
    assert (
        await upload(integration_client, {**headers, "Authorization": "Bearer invalid"})
    ).status_code == 403
    assert (await integration_client.get("/api/v1/account/resumes")).status_code == 401


async def test_expired_upload_access_and_failed_import_quota(
    integration_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    headers = await enter(integration_client)
    for _ in range(10):
        response = await integration_client.post(
            BASE,
            content=b"bad",
            headers={**headers, "Content-Type": "application/pdf", "X-Resume-Filename": "bad.pdf"},
        )
        assert response.status_code == 422
    assert (await upload(integration_client, headers)).status_code == 429
    async with database.begin() as connection:
        await connection.execute(
            update(DemoWorkspace).values(
                expires_at=DemoWorkspace.created_at + timedelta(microseconds=1)
            )
        )
    assert (await integration_client.get(BASE)).status_code == 401
    assert (await upload(integration_client, headers)).status_code == 401


@pytest.mark.parametrize("suspended", [False, True])
async def test_upload_cannot_finish_after_principal_expires_or_is_suspended(
    database: AsyncEngine, suspended: bool
) -> None:
    async with async_sessionmaker(database, expire_on_commit=False)() as session:
        now = datetime.now(UTC)
        user = User(
            kind="demo",
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=1),
        )
        session.add(user)
        await session.commit()
        owner: UUID = user.id
        # Authentication has already loaded this user. Another transaction revokes
        # access while parsing; the finishing upload must refresh its cached row.
        async with async_sessionmaker(database)() as changed:
            await changed.execute(
                update(User)
                .where(User.id == owner)
                .values(
                    status=PrincipalStatus.SUSPENDED if suspended else PrincipalStatus.ACTIVE,
                    expires_at=now + timedelta(hours=1) if suspended else now - timedelta(hours=1),
                )
            )
            await changed.commit()
        with pytest.raises(HTTPException) as error:
            await save_upload(
                session,
                owner,
                "late.pdf",
                b"unused",
                ParsedPdf(page_count=1, evidence=[], extraction_note=None),
            )
        assert error.value.status_code == 401
