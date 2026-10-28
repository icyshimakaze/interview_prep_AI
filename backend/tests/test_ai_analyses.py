import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in
from test_projects import command, project, start
from test_resumes import upload
from test_xkiro import quoted_document, wire
from test_xkiro import settings as xkiro_settings

from interview_prep.ai.analysis_models import AIAnalysis
from interview_prep.ai.mock import MockAIProvider, evaluate
from interview_prep.ai.schemas import AnswerInput, ResumeInput
from interview_prep.ai.xkiro import XkiroProvider
from interview_prep.core.security_models import OperationQuota
from interview_prep.modules.demo.service import delete_expired
from interview_prep.modules.identity.models import User

BASE = "/api/v1/account/ai"


def application(client: httpx.AsyncClient) -> FastAPI:
    assert isinstance(client._transport, httpx.ASGITransport)
    app = client._transport.app
    assert isinstance(app, FastAPI)
    return app


async def consent(client: httpx.AsyncClient) -> dict[str, object]:
    response = await client.get(f"{BASE}/options")
    assert response.status_code == 200, response.text
    return {"consent": True, "provider_version": response.json()["version"]}


async def test_resume_sharing_requires_account_consent_and_owned_source(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    path = f"{BASE}/resumes/{uuid4()}"
    assert (await account_client.get(f"{BASE}/options")).status_code == 401
    assert (await account_client.post(path, json={})).status_code == 401
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    path = f"{BASE}/resumes/{resume['id']}"
    body = await consent(account_client)
    assert (await account_client.post(path, json={})).status_code == 422
    assert (await account_client.post(path, json={**body, "consent": False})).status_code == 422
    assert (
        await account_client.post(path, json={**body, "owner_id": str(uuid4())})
    ).status_code == 422
    assert (
        await account_client.post(path, json={**body, "provider_version": "changed"})
    ).status_code == 409
    result = await account_client.post(path, json=body)
    assert result.status_code == 200, result.text
    assert result.json()["provenance"]["kind"] == "simulation"
    assert (await account_client.post(path, json=body)).json() == result.json()
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 1
        assert (
            await session.scalar(select(func.count()).select_from(OperationQuota)) == 2
        )  # upload only
    await sign_in(account_client, "bob")
    assert (await account_client.post(path, json=body)).status_code == 404


async def test_mocked_xkiro_saved_result_reused_without_new_budget_or_call(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    app = application(account_client)
    calls: list[httpx.Request] = []

    async def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        payload = json.loads(request.content)
        user = json.loads(payload["messages"][1]["content"])
        fixture = await MockAIProvider().analyze_resume(ResumeInput.model_validate(user))
        return httpx.Response(200, json=wire(quoted_document(fixture.data), payload["model"]))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        app.state.ai_provider = XkiroProvider(http, xkiro_settings())
        options = (await account_client.get(f"{BASE}/options")).json()
        assert "xKiro and its downstream" in options["disclosure"]
        body = await consent(account_client)
        path = f"{BASE}/resumes/{resume['id']}"
        first = await account_client.post(path, json=body)
        assert first.status_code == 200, first.text
        assert first.json()["provenance"]["provider"] == "XkiroProvider"
        assert first.json()["provenance"]["kind"] == "model_assisted"
        again = await account_client.post(path, json=body)
        assert again.json() == first.json() and len(calls) == 1
        async with async_sessionmaker(database)() as session:
            before = list(
                await session.scalars(
                    select(OperationQuota.count).order_by(OperationQuota.key_hash)
                )
            )
        await account_client.post(path, json=body)
        async with async_sessionmaker(database)() as session:
            after = list(
                await session.scalars(
                    select(OperationQuota.count).order_by(OperationQuota.key_hash)
                )
            )
        assert before == after
        # Editing the evidence changes content identity and requests new feedback.
        added = await account_client.post(
            f"/api/v1/account/resumes/{resume['id']}/evidence",
            json={
                "claim": "I tested an SQL database.",
                "category": "database",
                "review_status": "confirmed",
                "expected_revision": resume["revision"],
            },
        )
        assert added.status_code == 201, added.text
        assert (await account_client.post(path, json=body)).status_code == 200
        assert len(calls) == 2
        removed = await account_client.delete(
            f"/api/v1/account/resumes/{resume['id']}?expected_revision={added.json()['revision']}"
        )
        assert removed.status_code == 204, removed.text
        async with async_sessionmaker(database)() as session:
            assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 0


async def test_invalid_remote_output_retries_explicitly_with_bound_and_no_mock_fallback(
    account_client: httpx.AsyncClient,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    calls = 0

    def invalid(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=wire("{malformed"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(invalid)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, xkiro_settings())
        body = await consent(account_client)
        path = f"{BASE}/resumes/{resume['id']}"
        for _ in range(2):
            failed = await account_client.post(path, json=body)
            assert failed.status_code == 503 and failed.json()["code"] == "ai_invalid_output"
        assert (await account_client.post(path, json=body)).status_code == 409
        assert calls == 2


async def test_owner_quota_prevents_dispatch_and_other_owner_isolated(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    app = application(account_client)
    configured = app.state.settings.model_copy(update={"ai_owner_hourly_calls": 1})
    app.state.settings = configured  # reserves two units; budget cannot cover one dispatch
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: pytest.fail("Budget exceeded"))
    ) as http:
        app.state.ai_provider = XkiroProvider(http, xkiro_settings())
        result = await account_client.post(
            f"{BASE}/resumes/{resume['id']}", json=await consent(account_client)
        )
        assert result.status_code == 429 and int(result.headers["Retry-After"]) > 0
        async with async_sessionmaker(database)() as session:
            assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 0


async def test_concurrent_request_fences_duplicate_dispatch(
    account_client: httpx.AsyncClient,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def slow(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        entered.set()
        await release.wait()
        data = json.loads(json.loads(request.content)["messages"][1]["content"])
        fixture = await MockAIProvider().analyze_resume(ResumeInput.model_validate(data))
        return httpx.Response(200, json=wire(quoted_document(fixture.data)))

    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, xkiro_settings())
        body = await consent(account_client)
        path = f"{BASE}/resumes/{resume['id']}"
        first = asyncio.create_task(account_client.post(path, json=body))
        await asyncio.wait_for(entered.wait(), 5)
        try:
            duplicate = await account_client.post(path, json=body)
            assert duplicate.status_code == 409
        finally:
            release.set()
        assert (await first).status_code == 200 and calls == 1


@pytest.mark.parametrize("old_fails", [False, True])
async def test_replaced_receipt_cannot_be_overwritten_by_old_dispatch(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    old_fails: bool,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    entered = [asyncio.Event(), asyncio.Event()]
    release = [asyncio.Event(), asyncio.Event()]
    calls = 0

    async def slow(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        index = calls
        calls += 1
        entered[index].set()
        await release[index].wait()
        if index == 0 and old_fails:
            return httpx.Response(200, json=wire("{malformed"))
        data = json.loads(json.loads(request.content)["messages"][1]["content"])
        fixture = await MockAIProvider().analyze_resume(ResumeInput.model_validate(data))
        return httpx.Response(200, json=wire(quoted_document(fixture.data)))

    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, xkiro_settings())
        body = await consent(account_client)
        path = f"{BASE}/resumes/{resume['id']}"
        old = asyncio.create_task(account_client.post(path, json=body))
        replacement: asyncio.Task[httpx.Response] | None = None
        try:
            await asyncio.wait_for(entered[0].wait(), 5)
            # Simulate expiry/invalidation removing an in-flight receipt.
            async with async_sessionmaker(database)() as session:
                await session.execute(delete(AIAnalysis))
                await session.commit()
            replacement = asyncio.create_task(account_client.post(path, json=body))
            await asyncio.wait_for(entered[1].wait(), 5)
            release[0].set()
            assert (await old).status_code == (503 if old_fails else 404)
            async with async_sessionmaker(database)() as session:
                receipt = await session.scalar(select(AIAnalysis))
                assert receipt and receipt.state == "started" and receipt.result is None
            release[1].set()
            completed = await replacement
            assert completed.status_code == 200, completed.text
            assert (await account_client.post(path, json=body)).json() == completed.json()
            assert calls == 2
        finally:
            for event in release:
                event.set()
            await old
            if replacement:
                await replacement


async def test_defense_saved_answer_feedback_reuses_result_and_preserves_practice(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    item = await project(account_client)
    run = await start(account_client, item)
    path = f"{BASE}/defense/{run.id}/1"
    assert (await account_client.post(path, json=await consent(account_client))).status_code == 404
    run = await command(account_client, run, "submit", "I validated error paths with tests.")
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        content = AnswerInput.model_validate_json(body["messages"][1]["content"])
        data = evaluate(content).model_dump()
        data["score_basis"] = "rubric_mean"
        data["rubric_results"][0]["score"] = 0
        return httpx.Response(200, json=wire(json.dumps(data), body["model"]))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, xkiro_settings())
        body = await consent(account_client)
        result = await account_client.post(path, json=body)
        assert result.status_code == 200, result.text
        assert result.json()["data"]["profile"] == "technical"
        assert result.json()["provenance"]["kind"] == "model_assisted"
        assert (await account_client.post(path, json=body)).json() == result.json() and calls == 1
        unchanged = await account_client.get(f"/api/v1/account/projects/defense/{run.id}")
        assert unchanged.json()["revision"] == run.revision
        await sign_in(account_client, "bob")
        assert (await account_client.post(path, json=body)).status_code == 404
        assert calls == 1


async def test_analysis_expiry_and_composite_owner_constraint(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    resume = (await upload(account_client)).json()
    await account_client.post(f"{BASE}/resumes/{resume['id']}", json=await consent(account_client))
    async with async_sessionmaker(database)() as session:
        receipt = await session.scalar(select(AIAnalysis))
        assert receipt
        receipt.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()
        await delete_expired(session)
        assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 0
        other = User(kind="account", issuer="https://test.invalid", subject="other-owner")
        session.add(other)
        await session.flush()
        session.add(
            AIAnalysis(
                owner_id=other.id,
                input_key="a" * 64,
                resume_id=UUID(resume["id"]),
                attempts=1,
                state="started",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
