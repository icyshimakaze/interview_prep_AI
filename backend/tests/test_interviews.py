import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.ai.errors import ProviderUnavailable
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.schemas import AnswerEvaluation as AnswerResult
from interview_prep.ai.schemas import AnswerInput, ProviderResult
from interview_prep.modules.interviews.models import (
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from interview_prep.modules.interviews.schemas import (
    InterviewCommandResponse,
    InterviewReview,
    InterviewSessionView,
)
from interview_prep.modules.interviews.work_models import InterviewWork
from interview_prep.modules.interviews.worker import InterviewRunner
from interview_prep.modules.questions.seed import load_assessment_seed, load_bank_seed
from interview_prep.modules.roadmaps.models import ProgressEvent

BASE = "/api/v1/account/interviews"


async def seed(database: AsyncEngine) -> None:
    async with async_sessionmaker(database)() as session, session.begin():
        await load_bank_seed(session)
        await load_assessment_seed(session)


def runner(client: httpx.AsyncClient) -> InterviewRunner:
    transport = client._transport
    assert isinstance(transport, httpx.ASGITransport)
    app = transport.app
    assert isinstance(app, FastAPI)
    result: InterviewRunner = app.state.interview_runner
    return result


async def create(
    client: httpx.AsyncClient,
    count: int = 2,
    type_: str = "technical_fundamentals",
    difficulty: str = "auto",
    base: str = BASE,
) -> InterviewSessionView:
    response = await client.post(
        base,
        json={
            "command_key": str(uuid4()),
            "configuration": {
                "interview_type": type_,
                "question_count": count,
                "difficulty": difficulty,
            },
        },
    )
    assert response.status_code == 201, response.text
    return InterviewCommandResponse.model_validate(response.json()).session


async def command(
    client: httpx.AsyncClient,
    interview: InterviewSessionView,
    action: str,
    extra: dict[str, object] | None = None,
    base: str = BASE,
    key: UUID | None = None,
) -> InterviewSessionView:
    response = await client.post(
        f"{base}/{interview.id}/{action}",
        json={"command_key": str(key or uuid4()), "revision": interview.revision, **(extra or {})},
    )
    assert response.status_code in (200, 202), response.text
    return InterviewCommandResponse.model_validate(response.json()).session


async def read(
    client: httpx.AsyncClient, interview: InterviewSessionView, base: str = BASE
) -> InterviewSessionView:
    response = await client.get(f"{base}/{interview.id}")
    assert response.status_code == 200, response.text
    return InterviewSessionView.model_validate(response.json())


async def test_persisted_answer_before_failure_and_final_review(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    interview = await command(account_client, await create(account_client, 1), "start")
    assert interview.current_turn
    original = interview.current_turn.id
    text = "My response is saved even when optional evaluation fails."
    key = uuid4()
    body: dict[str, object] = {"answer_text": text}
    submitted = await command(account_client, interview, f"turns/{original}/submit", body, key=key)
    repeated = await command(account_client, interview, f"turns/{original}/submit", body, key=key)
    assert repeated.revision == submitted.revision
    async with async_sessionmaker(database)() as session:
        answer = await session.scalar(
            select(InterviewAnswer).where(InterviewAnswer.interview_question_id == original)
        )
        assert answer and answer.answer_text == text and answer.status == "submitted"
        assert await session.scalar(select(func.count()).select_from(InterviewWork)) == 1

    class FailingProvider(MockAIProvider):
        async def evaluate_answer(self, content: AnswerInput) -> ProviderResult[AnswerResult]:
            raise ProviderUnavailable()

    worker = runner(account_client)
    worker.provider_factory = lambda demo, remaining: FailingProvider()
    assert await worker.tick()
    submitted = await read(account_client, submitted)
    assert submitted.current_turn and submitted.current_turn.answer_text == text
    assert submitted.progress.evaluation_failed == 1
    assert (await account_client.get(f"{BASE}/{submitted.id}/review")).status_code == 409
    assert not (await account_client.get("/api/v1/account/dashboard")).json()["interviews"][0][
        "feedback"
    ]
    ended = await command(account_client, submitted, "complete")
    await worker.maintenance()
    review = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{ended.id}/review")).json()
    )
    assert review.session.status == "completed" and review.evaluation_coverage == "none"
    assert review.turns[0].turn.answer_text == text
    assert review.turns[0].evaluation and review.turns[0].evaluation.error_code == "ai_unavailable"
    forbidden = await account_client.post(
        f"{BASE}/{ended.id}/turns/{original}/submit",
        json={
            "command_key": str(uuid4()),
            "revision": review.session.revision,
            "answer_text": "overwrite",
        },
    )
    assert forbidden.status_code == 409
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(ProgressEvent)) == 1


async def test_followup_pause_resume_skip_and_ordering(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    interview = await command(account_client, await create(account_client), "start")
    assert interview.current_turn
    first = interview.current_turn.id
    invalid = await account_client.post(
        f"{BASE}/{interview.id}/advance",
        json={
            "command_key": str(uuid4()),
            "revision": interview.revision,
            "from_turn_id": str(first),
            "next_kind": "main",
        },
    )
    assert invalid.status_code == 409
    interview = await command(
        account_client,
        interview,
        "pause",
        {"draft": {"turn_id": str(first), "answer_text": "Saved draft"}},
    )
    reloaded = await read(account_client, interview)
    assert (
        reloaded.status == "paused"
        and reloaded.current_turn
        and reloaded.current_turn.answer_text == "Saved draft"
    )
    interview = await command(account_client, reloaded, "resume")
    interview = await command(
        account_client,
        interview,
        f"turns/{first}/submit",
        {"answer_text": "I would test both success and invalid input."},
    )
    interview = await command(account_client, interview, f"turns/{first}/followup")
    worker = runner(account_client)
    await worker.tick()
    await worker.tick()
    interview = await read(account_client, interview)
    assert interview.followup_decision == "ready"
    interview = await command(
        account_client, interview, "advance", {"from_turn_id": str(first), "next_kind": "followup"}
    )
    assert interview.current_turn and interview.current_turn.parent_id == first
    assert interview.current_turn.context_excerpt == "I would test both success and invalid input."
    child = interview.current_turn.id
    interview = await command(
        account_client,
        interview,
        f"turns/{child}/submit",
        {"answer_text": "I would change one input at a time."},
    )
    assert "followup" not in interview.allowed_actions
    interview = await command(
        account_client, interview, "advance", {"from_turn_id": str(child), "next_kind": "main"}
    )
    assert interview.current_turn and interview.current_turn.id != first
    interview = await command(
        account_client, interview, f"turns/{interview.current_turn.id}/skip", {"answer_text": None}
    )
    interview = await command(account_client, interview, "complete")
    await worker.maintenance()
    result = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{interview.id}/review")).json()
    )
    assert len(result.turns) == 3 and result.session.progress.skipped == 1
    assert result.turns[1].evaluation and result.turns[1].evaluation.status == "not_evaluable"


async def test_end_early_ownership_and_concurrent_submission(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    interview = await command(account_client, await create(account_client), "start")
    assert interview.current_turn
    turn = interview.current_turn.id
    await sign_in(account_client, "bob")
    assert (await account_client.get(f"{BASE}/{interview.id}")).status_code == 404
    denied = await account_client.post(
        f"{BASE}/{interview.id}/end",
        json={
            "command_key": str(uuid4()),
            "revision": interview.revision,
            "draft": None,
            "current_answer_action": "none",
        },
    )
    assert denied.status_code == 404
    await sign_in(account_client, "alice")
    response = await account_client.post(
        f"{BASE}/{interview.id}/end",
        json={
            "command_key": str(uuid4()),
            "revision": interview.revision,
            "draft": {"turn_id": str(turn), "answer_text": "Unsubmitted reasoning"},
            "current_answer_action": "keep_draft",
        },
    )
    assert response.status_code == 202, response.text
    await runner(account_client).maintenance()
    review = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{interview.id}/review")).json()
    )
    assert review.session.status == "abandoned" and review.turns[0].turn.status == "unanswered"
    assert review.turns[0].turn.answer_text == "Unsubmitted reasoning" and review.unasked_main == 1
    interview = await command(account_client, await create(account_client, 1), "start")
    assert interview.current_turn
    payload = {
        "command_key": str(uuid4()),
        "revision": interview.revision,
        "answer_text": "Only one answer",
    }
    responses = await asyncio.gather(
        *(
            account_client.post(
                f"{BASE}/{interview.id}/turns/{interview.current_turn.id}/submit", json=payload
            )
            for _ in range(2)
        )
    )
    assert [r.status_code for r in responses] == [202, 202]
    assert responses[0].json()["receipt"] == responses[1].json()["receipt"]


@pytest.mark.parametrize(
    ("type_", "difficulty", "count", "available"),
    [
        ("frontend", "medium", 1, True),
        ("frontend", "easy", 1, False),
        ("system_design", "hard", 1, True),
        ("behavioral", "easy", 1, True),
        ("full_stack", "medium", 2, True),
        ("backend", "auto", 2, True),
        ("mixed", "auto", 2, True),
    ],
)
async def test_interview_type_inventory(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    type_: str,
    difficulty: str,
    count: int,
    available: bool,
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    interview = await create(account_client, count, type_, difficulty)
    response = await account_client.post(
        f"{BASE}/{interview.id}/start",
        json={"command_key": str(uuid4()), "revision": interview.revision},
    )
    assert response.status_code == (200 if available else 409), response.text


async def test_expiry_preserves_draft_and_cancels_generation(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    interview = await command(account_client, await create(account_client), "start")
    assert interview.current_turn
    interview = await command(
        account_client,
        interview,
        "pause",
        {"draft": {"turn_id": str(interview.current_turn.id), "answer_text": "Retained on expiry"}},
    )
    worker = runner(account_client)
    worker.clock = lambda: interview.server_time + timedelta(hours=25)
    await worker.maintenance()
    review = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{interview.id}/review")).json()
    )
    assert review.session.status == "abandoned" and review.session.end_reason == "expired"
    assert review.turns[0].turn.answer_text == "Retained on expiry"
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(InterviewQuestion)) == 1
        assert await session.scalar(select(func.count()).select_from(InterviewSession)) == 1
