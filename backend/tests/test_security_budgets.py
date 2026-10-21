import asyncio
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

import httpx
import pytest
from conftest import test_settings as make_settings
from database_tools import migrate
from fastapi import HTTPException
from relational_helpers import fictional_owner
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_ai_providers import ANSWER
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.ai.mock import evaluate as mock_evaluate
from interview_prep.core.quotas import reserve
from interview_prep.core.security_models import EvaluationReceipt, OperationQuota
from interview_prep.modules.assessments.evaluation import ConceptualInput
from interview_prep.modules.assessments.models import QuestionAttempt
from interview_prep.modules.assessments.receipts import evaluate
from interview_prep.modules.demo.service import delete_expired
from interview_prep.modules.identity.models import User
from interview_prep.modules.projects.ingestion import ProjectImporter
from interview_prep.modules.projects.schemas import StaticAnalysis


async def test_durable_quota_is_atomic_across_sessions_and_failures(database: AsyncEngine) -> None:
    factory = async_sessionmaker(database)
    settings = make_settings().model_copy(update={"ai_owner_hourly_calls": 4, "ai_max_retries": 1})
    owner = uuid4()
    outcomes = await asyncio.gather(
        *(reserve(factory, settings, owner, "ai") for _ in range(8)), return_exceptions=True
    )
    assert sum(result is None for result in outcomes) == 2
    assert all(
        result is None or isinstance(result, HTTPException) and result.status_code == 429
        for result in outcomes
    )
    # New sessions/processes and an unrelated business rollback do not refund calls.
    async with factory() as session:
        await session.rollback()
    with pytest.raises(HTTPException) as limited:
        await reserve(async_sessionmaker(database), settings, owner, "ai")
    assert limited.value.status_code == 429
    await reserve(factory, settings, uuid4(), "ai")


async def test_import_failures_consume_quota_only_after_authentication(
    account_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    async def failing_parse(self: ProjectImporter, data: bytes) -> StaticAnalysis:
        nonlocal calls
        calls += 1
        raise HTTPException(422, detail="archive_corrupt")

    monkeypatch.setattr(ProjectImporter, "parse", failing_parse)
    path = "/api/v1/account/projects/zip"
    for _ in range(12):
        assert (await account_client.post(path, content=b"bad")).status_code == 401
    await sign_in(account_client)
    for _ in range(10):
        result = await account_client.post(
            path, content=b"bad", headers={"Content-Type": "application/zip"}
        )
        assert result.status_code == 422
    result = await account_client.post(
        path, content=b"bad", headers={"Content-Type": "application/zip"}
    )
    assert result.status_code == 429 and int(result.headers["Retry-After"]) > 0
    assert calls == 10


async def test_import_global_budget_expiry_and_no_raw_owner_retention(
    database: AsyncEngine,
) -> None:
    factory = async_sessionmaker(database)
    settings = make_settings().model_copy(update={"ai_global_daily_calls": 2, "ai_max_retries": 0})
    owner = uuid4()
    instant = datetime.now(UTC)
    await reserve(factory, settings, owner, "ai", now=instant)
    await reserve(factory, settings, uuid4(), "ai", now=instant)
    with pytest.raises(HTTPException):
        await reserve(factory, settings, uuid4(), "ai", now=instant)
    for _ in range(10):
        await reserve(factory, settings, owner, "import", now=instant)
    with pytest.raises(HTTPException):
        await reserve(factory, settings, owner, "import", now=instant)
    async with factory() as session:
        rows = (await session.scalars(select(OperationQuota))).all()
        assert all(str(owner) not in r.key_hash and len(r.key_hash) == 64 for r in rows)
        await delete_expired(session, instant + timedelta(days=3))
        assert await session.scalar(select(func.count()).select_from(OperationQuota)) == 0
    await reserve(factory, settings, owner, "ai", now=instant + timedelta(days=3))


async def test_security_migration_refuses_removing_live_budgets(database: AsyncEngine) -> None:
    await reserve(async_sessionmaker(database), make_settings(), uuid4(), "import")
    result = await migrate(
        database.url.render_as_string(hide_password=False), "downgrade", "0009_personal_roadmaps"
    )
    assert result.returncode != 0 and "live security budgets" in result.stderr
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(OperationQuota)) == 2


class PaidFixture:
    name = "FixtureProvider"
    version = "fixture-v1"
    kind: Literal["simulation", "model_assisted"] = "model_assisted"

    def __init__(self) -> None:
        self.calls = 0
        self.fail = False
        self.interrupt = False

    async def evaluate(self, content: ConceptualInput) -> object:
        self.calls += 1
        if self.interrupt:
            raise asyncio.CancelledError()
        if self.fail:
            raise ValueError("private-provider-body")
        return {
            **mock_evaluate(ANSWER).model_dump(),
            "score_basis": "rubric_mean",
            "kind": "model_assisted",
        }


async def test_paid_receipt_survives_rollback_and_is_scoped_to_owner_and_input(
    database: AsyncEngine,
) -> None:
    owner = await fictional_owner(database)
    provider = PaidFixture()
    content = ConceptualInput(ANSWER.question, ANSWER.answer, tuple(ANSWER.expected_concepts), ())
    answer = QuestionAttempt(
        owner_id=owner, assessment_attempt_id=uuid4(), assessment_question_id=uuid4()
    )
    async with async_sessionmaker(database)() as session:
        session.info["settings"] = make_settings()
        result = await evaluate(session, answer, provider, content)
        await session.rollback()  # A later question's failure rolls back grading, not this receipt.
        assert await evaluate(session, answer, provider, content) == result
        assert provider.calls == 1
        answer.assessment_question_id = uuid4()
        await evaluate(session, answer, provider, content)
        assert provider.calls == 2
        other = await fictional_owner(database)
        answer.owner_id = other
        await evaluate(session, answer, provider, content)
        assert provider.calls == 3
        await session.execute(delete(User).where(User.id == owner))
        await session.commit()
        assert (
            await session.scalar(
                select(func.count())
                .select_from(EvaluationReceipt)
                .where(EvaluationReceipt.owner_id == owner)
            )
            == 0
        )
        assert await session.scalar(select(func.count()).select_from(EvaluationReceipt)) == 1


async def test_concurrent_paid_receipt_does_not_dispatch_twice(database: AsyncEngine) -> None:
    owner = await fictional_owner(database)
    started, release = asyncio.Event(), asyncio.Event()

    class SlowFixture(PaidFixture):
        async def evaluate(self, content: ConceptualInput) -> object:
            started.set()
            await release.wait()
            return await super().evaluate(content)

    provider = SlowFixture()
    answer = QuestionAttempt(
        owner_id=owner, assessment_attempt_id=uuid4(), assessment_question_id=uuid4()
    )
    content = ConceptualInput(ANSWER.question, ANSWER.answer, tuple(ANSWER.expected_concepts), ())
    factory = async_sessionmaker(database)

    async def dispatch() -> object:
        async with factory() as session:
            session.info["settings"] = make_settings()
            return await evaluate(session, answer, provider, content)

    first = asyncio.create_task(dispatch())
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        with pytest.raises(HTTPException) as conflict:
            await dispatch()
        assert conflict.value.status_code == 409
    finally:
        release.set()
        await first
    assert provider.calls == 1


@pytest.mark.parametrize("interrupted", [False, True])
async def test_failed_and_ambiguous_paid_evaluations_have_bounded_retries(
    database: AsyncEngine, interrupted: bool
) -> None:
    owner = await fictional_owner(database)
    provider = PaidFixture()
    provider.fail, provider.interrupt = True, interrupted
    answer = QuestionAttempt(
        owner_id=owner, assessment_attempt_id=uuid4(), assessment_question_id=uuid4()
    )
    content = ConceptualInput(ANSWER.question, ANSWER.answer, tuple(ANSWER.expected_concepts), ())
    async with async_sessionmaker(database)() as session:
        session.info["settings"] = make_settings()
        for _ in range(1 if interrupted else 2):
            with pytest.raises(asyncio.CancelledError if interrupted else ValueError):
                await evaluate(session, answer, provider, content)
            await session.rollback()
        with pytest.raises(HTTPException) as limit:
            await evaluate(session, answer, provider, content)
        assert limit.value.status_code == 409
        assert provider.calls == (1 if interrupted else 2)
