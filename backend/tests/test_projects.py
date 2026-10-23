import asyncio
from uuid import uuid4

import httpx
import pytest
from database_tools import migrate
from fastapi import FastAPI, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in
from test_project_analysis import zipped

from interview_prep.modules.projects.defense_models import DefenseAnswer
from interview_prep.modules.projects.example import example_archive
from interview_prep.modules.projects.ingestion import ProjectImporter
from interview_prep.modules.projects.models import ProjectAnalysis, SourceFile
from interview_prep.modules.projects.schemas import DefenseView, ProjectDetail, StaticAnalysis
from interview_prep.modules.questions.models import Question

BASE = "/api/v1/account/projects"


async def project(client: httpx.AsyncClient, base: str = BASE) -> ProjectDetail:
    response = await client.post(f"{base}/example")
    assert response.status_code == 200, response.text
    return ProjectDetail.model_validate(response.json())


async def start(client: httpx.AsyncClient, item: ProjectDetail, count: int = 2) -> DefenseView:
    response = await client.post(
        f"{BASE}/{item.id}/defense",
        json={
            "command_key": str(uuid4()),
            "question_count": count,
        },
    )
    assert response.status_code == 200, response.text
    return DefenseView.model_validate(response.json())


async def command(
    client: httpx.AsyncClient,
    run: DefenseView,
    action: str,
    answer: str | None = None,
) -> DefenseView:
    response = await client.post(
        f"{BASE}/defense/{run.id}",
        json={
            "revision": run.revision,
            "action": action,
            "answer_text": answer,
        },
    )
    assert response.status_code == 200, response.text
    return DefenseView.model_validate(response.json())


async def test_project_persistence_dedup_provenance_and_delete(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    item = await project(account_client)
    assert (await project(account_client)).id == item.id
    assert item.example and len(item.questions) == 10
    assert item.questions[0].focus == "Framework choice"
    uploaded = await account_client.post(
        f"{BASE}/zip",
        content=example_archive(),
        headers={"Content-Type": "application/zip"},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["id"] != str(item.id) and not uploaded.json()["example"]
    run = await start(account_client, item)
    run = await command(account_client, run, "submit", "I validated the generated code.")
    read = await account_client.get(f"{BASE}/defense/{run.id}")
    assert read.json()["responses"][0]["answer_text"] == "I validated the generated code."
    async with async_sessionmaker(database)() as session:
        assert all(v is None for v in (await session.scalars(select(SourceFile.retained_text))))
        assert all(
            v is None for v in (await session.scalars(select(ProjectAnalysis.archive_storage_key)))
        )
    assert (await account_client.delete(f"{BASE}/{item.id}")).status_code == 204
    assert (await account_client.get(f"{BASE}/defense/{run.id}")).status_code == 404
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(DefenseAnswer)) == 0
        assert await session.scalar(select(func.count()).select_from(Question)) == 10


async def test_project_ownership_and_revision_state_machine(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client, "alice")
    item = await project(account_client)
    run = await start(account_client, item)
    await sign_in(account_client, "bob")
    assert (await account_client.get(BASE)).json() == {"items": []}
    for path in [f"/{item.id}", f"/{item.id}/defense", f"/defense/{run.id}"]:
        assert (await account_client.get(BASE + path)).status_code == 404
    assert (await account_client.delete(f"{BASE}/{item.id}")).status_code == 404
    assert (
        await account_client.post(
            f"{BASE}/defense/{run.id}",
            json={
                "revision": 1,
                "action": "end",
            },
        )
    ).status_code == 404
    await sign_in(account_client, "alice")
    results = await asyncio.gather(
        *[
            account_client.post(
                f"{BASE}/defense/{run.id}",
                json={
                    "revision": 1,
                    "action": "save",
                    "answer_text": answer,
                },
            )
            for answer in ["one", "two"]
        ]
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    run = DefenseView.model_validate(next(r for r in results if r.status_code == 200).json())
    run = await command(account_client, run, "pause", "saved paused draft")
    assert run.status == "paused"
    denied = await account_client.post(
        f"{BASE}/defense/{run.id}",
        json={
            "revision": run.revision,
            "action": "submit",
            "answer_text": "overwrite",
        },
    )
    assert denied.status_code == 409
    run = await command(account_client, run, "resume")
    run = await command(account_client, run, "submit")
    assert run.responses[0].answer_text == "saved paused draft"
    run = await command(account_client, run, "skip", "Partial idea")
    assert run.status == "completed" and run.completed_at
    assert run.responses[1].answer_text == "Partial idea"
    async with async_sessionmaker(database)() as session:
        with pytest.raises(IntegrityError):
            await session.execute(
                text("UPDATE project_defense_answers SET answer_text='changed' WHERE run_id=:run"),
                {"run": run.id},
            )
        await session.rollback()
    history = await account_client.get(f"{BASE}/{item.id}/defense")
    assert history.json()["items"][0]["status"] == "completed"


async def test_project_import_failure_preserves_saved_answer(
    account_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await sign_in(account_client)
    item = await project(account_client)
    run = await command(account_client, await start(account_client, item), "save", "Keep this")

    async def fail(self: ProjectImporter, data: bytes) -> StaticAnalysis:
        raise HTTPException(503, detail="project_worker_unavailable")

    monkeypatch.setattr(ProjectImporter, "parse", fail)
    response = await account_client.post(f"{BASE}/example")
    assert response.status_code == 503
    assert (await account_client.get(f"{BASE}/defense/{run.id}")).json()["responses"][0][
        "answer_text"
    ] == "Keep this"
    assert len((await account_client.get(BASE)).json()["items"]) == 1
    assert (await account_client.post(f"{BASE}/zip", content=b"bad")).status_code == 415


async def test_project_quota_and_start_replay(account_client: httpx.AsyncClient) -> None:
    await sign_in(account_client)
    item = await project(account_client)
    body = {"command_key": str(uuid4()), "question_count": 1}
    first = await account_client.post(f"{BASE}/{item.id}/defense", json=body)
    assert (
        await account_client.post(f"{BASE}/{item.id}/defense", json=body)
    ).json() == first.json()
    assert (
        await account_client.post(
            f"{BASE}/{item.id}/defense",
            json={**body, "question_count": 2},
        )
    ).status_code == 409
    for i in range(5):
        response = await account_client.post(
            f"{BASE}/zip",
            content=zipped({"app.py": f"x = {i}"}),
            headers={"Content-Type": "application/zip"},
        )
        assert response.status_code == (200 if i < 4 else 409), response.text


async def test_project_demo_csrf_isolation_and_no_provider(
    integration_client: httpx.AsyncClient,
) -> None:
    client = integration_client
    client.headers["Origin"] = "http://localhost:3000"
    response = await client.post("/api/v1/demo/sessions", json={})
    assert response.status_code in (200, 201), response.text
    base = "/api/v1/demo/projects"
    assert (await client.post(f"{base}/example")).status_code == 403
    csrf = client.cookies.get("interview_prep_csrf")
    assert csrf
    client.headers["X-CSRF-Token"] = csrf
    transport = client._transport
    assert isinstance(transport, httpx.ASGITransport) and isinstance(transport.app, FastAPI)
    transport.app.state.ai_provider = None
    item = await project(client, base)
    assert item.example
    client.cookies.clear()
    assert (await client.get(f"{base}/{item.id}")).status_code == 401


async def test_project_populated_downgrade_preserves_snapshot_and_answer(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    item = await project(account_client)
    run = await command(account_client, await start(account_client, item), "submit", "Keep history")
    # Let the newer quota migration roll back so this case still exercises the
    # Project Defense migration's independent historical-data refusal.
    async with database.begin() as connection:
        await connection.execute(
            text("UPDATE operation_quotas SET expires_at = now() - interval '1 hour'")
        )
    result = await migrate(
        database.url.render_as_string(hide_password=False),
        "downgrade",
        "0007_mock_interviews",
    )
    assert result.returncode != 0 and "Refusing to discard project defense data" in result.stderr
    assert (await account_client.get(f"{BASE}/{item.id}")).status_code == 200
    saved = DefenseView.model_validate(
        (await account_client.get(f"{BASE}/defense/{run.id}")).json()
    )
    assert saved.responses[0].answer_text == "Keep history"
    async with database.connect() as connection:
        assert await connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0012_ai_context_reviews"
        )
