import asyncio
import json

import httpx
import pytest
from test_ai_providers import ANSWER, FOLLOWUP, PROJECT, RESUME, ROADMAP, openai_wire, remote

from interview_prep.ai.errors import InvalidProviderOutput, ProviderTimeout
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.schemas import ProjectInput


@pytest.mark.parametrize("operation", ["resume", "followup", "roadmap", "project"])
async def test_valid_json_with_invalid_domain_relationships_is_rejected(operation: str) -> None:
    mock = MockAIProvider()
    if operation == "resume":
        data = (await mock.analyze_resume(RESUME)).data.model_dump()
        data["skills"][0]["evidence"] = "fabricated source"
    elif operation == "followup":
        data = (await mock.generate_followup(FOLLOWUP)).data.model_dump()
        data["question"] = FOLLOWUP.question
    elif operation == "roadmap":
        data = (await mock.recommend_roadmap(ROADMAP)).data.model_dump()
        data["steps"][0]["minutes"] = 600
    else:
        data = (await mock.generate_project_questions(PROJECT)).data.model_dump()
        data["questions"][0]["evidence"] = "fabricated source"
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=openai_wire(json.dumps(data))),
        )
    ) as client:
        provider: AIProvider = remote("openai", client)
        with pytest.raises(InvalidProviderOutput):
            if operation == "resume":
                await provider.analyze_resume(RESUME)
            elif operation == "followup":
                await provider.generate_followup(FOLLOWUP)
            elif operation == "roadmap":
                await provider.recommend_roadmap(ROADMAP)
            else:
                await provider.generate_project_questions(PROJECT)


@pytest.mark.parametrize(
    "payload",
    [
        {"done": False, "done_reason": "stop", "message": {"role": "assistant", "content": "{}"}},
        {"done": True, "done_reason": "length", "message": {"role": "assistant", "content": "{}"}},
        {
            "done": True,
            "done_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "{}",
                "tool_calls": [{"function": "execute"}],
            },
        },
    ],
)
async def test_ollama_partial_or_tool_responses_are_rejected(payload: dict[str, object]) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=payload),
        )
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await remote("ollama", client).evaluate_answer(ANSWER)


async def test_retry_wait_is_part_of_total_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    delays: list[float] = []

    async def stall(delay: float) -> None:
        delays.append(delay)
        await asyncio.Event().wait()

    monkeypatch.setattr("interview_prep.ai.transport.asyncio.sleep", stall)

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, headers={"Retry-After": "0.02"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderTimeout):
            await remote("openai", client, retries=2, seconds=0.03).evaluate_answer(ANSWER)
    assert calls == 1 and delays == [0.02]


async def test_project_question_count_is_a_domain_constraint() -> None:
    data = (await MockAIProvider().generate_project_questions(PROJECT)).data.model_dump_json()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=openai_wire(data)),
        )
    ) as client:
        with pytest.raises(InvalidProviderOutput):
            await remote("openai", client).generate_project_questions(
                ProjectInput(text=PROJECT.text, question_count=1),
            )
