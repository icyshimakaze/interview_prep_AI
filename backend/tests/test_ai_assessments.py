import httpx
from sqlalchemy.ext.asyncio import AsyncEngine
from test_assessments import BASE, configuration, save, seed, start
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.ai.mock import MockAIProvider as SharedMock
from interview_prep.ai.remote import OpenAIProvider
from interview_prep.modules.assessments.evaluation import ProviderEvaluationAdapter
from interview_prep.modules.assessments.router import evaluation_provider
from interview_prep.modules.assessments.schemas import AttemptView


async def test_real_provider_bridge_persists_model_provenance_without_correctness(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client, configuration("DBMS", "medium", "written"))
    attempt = await save(account_client, attempt, answer="Indexes consume storage.")

    # An in-process provider uses the real shared schema/adapter; no credentials or HTTP.
    class FixtureProvider(SharedMock):
        name = "OpenAIProvider"
        version = "openai-responses-v1"
        model: str | None = "test-model"
        kind = OpenAIProvider.kind

    transport = account_client._transport
    assert isinstance(transport, httpx.ASGITransport)
    # ASGITransport's app is structurally callable; narrow to the actual FastAPI class.
    from fastapi import FastAPI

    app = transport.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[evaluation_provider] = lambda: ProviderEvaluationAdapter(
        FixtureProvider()
    )
    try:
        response = await account_client.post(
            f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
        )
        assert response.status_code == 200, response.text
        completed = AttemptView.model_validate(response.json())
        review = completed.questions[0].review
        assert review and review.metadata
        assert review.result_kind == "model_assisted" and review.is_correct is None
        assert review.metadata.model == "test-model"
        assert review.metadata.prompt_version == "ai-prompts-v1"
        matrix = (await account_client.get("/api/v1/account/skill-evidence")).json()
        assert not any(row["assessment_validated"] for row in matrix["rows"])
    finally:
        app.dependency_overrides.clear()
