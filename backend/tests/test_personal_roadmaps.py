import asyncio
from datetime import date, timedelta
from uuid import uuid4

import httpx
import pytest
from database_tools import migrate
from skill_helpers import prepare
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_assessments import configuration, correct_options, save, seed, start
from test_auth import account_client as account_client
from test_candidate_context import sign_in
from test_planning_rules import evaluation
from test_projects import project
from test_projects import start as start_defense

from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationKind,
    EvaluationStatus,
)
from interview_prep.modules.progress.schemas import ProgressAnalytics
from interview_prep.modules.progress.service import analytics
from interview_prep.modules.roadmaps.models import ProgressEvent, Roadmap, RoadmapItem
from interview_prep.modules.roadmaps.schemas import RoadmapWorkspace

BASE = "/api/v1/account"


async def generate(
    client: httpx.AsyncClient, state: RoadmapWorkspace | None = None
) -> RoadmapWorkspace:
    response = await client.post(
        f"{BASE}/roadmap/generate",
        json={
            "command_key": str(uuid4()),
            "weekly_minutes": 120,
            "expected_id": str(state.current.id) if state and state.current else None,
            "expected_revision": state.current.revision if state and state.current else None,
        },
    )
    assert response.status_code == 200, response.text
    return RoadmapWorkspace.model_validate(response.json())


async def change(
    client: httpx.AsyncClient,
    state: RoadmapWorkspace,
    action: str,
) -> RoadmapWorkspace:
    assert state.current and state.current.items
    response = await client.post(
        f"{BASE}/roadmap/items/{state.current.items[0].id}",
        json={
            "revision": state.current.revision,
            "action": action,
        },
    )
    assert response.status_code == 200, response.text
    return RoadmapWorkspace.model_validate(response.json())


async def test_personal_roadmap_complete_reopen_regeneration_retains_history(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    assert (await account_client.get(f"{BASE}/roadmap")).json()["current"] is None
    first = await generate(account_client)
    completed = await change(account_client, first, "complete")
    assert completed.current and completed.current.items[0].completed_at
    topic = completed.current.items[0].topic
    second = await generate(account_client, completed)
    assert second.current and second.history[0].items[0].topic == topic
    assert second.history[0].items[0].status == "completed"
    assert topic not in [i.topic for i in second.current.items]
    old = second.history[0]
    reopened = await account_client.post(
        f"{BASE}/roadmap/items/{old.items[0].id}",
        json={
            "revision": old.revision,
            "action": "reopen",
        },
    )
    assert reopened.status_code == 200, reopened.text
    restored = RoadmapWorkspace.model_validate(reopened.json())
    assert restored.history[0].items[0].completed_at is None
    third = await generate(account_client, restored)
    assert third.current and topic in [i.topic for i in third.current.items]
    assert len(third.history) == 2
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(Roadmap)) == 3
        assert await session.scalar(select(func.count()).select_from(ProgressEvent)) == 1
        item = await session.get(RoadmapItem, old.items[0].id)
        assert item
        item.title = "overwrite saved rationale"
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


async def test_personal_roadmap_replay_concurrency_ownership_and_invalid_inputs(
    account_client: httpx.AsyncClient,
) -> None:
    await sign_in(account_client, "alice")
    key = str(uuid4())
    body = {"command_key": key, "weekly_minutes": 60}
    first = await account_client.post(f"{BASE}/roadmap/generate", json=body)
    assert first.status_code == 200, first.text
    assert (await account_client.post(f"{BASE}/roadmap/generate", json=body)).json() == first.json()
    assert (
        await account_client.post(f"{BASE}/roadmap/generate", json={**body, "weekly_minutes": 30})
    ).status_code == 409
    state = RoadmapWorkspace.model_validate(first.json())
    assert state.current
    identifier = state.current.items[0].id
    commands = await asyncio.gather(
        *[
            account_client.post(
                f"{BASE}/roadmap/items/{identifier}", json={"revision": 1, "action": "complete"}
            )
            for _ in range(2)
        ]
    )
    assert sorted(r.status_code for r in commands) == [200, 409]
    await sign_in(account_client, "bob")
    assert (await account_client.get(f"{BASE}/roadmap")).json()["current"] is None
    assert (await account_client.get(f"{BASE}/progress")).json()["roadmap"]["current_total"] == 0
    assert (
        await account_client.post(
            f"{BASE}/roadmap/items/{identifier}",
            json={
                "revision": 2,
                "action": "reopen",
            },
        )
    ).status_code == 404
    invalid: list[dict[str, object]] = [
        {"weekly_minutes": 0},
        {"weekly_minutes": True},
        {"owner_id": str(uuid4())},
        {"target_id": str(uuid4())},
        {"interview_date": "2000-01-01"},
    ]
    for extra in invalid:
        response = await account_client.post(
            f"{BASE}/roadmap/generate",
            json={
                "command_key": str(uuid4()),
                "weekly_minutes": 60,
                **extra,
            },
        )
        assert response.status_code in {404, 422}, response.text


async def test_personal_roadmap_target_budget_date_and_project_defense_inputs(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    target = await account_client.post(
        f"{BASE}/targets",
        json={
            "title": "Backend developer",
            "description": "Python and SQL",
            "priority": "high",
        },
    )
    assert target.status_code == 201, target.text
    item = await project(account_client)
    await start_defense(account_client, item, 1)
    response = await account_client.post(
        f"{BASE}/roadmap/generate",
        json={
            "command_key": str(uuid4()),
            "target_id": target.json()["id"],
            "weekly_minutes": 15,
            "interview_date": (date.today() + timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    state = RoadmapWorkspace.model_validate(response.json())
    assert state.current and state.current.target_priority == "high"
    assert any("Project explanation" in i.topic for i in state.current.items)
    assert all(i.estimated_minutes <= 15 for i in state.current.items)
    assert any(i.scheduled_on is None for i in state.current.items)


async def test_personal_progress_uses_persisted_grades_and_recent_sessions(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    for correct in [True, False, True]:
        attempt = await start(account_client, configuration("DBMS", "easy", "multiple_select"))
        selections = await correct_options(database, attempt.questions[0].question_version_id)
        attempt = await save(
            account_client, attempt, selections=selections if correct else selections[:1]
        )
        done = await account_client.post(
            f"{BASE}/assessments/{attempt.id}/submit", json={"revision": attempt.revision}
        )
        assert done.status_code == 200, done.text
    state = await change(account_client, await generate(account_client), "complete")
    state = await change(account_client, state, "reopen")
    await change(account_client, state, "complete")
    response = await account_client.get(f"{BASE}/progress")
    assert response.status_code == 200, response.text
    data = ProgressAnalytics.model_validate(response.json())
    assert sum(p.correct for p in data.assessments) == 2
    assert sum(p.graded for p in data.assessments) == 3
    assert not data.assessment_chart_available  # Three sessions on one day is not a trend.
    assert data.categories[0].percent == 66.7
    assert len(data.recent_sessions) == 3
    assert data.roadmap.current_completed == 1 and data.roadmap.completion_events == 2
    assert data.interview_series == []
    await sign_in(account_client, "other")
    private = (await account_client.get(f"{BASE}/progress")).json()
    assert not private["assessments"] and not private["recent_sessions"]


@pytest.mark.parametrize("demo", [False, True])
async def test_personal_progress_validated_strengths_reuse_real_eligibility(
    database: AsyncEngine,
    demo: bool,
) -> None:
    owner = await prepare(database, demo=demo)
    async with async_sessionmaker(database)() as session:
        user = await session.get(User, owner)
        assert user
        data = await analytics(session, user)
        assert bool(data.validated_strengths) is not demo
        assert data.interview_series == []  # Historical unscaled ratings are never invented.


async def test_personal_roadmap_demo_csrf_and_unsafe_downgrade(
    integration_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    client = integration_client
    client.headers["Origin"] = "http://localhost:3000"
    assert (await client.post("/api/v1/demo/sessions", json={})).status_code == 200
    base = "/api/v1/demo"
    saved = (await client.get(f"{base}/roadmap")).json()
    assert saved["current"]
    body = {
        "command_key": str(uuid4()),
        "weekly_minutes": 60,
        "expected_id": saved["current"]["id"],
        "expected_revision": saved["current"]["revision"],
    }
    assert (await client.post(f"{base}/roadmap/generate", json=body)).status_code == 403
    client.headers["X-CSRF-Token"] = client.cookies.get("interview_prep_csrf") or ""
    response = await client.post(f"{base}/roadmap/generate", json=body)
    assert response.status_code == 200, response.text
    assert response.json()["history"][0]["items"][0]["status"] == "completed"
    result = await migrate(
        database.url.render_as_string(hide_password=False), "downgrade", "0008_project_defense"
    )
    assert result.returncode != 0 and "Unsafe downgrade" in result.stderr
    assert (await client.get(f"{base}/progress")).json()["validated_strengths"] == []


async def test_personal_progress_newest_failed_result_cannot_resurrect_older_rating(
    database: AsyncEngine,
) -> None:
    owner = await prepare(database)
    async with async_sessionmaker(database, expire_on_commit=False)() as session:
        original = await session.scalar(select(AnswerEvaluation))
        user = await session.get(User, owner)
        assert original and user
        rated = AnswerEvaluation(
            owner_id=owner,
            interview_answer_id=original.interview_answer_id,
            version=2,
            supersedes_id=original.id,
            kind=EvaluationKind.MODEL_ASSISTED,
            status=EvaluationStatus.COMPLETED,
            evaluator_version="test-rating-v1",
            rubric_version="answer-rubric-v1",
            provider="Authored test provider",
            model="test-model",
            score=2,
            score_scale_max=4,
            result_payload=evaluation().model_dump(mode="json"),
        )
        session.add(rated)
        await session.commit()
        assert len((await analytics(session, user)).interview_series) == 1
        session.add(
            AnswerEvaluation(
                owner_id=owner,
                interview_answer_id=original.interview_answer_id,
                version=3,
                supersedes_id=rated.id,
                kind=EvaluationKind.MODEL_ASSISTED,
                status=EvaluationStatus.FAILED,
                evaluator_version="test-rating-v1",
                rubric_version="answer-rubric-v1",
                provider="Authored test provider",
                model="test-model",
            )
        )
        await session.commit()
        data = await analytics(session, user)
        assert data.interview_series == [] and data.excluded_interview_evaluations == 1
