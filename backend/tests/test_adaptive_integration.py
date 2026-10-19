from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from skill_helpers import prepare
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_assessments import BASE, configuration, seed, start
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.modules.adaptive import service
from interview_prep.modules.adaptive.engine import select_questions
from interview_prep.modules.adaptive.schemas import Selection, SelectionInput
from interview_prep.modules.assessments.models import (
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentStatus,
    AttemptStatus,
)
from interview_prep.modules.assessments.schemas import Configuration
from interview_prep.modules.context.models import (
    JobSkillRequirement,
    RequirementPriority,
    ReviewStatus,
    Skill,
    TargetJobVersion,
)
from interview_prep.modules.questions.models import Difficulty


async def test_adaptive_start_trace_replay_exact_filters_and_owner_isolation(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    config = {**configuration(None, "easy", "written", 2), "difficulty": None}
    first = await start(account_client, config)
    assert first.selection and first.selection.policy_version == "adaptive-v1"
    assert len(first.selection.choices) == 2
    assert all(c.target_difficulty == Difficulty.EASY for c in first.selection.choices)
    assert first.selection == (await start(account_client, config)).selection
    second = await start(account_client, {**config, "submission_key": str(uuid4())})
    assert second.selection
    assert set(c.question_id for c in first.selection.choices).isdisjoint(
        c.question_id for c in second.selection.choices
    )
    async with async_sessionmaker(database)() as session:
        assessment = await session.scalar(
            select(Assessment).where(
                Assessment.id
                == select(AssessmentQuestion.assessment_id)
                .where(AssessmentQuestion.id == first.questions[0].id)
                .scalar_subquery()
            )
        )
        assert assessment and assessment.configuration
        assert assessment.configuration["selection"] == first.selection.model_dump(mode="json")
        history, count = await service.exposures(session, assessment.owner_id)
        assert count == 4
        assert [h.question_id for h in history] == [
            c.question_id for c in (*first.selection.choices, *second.selection.choices)
        ]
    hard = await start(account_client, configuration(difficulty="hard"))
    assert hard.selection and hard.questions[0].difficulty == Difficulty.HARD
    assert any("exact filter" in n for n in hard.selection.notices)
    await sign_in(account_client, "bob")
    assert (await account_client.get(f"{BASE}/{first.id}")).status_code == 404
    bob = await start(account_client, config)
    assert bob.selection == first.selection  # Alice's exposure/evidence cannot affect Bob.


async def test_owned_target_importance_and_foreign_target_rejected(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    target = (
        await account_client.post(
            "/api/v1/account/targets",
            json={
                "title": "SQL engineer",
                "description": "SQL",
            },
        )
    ).json()
    async with async_sessionmaker(database)() as session, session.begin():
        version = await session.scalar(
            select(TargetJobVersion).where(TargetJobVersion.target_job_id == UUID(target["id"]))
        )
        skill = await session.scalar(select(Skill).where(Skill.name == "SQL"))
        assert version and skill
        session.add(
            JobSkillRequirement(
                owner_id=version.owner_id,
                target_job_version_id=version.id,
                skill_id=skill.id,
                source_excerpt="SQL",
                source_start=0,
                source_end=3,
                priority=RequirementPriority.ESSENTIAL,
                review_status=ReviewStatus.CONFIRMED,
            )
        )
    config = {
        **configuration(None, "easy", "short_answer"),
        "difficulty": None,
        "target_id": target["id"],
    }
    attempt = await start(account_client, config)
    assert attempt.selection and attempt.selection.choices[0].components["job_relevance"] == 60
    await sign_in(account_client, "bob")
    assert (await account_client.post(BASE, json=config)).status_code == 404
    assert (
        await account_client.post(BASE, json={**config, "target_id": str(uuid4())})
    ).status_code == 404
    assert (
        await account_client.post(BASE, json={**config, "owner_id": "alice"})
    ).status_code == 422


@pytest.mark.parametrize(
    "problem,demo,expected",
    [
        ("", False, 5),
        ("multi_skill", False, 0),
        ("ungraded", False, 0),
        ("incomplete", False, 0),
        ("", True, 0),
        ("simulation", False, 4),
    ],
)
async def test_adapter_uses_real_eligible_evidence_and_allocation_history(
    database: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
    demo: bool,
    expected: int,
) -> None:
    owner = await prepare(database, problem=problem, demo=demo)
    inputs: list[SelectionInput] = []

    def capture(data: SelectionInput) -> Selection:
        inputs.append(data)
        return select_questions(data)

    monkeypatch.setattr(service, "select_questions", capture)
    async with async_sessionmaker(database)() as session:
        await service.allocate(
            session,
            owner,
            Configuration(
                question_types=["short_answer"],
                question_count=1,
            ),
            "seed",
        )
    assert len(inputs) == 1 and len(inputs[0].performance) == expected
    assert len(inputs[0].history) == 3  # two assessment allocations, one interview turn
    assert all(p.eligible and p.difficulty == Difficulty.EASY for p in inputs[0].performance)
    if not problem and not demo:
        assert {p.channel for p in inputs[0].performance} == {"assessment", "interview"}


async def test_legacy_configuration_can_resume_and_replay(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    config = configuration()
    attempt = await start(account_client, config)
    # Build an old-format aggregate through the immutable allocation lifecycle.
    async with async_sessionmaker(database)() as session, session.begin():
        row = await session.scalar(select(Assessment))
        assert row and row.configuration
        old = {k: v for k, v in row.configuration.items() if k not in ("target_id", "selection")}
        assert Configuration.model_validate(old).target_id is None
        legacy = Assessment(
            owner_id=row.owner_id,
            title="Legacy configuration",
            status=AssessmentStatus.READY,
            context_version="catalogue-v1",
            policy_version=row.policy_version,
            configuration=old,
        )
        session.add(legacy)
        await session.flush()
        session.add(
            AssessmentQuestion(
                owner_id=row.owner_id,
                assessment_id=legacy.id,
                position=1,
                question_version_id=attempt.questions[0].question_version_id,
            )
        )
        await session.flush()
        key = uuid4()
        previous = AssessmentAttempt(
            owner_id=row.owner_id,
            assessment_id=legacy.id,
            attempt_number=1,
            submission_key=key,
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(UTC),
            deadline_at=datetime.now(UTC) + timedelta(hours=1),
        )
        session.add(previous)
        await session.flush()
        identifier = previous.id
    replay = await start(account_client, {**config, "submission_key": str(key)})
    assert replay.id == identifier and replay.selection is None
    assert replay.configuration and replay.configuration.target_id is None
    response = await account_client.get(f"{BASE}/{identifier}")
    assert response.status_code == 200 and response.json()["selection"] is None
