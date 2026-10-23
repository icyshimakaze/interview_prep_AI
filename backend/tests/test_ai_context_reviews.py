import json
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import httpx
import pytest
from database_tools import migrate
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_ai_analyses import BASE, application, consent
from test_auth import account_client as account_client
from test_candidate_context import JOB, sign_in
from test_personal_roadmaps import generate
from test_projects import project
from test_xkiro import quoted_document, settings, wire

from interview_prep.ai.analysis_models import AIAnalysis
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.schemas import JobInput, ProjectInput, RoadmapInput
from interview_prep.ai.xkiro import XkiroProvider
from interview_prep.core.security_models import OperationQuota
from interview_prep.modules.context.models import TargetJob, TargetJobVersion
from interview_prep.modules.identity.models import User
from interview_prep.modules.projects.models import ProjectAnalysis
from interview_prep.modules.roadmaps.models import Roadmap as SavedPlan

Kind = Literal["targets", "roadmaps", "projects"]


async def source(client: httpx.AsyncClient, kind: Kind) -> tuple[str, UUID]:
    if kind == "targets":
        result = await client.post("/api/v1/account/targets", json=JOB)
        assert result.status_code == 201
        return result.json()["id"], UUID(result.json()["id"])
    if kind == "projects":
        detail = await project(client)
        return str(detail.id), detail.analysis_id
    state = await generate(client)
    assert state.current
    return str(state.current.id), state.current.id


@pytest.mark.parametrize("kind", ["targets", "roadmaps", "projects"])
async def test_context_reviews_consent_ownership_cache_quota_and_cascade(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    kind: Kind,
) -> None:
    assert (await account_client.post(f"{BASE}/{kind}/{uuid4()}", json={})).status_code == 401
    await sign_in(account_client)
    identifier, source_id = await source(account_client, kind)
    path = f"{BASE}/{kind}/{identifier}"
    calls = 0

    async def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        payload = json.loads(request.content)
        data = json.loads(payload["messages"][1]["content"])
        assert identifier not in json.dumps(data)  # No owner/source IDs shared.
        mock = MockAIProvider()
        if kind == "targets":
            job = await mock.analyze_job_description(JobInput.model_validate(data))
            output = quoted_document(job.data)
        elif kind == "roadmaps":
            content = RoadmapInput.model_validate(data)
            assert content.context and "reason" in content.context
            assert content.weekly_minutes <= 600
            output = (await mock.recommend_roadmap(content)).data.model_dump_json()
        else:
            project_input = ProjectInput.model_validate(data)
            assert "Observed" in project_input.text and " at " in project_input.text
            assert "retained_text" not in project_input.text
            assert project_input.question_count == 6
            output = (await mock.generate_project_questions(project_input)).data.model_dump_json()
        return httpx.Response(200, json=wire(output, payload["model"]))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, settings())
        body = await consent(account_client)
        assert (await account_client.post(path, json={**body, "consent": False})).status_code == 422
        assert (
            await account_client.post(path, json={**body, "owner_id": str(uuid4())})
        ).status_code == 422
        assert (
            await account_client.post(path, json={**body, "provider_version": "old"})
        ).status_code == 409
        before = (await account_client.get("/api/v1/account/dashboard")).json()
        response = await account_client.post(path, json=body)
        assert response.status_code == 200, response.text
        assert response.json()["provenance"]["kind"] == "model_assisted"
        async with async_sessionmaker(database)() as session:
            quota = list(
                await session.scalars(
                    select(OperationQuota.count).order_by(OperationQuota.key_hash)
                )
            )
        assert (await account_client.post(path, json=body)).json() == response.json()
        assert calls == 1
        assert (await account_client.get("/api/v1/account/dashboard")).json() == before
        async with async_sessionmaker(database)() as session:
            assert (
                list(
                    await session.scalars(
                        select(OperationQuota.count).order_by(OperationQuota.key_hash)
                    )
                )
                == quota
            )
            assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 1
        await sign_in(account_client, "bob")
        assert (await account_client.post(path, json=body)).status_code == 404
        assert calls == 1
    async with async_sessionmaker(database)() as session:
        if kind == "targets":
            await session.execute(delete(TargetJob).where(TargetJob.id == source_id))
        elif kind == "projects":
            await session.execute(delete(ProjectAnalysis).where(ProjectAnalysis.id == source_id))
        else:
            await session.execute(delete(SavedPlan).where(SavedPlan.id == source_id))
        await session.commit()
        assert await session.scalar(select(func.count()).select_from(AIAnalysis)) == 0


@pytest.mark.parametrize("kind", ["targets", "roadmaps", "projects"])
async def test_context_invalid_output_is_bounded_and_source_remains(
    account_client: httpx.AsyncClient,
    kind: Kind,
) -> None:
    await sign_in(account_client)
    identifier, _ = await source(account_client, kind)
    calls = 0

    def invalid(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=wire('{"unchecked":"output"}'))

    async with httpx.AsyncClient(transport=httpx.MockTransport(invalid)) as http:
        application(account_client).state.ai_provider = XkiroProvider(http, settings())
        body = await consent(account_client)
        path = f"{BASE}/{kind}/{identifier}"
        for _ in range(2):
            result = await account_client.post(path, json=body)
            assert result.status_code == 503 and result.json()["code"] == "ai_invalid_output"
        assert (await account_client.post(path, json=body)).status_code == 409
        assert calls == 2
    endpoint = (
        "/api/v1/account/roadmap" if kind == "roadmaps" else f"/api/v1/account/{kind}/{identifier}"
    )
    assert (await account_client.get(endpoint)).status_code == 200


async def test_context_receipt_ownership_and_nondestructive_downgrade(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    identifier, _ = await source(account_client, "targets")
    async with async_sessionmaker(database)() as session:
        version = await session.scalar(
            select(TargetJobVersion).where(TargetJobVersion.target_job_id == UUID(identifier))
        )
        assert version
        other = User(issuer="https://test.invalid", subject="other", kind="account")
        session.add(other)
        await session.flush()
        session.add(
            AIAnalysis(
                owner_id=other.id,
                input_key="a" * 64,
                target_version_id=version.id,
                attempts=1,
                state="started",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
    result = await account_client.post(
        f"{BASE}/targets/{identifier}", json=await consent(account_client)
    )
    assert result.status_code == 200
    rollback = await migrate(
        database.url.render_as_string(hide_password=False), "downgrade", "0011_ai_analyses"
    )
    assert rollback.returncode != 0 and "context reviews exist" in rollback.stderr
    assert (
        await account_client.post(
            f"{BASE}/targets/{identifier}", json=await consent(account_client)
        )
    ).json() == result.json()
