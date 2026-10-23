import asyncio
import base64
import json
from typing import get_args

import httpx
import pytest
from conftest import test_settings as make_settings
from pydantic import ValidationError
from test_ai_providers import ANSWER, RESUME, all_results

from interview_prep.ai.errors import (
    InvalidProviderOutput,
    ProviderRateLimited,
    ProviderRefusal,
    ProviderTimeout,
    ProviderUnavailable,
)
from interview_prep.ai.factory import create_provider
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.schemas import (
    JobAnalysis,
    JobInput,
    Operation,
    ResumeAnalysis,
    ResumeInput,
    SkillMention,
)
from interview_prep.ai.xkiro import ImageInput, XkiroProvider
from interview_prep.core.config import Settings

FREE = "qwen/qwen3.8-max:free"
OMNI = "qwen/qwen3.8-omni-flash:free"
TEST_KEY = "fictional-unit-test-credential-never-real"


def settings(**updates: object) -> Settings:
    values = make_settings().model_dump()
    values.update(ai_provider="xkiro", xkiro_api_key=TEST_KEY, ai_max_retries=0)
    values.update(updates)
    return Settings(_env_file=None, **values)


def wire(text: str, model: str = FREE, finish: str = "stop") -> dict[str, object]:
    return {
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish,
                "message": {
                    "role": "assistant",
                    "content": text,
                    "tool_calls": None,
                    "function_call": None,
                    "refusal": None,
                },
            }
        ],
    }


def quoted_document(result: ResumeAnalysis | JobAnalysis) -> str:
    payload = result.model_dump()
    mentions = result.skills if isinstance(result, ResumeAnalysis) else result.requirements
    payload["skills" if isinstance(result, ResumeAnalysis) else "requirements"] = [
        mention.model_dump(exclude={"start", "end"}) for mention in mentions
    ]
    return json.dumps(payload)


async def test_six_operations_routing_schema_boundary_and_provenance() -> None:
    examples = await all_results(MockAIProvider())
    expected = [r.model_dump()["data"] for r in examples]
    expected[2]["score_basis"] = "rubric_mean"
    operations = list(get_args(Operation))
    captured: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        i = len(captured) - 1
        body = json.loads(request.content)
        text = (
            quoted_document(ResumeAnalysis.model_validate(expected[i]))
            if i == 0
            else quoted_document(JobAnalysis.model_validate(expected[i]))
            if i == 1
            else json.dumps(expected[i])
        )
        return httpx.Response(200, json=wire(text, body["model"]))

    configured = settings(xkiro_model_routes={"analyze_resume": OMNI, "generate_followup": OMNI})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        provider = create_provider(configured, client)
        actual = await all_results(provider)
        assert isinstance(provider, XkiroProvider)
    for i, result in enumerate(actual):
        expected_model = OMNI if operations[i] in {"analyze_resume", "generate_followup"} else FREE
        assert result.model_dump()["data"] == expected[i]
        assert result.model_dump()["provenance"]["model"] == expected_model
        assert result.model_dump()["provenance"]["kind"] == "model_assisted"
        request = captured[i]
        assert str(request.url) == "https://api.xkiro.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer " + TEST_KEY
        body = json.loads(request.content)
        assert body["model"] == expected_model
        assert body["response_format"] == {"type": "json_object"}
        assert body["stream"] is False and body["max_tokens"] == 4096
        assert "schema" in body["messages"][0]["content"]
        assert "UNTRUSTED" in body["messages"][0]["content"]
        assert TEST_KEY not in request.content.decode()
        assert "tools" not in body and "web_search" not in body


@pytest.mark.parametrize(
    "model", ["qwen/qwen3.8-max", "qwen/qwen3.8-omni-flash", "automatic", "qwen/x\n:free"]
)
def test_models_require_explicit_free_id_or_paid_authorization(model: str) -> None:
    with pytest.raises(ValidationError):
        settings(xkiro_reasoning_model=model)
    with pytest.raises(ValidationError):
        settings(xkiro_model_routes={"generate_followup": model})


def test_explicit_paid_model_authorization_and_no_credential_serialization() -> None:
    configured = settings(
        xkiro_reasoning_model="qwen/operator-chosen", xkiro_allow_paid_models=True
    )
    assert configured.xkiro_reasoning_model == "qwen/operator-chosen"
    assert TEST_KEY not in repr(configured) + configured.model_dump_json()
    assert "xkiro_api_key" not in configured.model_dump()
    with pytest.raises(ValidationError):
        settings(xkiro_base_url="https://attacker.invalid/v1")
    with pytest.raises(ValidationError):
        settings(xkiro_model_routes={"unsupported": FREE})
    with pytest.raises(ValidationError):
        settings(public_demo_only=True)


async def test_missing_key_and_demo_never_make_network_calls() -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        pytest.fail("Missing keys and demo must not send provider requests")

    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        with pytest.raises(ProviderUnavailable):
            await create_provider(settings(xkiro_api_key=""), client).analyze_resume(RESUME)
        demo = create_provider(settings(), client, demo=True)
        assert isinstance(demo, MockAIProvider)
        assert (await demo.analyze_resume(RESUME)).provenance.kind == "simulation"


@pytest.mark.parametrize("finish", ["length", "tool_calls", "function_call", "unknown"])
async def test_incomplete_responses_rejected(finish: str) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=wire("{}", finish=finish)))
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await create_provider(settings(), client).evaluate_answer(ANSWER)


@pytest.mark.parametrize(
    "payload",
    [
        {"summary": "ok", "skills": [], "suggestions": ["review"], "unexpected": True},
        {
            "summary": "ok",
            "skills": [{"name": "Python", "evidence": "invented"}],
            "suggestions": ["review"],
        },
        {"summary": "ok", "skills": [], "suggestions": []},
    ],
)
async def test_invalid_domain_output_is_not_returned(payload: dict[str, object]) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=wire(json.dumps(payload))))
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await create_provider(settings(), client).analyze_resume(RESUME)


@pytest.mark.parametrize("job", [False, True])
async def test_document_offsets_are_grounded_locally_in_unicode_source(job: bool) -> None:
    source = "📄 é — Python and Python"
    mention: dict[str, object] = {"name": "Python", "evidence": "Python"}
    if job:
        mention["importance"] = "mentioned"
    payload = {
        "summary": "Quoted claim, not verified skill.",
        "requirements" if job else "skills": [mention],
        "review_notes" if job else "suggestions": ["Review the source."],
    }

    def handle(request: httpx.Request) -> httpx.Response:
        prompt = json.loads(request.content)["messages"][0]["content"]
        assert "server calculates" in prompt
        assert '"start"' not in prompt and '"end"' not in prompt
        return httpx.Response(200, json=wire(json.dumps(payload)))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        provider = XkiroProvider(client, settings())
        skill: SkillMention
        if job:
            result = await provider.analyze_job_description(JobInput(text=source))
            skill = result.data.requirements[0]
        else:
            resume = await provider.analyze_resume(ResumeInput(text=source))
            skill = resume.data.skills[0]
        assert (skill.start, skill.end) == (6, 12)
        assert source[skill.start : skill.end] == skill.evidence


@pytest.mark.parametrize(
    "mentions",
    [
        [{"name": "Python", "evidence": "Python", "start": 99, "end": 101}],
        [{"name": "Python", "evidence": "python"}],
        [{"name": "Python", "evidence": "Python"}] * 2,
    ],
    ids=["unrequested-model-offsets", "inexact-evidence", "duplicate-skill"],
)
async def test_grounding_rejects_invalid_evidence_or_fields(
    mentions: list[dict[str, object]],
) -> None:
    payload = {"summary": "Review", "skills": mentions, "suggestions": ["Review evidence"]}
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=wire(json.dumps(payload))))
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await XkiroProvider(client, settings()).analyze_resume(ResumeInput(text="Python"))


@pytest.mark.parametrize(
    "raw",
    ["not json", "[]", '{"choices":[]}', "x" * 262145],
    ids=["not-json", "array", "empty-choices", "oversized"],
)
async def test_malformed_envelope_and_size(raw: str) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, text=raw))
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await create_provider(settings(), client).analyze_resume(RESUME)


async def test_refusal_tools_and_unrequested_model_rejected() -> None:
    responses = [
        wire("{}", finish="content_filter"),
        wire("{}", model="qwen/paid-substitute"),
        {
            "model": FREE,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "{}",
                        "tool_calls": [{"function": "execute"}],
                    },
                }
            ],
        },
    ]
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=responses.pop(0)))
    ) as client:
        with pytest.raises(ProviderRefusal):
            await create_provider(settings(), client).analyze_resume(RESUME)
        for _ in range(2):
            with pytest.raises(InvalidProviderOutput):
                await create_provider(settings(), client).analyze_resume(RESUME)


@pytest.mark.parametrize(
    "status,attempts",
    [
        (400, 1),
        (401, 1),
        (402, 1),
        (403, 1),
        (404, 1),
        (422, 1),
        (429, 2),
        (503, 2),
        (302, 1),
    ],
)
async def test_bounded_errors_never_substitute_paid_models(status: int, attempts: int) -> None:
    models: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        models.append(json.loads(request.content)["model"])
        return httpx.Response(
            status,
            text=TEST_KEY,
            headers={"Retry-After": "0", "Location": "https://attacker.invalid"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderUnavailable) as error:
            await create_provider(settings(ai_max_retries=1), client).analyze_resume(RESUME)
        assert error.value.code == ("ai_rate_limited" if status == 429 else "ai_unavailable")
        assert TEST_KEY not in str(error.value)
    assert models == [FREE] * attempts


async def test_retry_after_and_timeout_do_not_duplicate_work() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"Retry-After": "9999"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderRateLimited):
            await create_provider(settings(ai_max_retries=2), client).analyze_resume(RESUME)
    assert calls == 1

    async def slow(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(10)
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
        with pytest.raises(ProviderTimeout):
            await create_provider(settings(ai_timeout_seconds=0.1), client).analyze_resume(RESUME)


async def test_multimodal_routes_inline_image_to_omni_and_validates_result() -> None:
    content = ImageInput(
        prompt="Describe the visible chart.",
        media_type="image/png",
        data_base64=base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode(),
    )

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == OMNI
        parts = body["messages"][1]["content"]
        assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")
        return httpx.Response(
            200,
            json=wire(
                json.dumps(
                    {"summary": "A chart", "observations": [], "limitations": "Requires review"}
                ),
                OMNI,
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await XkiroProvider(client, settings()).analyze_image(content)
        assert result.provenance.model == OMNI and result.data.summary == "A chart"
    with pytest.raises(ValidationError):
        ImageInput(
            prompt="Describe", media_type="image/png", data_base64="https://attacker.invalid"
        )
    with pytest.raises(ValidationError):
        ImageInput(
            prompt="Describe",
            media_type="image/png",
            data_base64=base64.b64encode(b"not png").decode(),
        )


async def test_route_change_changes_frozen_identity() -> None:
    async with httpx.AsyncClient() as client:
        first = XkiroProvider(client, settings())
        second = XkiroProvider(client, settings(xkiro_model_routes={"generate_followup": OMNI}))
        assert first.model == second.model == FREE
        assert first.version != second.version
