from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from database_tools import migrate
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in
from test_interviews import BASE, command, create, read, runner, seed

from interview_prep.ai.factory import create_provider
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.schemas import AnswerInput
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import InterviewAnswer, InterviewQuestion
from interview_prep.modules.interviews.policy import utc_now
from interview_prep.modules.interviews.schemas import InterviewReview
from interview_prep.modules.interviews.work_models import FollowupContent, InterviewWork


async def test_duplicate_followups_and_session_budget(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 4), "start")
    worker = runner(account_client)
    seen = set()
    for index in range(4):
        assert session.current_turn and session.current_turn.id not in seen
        turn = session.current_turn.id
        seen.add(turn)
        session = await command(
            account_client,
            session,
            f"turns/{turn}/submit",
            {"answer_text": "My practice response."},
        )
        if index < 3:
            session = await command(account_client, session, f"turns/{turn}/followup")
            duplicate = await account_client.post(
                f"{BASE}/{session.id}/turns/{turn}/followup",
                json={"command_key": str(uuid4()), "revision": session.revision},
            )
            assert duplicate.status_code == 409 and duplicate.json()["code"] == "followup_limit"
            await worker.tick()
            await worker.tick()
            session = await read(account_client, session)
            session = await command(
                account_client, session, "advance", {"from_turn_id": str(turn), "next_kind": "main"}
            )
        else:
            exhausted = await account_client.post(
                f"{BASE}/{session.id}/turns/{turn}/followup",
                json={"command_key": str(uuid4()), "revision": session.revision},
            )
            assert exhausted.status_code == 409 and exhausted.json()["code"] == "followup_limit"
    assert session.progress.followups_reserved == 3
    async with async_sessionmaker(database)() as db:
        assert await db.scalar(select(func.count()).select_from(FollowupContent)) == 3


async def test_cancelled_followup_cannot_insert_late_question(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client), "start")
    assert session.current_turn
    first = session.current_turn.id
    session = await command(
        account_client, session, f"turns/{first}/submit", {"answer_text": "Answer for context"}
    )
    worker = runner(account_client)
    await worker.tick()
    session = await read(account_client, session)
    session = await command(account_client, session, f"turns/{first}/followup")
    dispatch = await worker.claim()
    assert dispatch
    session = await read(account_client, session)
    session = await command(
        account_client, session, "advance", {"from_turn_id": str(first), "next_kind": "main"}
    )
    assert isinstance(dispatch.content, AnswerInput)
    from interview_prep.ai.schemas import FollowupInput

    assert isinstance(dispatch.content, FollowupInput)
    generated = await MockAIProvider().generate_followup(dispatch.content)
    await worker.finish(dispatch, generated.data, generated.provenance, None)
    async with async_sessionmaker(database)() as db:
        assert await db.scalar(select(func.count()).select_from(FollowupContent)) == 0
        assert await db.scalar(select(func.count()).select_from(InterviewQuestion)) == 2
    assert (await read(account_client, session)).current_turn == session.current_turn


@pytest.mark.parametrize("dispatched", [False, True])
async def test_lease_recovery_and_interrupted_dispatch(
    account_client: httpx.AsyncClient, database: AsyncEngine, dispatched: bool
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.current_turn
    session = await command(
        account_client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "Durable answer"},
    )
    worker = runner(account_client)
    if dispatched:
        assert await worker.claim()
    else:
        async with async_sessionmaker(database)() as db, db.begin():
            job = await db.scalar(select(InterviewWork))
            assert job
            job.state, job.lease_token, job.lease_expires_at = (
                "running",
                uuid4(),
                utc_now() + timedelta(seconds=90),
            )
    worker.clock = lambda: utc_now() + timedelta(seconds=100)
    await worker.maintenance()
    async with async_sessionmaker(database)() as db:
        job = await db.scalar(select(InterviewWork))
        assert job and job.state == ("failed" if dispatched else "pending")
    worker.clock = utc_now
    if dispatched:
        session = await read(account_client, session)
        async with async_sessionmaker(database)() as db:
            job = await db.scalar(select(InterviewWork))
            assert job and job.evaluation_id
            evaluation_id = job.evaluation_id
        assert session.current_turn
        session = await command(
            account_client,
            session,
            f"turns/{session.current_turn.id}/evaluation/retry",
            {"evaluation_id": str(evaluation_id)},
        )
    assert await worker.tick()
    session = await read(account_client, session)
    assert session.progress.evaluation_failed == 0
    assert session.current_turn and session.current_turn.evaluation_status == "completed"


async def test_finalization_deadline_retains_answer_without_provider(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.current_turn
    session = await command(
        account_client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "No worker was available yet"},
    )
    session = await command(account_client, session, "complete")
    worker = runner(account_client)
    worker.clock = lambda: utc_now() + timedelta(seconds=125)
    await worker.maintenance()
    review = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{session.id}/review")).json()
    )
    assert review.session.status == "completed" and review.session.progress.evaluation_failed == 1
    assert review.turns[0].turn.answer_text == "No worker was available yet"


async def test_stale_revision_keys_and_foreign_turns(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.current_turn
    key = uuid4()
    original = session
    session = await command(
        account_client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "Original"},
        key=key,
    )
    assert session.current_turn
    changed = await account_client.post(
        f"{BASE}/{session.id}/turns/{session.current_turn.id}/submit",
        json={"command_key": str(key), "revision": original.revision, "answer_text": "Changed"},
    )
    assert changed.status_code == 409 and changed.json()["code"] == "command_conflict"
    stale = await account_client.post(
        f"{BASE}/{session.id}/pause",
        json={"command_key": str(uuid4()), "revision": original.revision, "draft": None},
    )
    assert stale.status_code == 409 and stale.json()["code"] == "interview_revision"
    foreign = await account_client.post(
        f"{BASE}/{session.id}/turns/{uuid4()}/submit",
        json={"command_key": str(uuid4()), "revision": session.revision, "answer_text": "Foreign"},
    )
    assert foreign.status_code == 404


async def test_demo_always_mock_with_no_credentials_and_csrf(
    integration_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    client = integration_client
    assert (
        await client.post(
            "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
        )
    ).status_code == 200
    base = "/api/v1/demo/interviews"
    worker = runner(client)
    worker.settings = worker.settings.model_copy(update={"ai_provider": "openai"})
    worker.provider_factory = lambda demo, remaining: create_provider(
        worker.settings, worker.http, demo=demo
    )
    assert (await client.get(base + "/options")).json()["provider"]["name"] == "MockAIProvider"
    body = {"command_key": str(uuid4()), "configuration": {"question_count": 1}}
    assert (await client.post(base, json=body)).status_code == 403
    client.headers.update(
        {"Origin": "http://localhost:3000", "X-CSRF-Token": client.cookies["interview_prep_csrf"]}
    )
    session = await command(client, await create(client, 1, base=base), "start", base=base)
    assert session.current_turn
    session = await command(
        client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "No external credentials used"},
        base=base,
    )
    assert await worker.tick()
    session = await read(client, session, base)
    session = await command(client, session, "complete", base=base)
    await worker.maintenance()
    review = InterviewReview.model_validate(
        (await client.get(f"{base}/{session.id}/review")).json()
    )
    assert review.session.provider.kind == "simulation"
    assert review.turns[0].evaluation and review.turns[0].evaluation.kind == "simulation"


async def test_erasure_fences_dispatched_work(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.current_turn
    session = await command(
        account_client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "Erase private work"},
    )
    worker = runner(account_client)
    dispatch = await worker.claim()
    assert dispatch
    async with async_sessionmaker(database)() as db, db.begin():
        await db.execute(delete(User).where(User.id == dispatch.owner_id))
    result = await MockAIProvider().evaluate_answer(dispatch.content)
    await worker.finish(dispatch, result.data, result.provenance, None)
    async with async_sessionmaker(database)() as db:
        assert await db.scalar(select(func.count()).select_from(InterviewAnswer)) == 0
        assert await db.scalar(select(func.count()).select_from(InterviewWork)) == 0


async def test_missing_optional_provider_configuration_still_saves_answer(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    worker = runner(account_client)
    worker.settings = worker.settings.model_copy(update={"ai_provider": "openai"})
    worker.provider_factory = lambda demo, remaining: create_provider(
        worker.settings, worker.http, demo=demo
    )
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.provider.model is None and session.current_turn
    session = await command(
        account_client,
        session,
        f"turns/{session.current_turn.id}/submit",
        {"answer_text": "Retained without provider credentials"},
    )
    await worker.tick()
    session = await read(account_client, session)
    assert session.progress.evaluation_failed == 1 and session.current_turn
    assert session.current_turn.answer_text == "Retained without provider credentials"
    session = await command(account_client, session, "complete")
    await worker.maintenance()
    review = InterviewReview.model_validate(
        (await account_client.get(f"{BASE}/{session.id}/review")).json()
    )
    assert review.turns[0].evaluation and review.turns[0].evaluation.error_code == "ai_unavailable"


async def test_database_guards_reject_reordering_and_reopening(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await command(account_client, await create(account_client, 1), "start")
    assert session.current_turn
    async with async_sessionmaker(database)() as db:
        with pytest.raises(IntegrityError):
            await db.execute(
                text("UPDATE interview_questions SET sequence=99 WHERE id=:id"),
                {"id": session.current_turn.id},
            )
        await db.rollback()
    session = await command(
        account_client, session, f"turns/{session.current_turn.id}/skip", {"answer_text": None}
    )
    session = await command(account_client, session, "complete")
    await runner(account_client).maintenance()
    async with async_sessionmaker(database)() as db:
        with pytest.raises(IntegrityError):
            await db.execute(
                text(
                    "UPDATE interview_sessions SET status='active',completed_at=NULL WHERE id=:id"
                ),
                {"id": session.id},
            )
        await db.rollback()


async def test_populated_interview_downgrade_refuses_data_loss(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client, "alice")
    session = await create(account_client, 1)
    refused = await migrate(
        database.url.render_as_string(hide_password=False), "downgrade", "0006_real_assessments"
    )
    assert refused.returncode != 0 and "Unsafe downgrade" in refused.stderr
    assert (await read(account_client, session)).id == session.id
    async with database.connect() as connection:
        assert (
            await connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0010_security_budgets"
        )
