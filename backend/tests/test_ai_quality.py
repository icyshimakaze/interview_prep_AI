"""Synthetic examples document lexical failure modes, not model-accuracy claims."""

import json

import httpx
import pytest
from check_ai_quality import FREE_MODEL, EvaluationCase, live_settings, load_cases, sample
from pydantic import SecretStr

from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.schemas import FollowupInput
from interview_prep.ai.xkiro import XkiroProvider
from interview_prep.core.config import Settings


@pytest.mark.parametrize("case", load_cases().cases, ids=lambda case: case.id)
async def test_synthetic_case_labels_and_lexical_limits(case: EvaluationCase) -> None:
    provider = MockAIProvider()
    result = await provider.evaluate_answer(case.content)
    assert result == await provider.evaluate_answer(case.content)
    assert result.provenance.kind == "simulation"
    assert result.data.matched_concepts == case.expected_mock_matches
    assert result.data.missing_concepts == [
        concept
        for concept in case.content.expected_concepts
        if concept not in case.expected_mock_matches
    ]
    assert result.data.score_basis == "lexical_coverage"
    assert all(
        row.score is None for row in result.data.rubric_results if row.dimension != "completeness"
    )
    followup = await provider.generate_followup(FollowupInput(**case.content.model_dump()))
    assert followup.provenance.kind == "simulation"
    assert "not an assessment" in followup.data.rationale
    assert followup.data.question != case.content.question


async def test_incorrect_keyword_answer_can_tie_strong_answer_without_validating_correctness() -> (
    None
):
    cases = {case.id: case for case in load_cases().cases}
    provider = MockAIProvider()
    strong = await provider.evaluate_answer(cases["technical_strong"].content)
    wrong = await provider.evaluate_answer(cases["technical_incorrect"].content)
    assert strong.data.score == wrong.data.score == 4
    assert "does not judge correctness" in wrong.data.overall_feedback
    assert wrong.data.rubric_results[0].score is None


async def test_live_diagnostic_is_free_pinned_and_does_not_retry_or_expose_error_body() -> None:
    settings = live_settings(
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://unused:unused@localhost/unused_test",
            demo_rate_limit_key="synthetic-quality-check-only-key-12345",
            xkiro_api_key=SecretStr("synthetic-quality-key"),
            xkiro_reasoning_model="vendor/paid-model",
            xkiro_model_routes={"evaluate_answer": "vendor/another-paid-model"},
            xkiro_allow_paid_models=True,
            ai_max_retries=2,
        )
    )
    requests = 0

    def fail(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert str(request.url) == "https://api.xkiro.com/v1/chat/completions"
        assert json.loads(request.content)["model"] == FREE_MODEL
        return httpx.Response(429, json={"error": "private provider diagnostic"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(fail)) as client:
        result = await sample(XkiroProvider(client, settings), load_cases().cases[0])
    assert requests == 1
    assert result["result"] == "failed"
    assert "private provider diagnostic" not in json.dumps(result)
    assert settings.ai_max_retries == 0 and not settings.xkiro_allow_paid_models
