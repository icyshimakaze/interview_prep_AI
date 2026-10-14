import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentStatus,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.identity.models import User
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    PublicationStatus,
    Question,
    QuestionRole,
    QuestionRubricCriterion,
    QuestionTag,
    QuestionType,
    QuestionVersion,
    QuestionVisibility,
)
from interview_prep.modules.questions.seed import load_bank_seed

BASE = "/api/v1/account/questions"


async def test_storage_bounds_preserve_existing_bookmarks_and_attempts(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed(database)
    await sign_in(account_client)
    monkeypatch.setattr("interview_prep.modules.questions.mutations.MAX_BOOKMARKS", 1)
    monkeypatch.setattr("interview_prep.modules.questions.mutations.MAX_PRACTICE_ATTEMPTS", 1)
    questions = (await account_client.get(BASE)).json()["items"]
    first, second = questions[:2]
    assert (await account_client.put(f"{BASE}/{first['id']}/bookmark", json={})).status_code == 200
    blocked = await account_client.put(f"{BASE}/{second['id']}/bookmark", json={})
    assert blocked.status_code == 409 and blocked.json()["code"] == "bookmark_limit"
    payload = {
        "question_version_id": first["version_id"],
        "submission_key": str(uuid4()),
        "answer_text": "My response",
    }
    assert (
        await account_client.post(f"{BASE}/{first['id']}/attempts", json=payload)
    ).status_code == 200
    blocked = await account_client.post(
        f"{BASE}/{first['id']}/attempts", json={**payload, "submission_key": str(uuid4())}
    )
    assert blocked.status_code == 409 and blocked.json()["code"] == "practice_limit"
    assert (
        await account_client.post(f"{BASE}/{first['id']}/attempts", json=payload)
    ).status_code == 200
    assert (await account_client.get(f"{BASE}/{first['id']}/attempts")).json()["total"] == 1


async def seed(database: AsyncEngine) -> None:
    async with async_sessionmaker(database)() as session, session.begin():
        assert await load_bank_seed(session) == 23


async def pick(client: httpx.AsyncClient, search: str = "Two Sum") -> dict[str, object]:
    response = await client.get(BASE, params={"search": search})
    assert response.status_code == 200, response.text
    data: dict[str, object] = response.json()["items"][0]
    return data


async def test_filters_search_difficulty_roles_and_stable_pagination(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    assert (await account_client.get(BASE)).status_code == 401
    await sign_in(account_client)
    all_rows = (await account_client.get(BASE, params={"limit": 50})).json()
    assert all_rows["total"] == 23 and len(all_rows["items"]) == 23
    cases = [
        ({"category": "Data Structures"}, "category", "Data Structures"),
        ({"subtopic": "Linked List"}, "subtopic", "Linked List"),
        ({"difficulty": "easy"}, "difficulty", "easy"),
        ({"difficulty": "hard"}, "difficulty", "hard"),
        ({"question_type": "multiple_choice"}, "question_type", "multiple_choice"),
        ({"role": "frontend-engineer"}, "roles", "frontend-engineer"),
    ]
    for parameters, field, expected in cases:
        page = (await account_client.get(BASE, params={**parameters, "limit": 50})).json()
        assert page["items"] and page["total"] < 23
        assert all(
            (expected in row[field] if field == "roles" else row[field] == expected)
            for row in page["items"]
        )
    hard = (await account_client.get(BASE, params={"difficulty": "hard"})).json()
    assert hard["total"] == 1 and hard["items"][0]["title"] == "Design a bounded short-link service"
    assert (
        await account_client.get(BASE, params={"difficulty": "hard", "category": "SQL"})
    ).json()["total"] == 0
    for phrase in ["  TWO SUM  ", "monotonic-stack", "all-negative"]:
        assert (await account_client.get(BASE, params={"search": phrase})).json()["total"] >= 1
    literal_underscore = (await account_client.get(BASE, params={"search": "_"})).json()
    assert literal_underscore["total"] == 1
    assert literal_underscore["items"][0]["title"] == "COUNT and NULL"
    for phrase in ["%", "' OR 1=1 --", "no such question"]:
        assert (await account_client.get(BASE, params={"search": phrase})).json()["total"] == 0
    pages = [
        (await account_client.get(BASE, params={"limit": 7, "offset": offset})).json()
        for offset in (0, 7, 14, 21)
    ]
    combined = [row["id"] for page in pages for row in page["items"]]
    assert combined == [row["id"] for row in all_rows["items"]]
    assert len(set(combined)) == 23
    beyond = (await account_client.get(BASE, params={"offset": 100})).json()
    assert beyond["items"] == [] and beyond["total"] == 23
    facets = (await account_client.get(BASE + "/facets")).json()
    assert "SQL" in facets["categories"] and "Stack" in facets["subtopics"]
    assert set(facets["roles"]) == {"software-engineer", "backend-engineer", "frontend-engineer"}


@pytest.mark.parametrize(
    "query",
    [
        {"difficulty": "expert"},
        {"question_type": "unknown"},
        {"limit": 0},
        {"limit": 51},
        {"offset": -1},
        {"search": "x" * 101},
        {"owner_id": str(uuid4())},
    ],
)
async def test_invalid_filters_fail_closed(
    account_client: httpx.AsyncClient, query: dict[str, str | int]
) -> None:
    await sign_in(account_client)
    assert (await account_client.get(BASE, params=query)).status_code == 422


async def test_bookmarks_are_owned_idempotent_and_do_not_mark_attempted(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    question = await pick(account_client)
    path = f"{BASE}/{question['id']}/bookmark"
    responses = await asyncio.gather(*(account_client.put(path, json={}) for _ in range(3)))
    assert all(r.status_code == 200 for r in responses)
    page = (await account_client.get(BASE, params={"bookmarked": "true"})).json()
    assert page["total"] == 1 and page["items"][0]["bookmarked"]
    assert not page["items"][0]["attempted"]
    await sign_in(account_client, "bob")
    assert (await account_client.get(BASE, params={"bookmarked": "true"})).json()["total"] == 0
    assert (await account_client.delete(path)).json() == {"bookmarked": False}
    await sign_in(account_client)
    assert (await account_client.get(BASE, params={"bookmarked": "true"})).json()["total"] == 1
    for _ in range(2):
        assert (await account_client.delete(path)).status_code == 200
    assert (await account_client.get(BASE, params={"bookmarked": "true"})).json()["total"] == 0


async def test_attempts_unlock_exact_owned_version_without_answer_key_leaks(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    question = await pick(account_client, "Process and thread")
    path = f"{BASE}/{question['id']}"
    before = (await account_client.get(path)).json()
    assert before["expected_concepts"] is None and not before["concepts_unlocked"]
    assert len(before["options"]) == 3
    assert all(set(o) == {"id", "text"} for o in before["options"])
    assert "is_correct" not in str(before) and "anchor_" not in str(before)
    body = {
        "question_version_id": question["version_id"],
        "submission_key": str(uuid4()),
        "answer_text": "My own explanation",
    }
    submissions = await asyncio.gather(
        *(account_client.post(path + "/attempts", json=body) for _ in range(3))
    )
    assert all(response.status_code == 200 for response in submissions)
    assert len({response.json()["id"] for response in submissions}) == 1
    assert submissions[0].json()["result_kind"] == "self_review"
    after = (await account_client.get(path)).json()
    assert after["concepts_unlocked"] and after["expected_concepts"]
    assert "is_correct" not in str(after)
    history = (await account_client.get(path + "/attempts")).json()
    assert history["total"] == 1 and history["items"][0]["response"] == body["answer_text"]
    assert (await account_client.get(BASE, params={"attempted": "true"})).json()["total"] == 1
    changed = await account_client.post(
        path + "/attempts", json={**body, "answer_text": "Changed payload"}
    )
    assert changed.status_code == 409 and changed.json()["code"] == "submission_conflict"
    await sign_in(account_client, "bob")
    assert (await account_client.get(path)).json()["expected_concepts"] is None
    assert (await account_client.get(path + "/attempts")).json()["total"] == 0
    attempt_id = history["items"][0]["id"]
    assert (await account_client.delete(path + f"/attempts/{attempt_id}")).status_code == 404
    await sign_in(account_client)
    assert (await account_client.delete(path + f"/attempts/{attempt_id}")).status_code == 204
    assert (await account_client.get(path)).json()["expected_concepts"] is None
    assert (await account_client.get(BASE, params={"attempted": "true"})).json()["total"] == 0


@pytest.mark.parametrize(
    "change",
    [
        {"answer_text": " "},
        {"answer_text": 5},
        {"answer_text": "x" * 10001},
        {"question_version_id": str(uuid4())},
        {"submission_key": "invalid"},
        {"owner_id": str(uuid4())},
    ],
)
async def test_invalid_practice_is_not_saved(
    account_client: httpx.AsyncClient, database: AsyncEngine, change: dict[str, object]
) -> None:
    await seed(database)
    await sign_in(account_client)
    question = await pick(account_client)
    path = f"{BASE}/{question['id']}"
    body = {
        "question_version_id": question["version_id"],
        "submission_key": str(uuid4()),
        "answer_text": "Response",
    }
    response = await account_client.post(path + "/attempts", json={**body, **change})
    assert response.status_code in (409, 422)
    assert (await account_client.get(path + "/attempts")).json()["total"] == 0


async def publish_question(
    session: AsyncSession,
    owner: UUID | None = None,
    question_id: UUID | None = None,
    number: int = 1,
) -> QuestionVersion:
    if question_id is None:
        question = Question(
            owner_id=owner,
            visibility=QuestionVisibility.PRIVATE if owner else QuestionVisibility.GLOBAL,
            canonical_concept="test-private-" + str(uuid4()),
        )
        session.add(question)
        await session.flush()
        question_id = question.id
    version = QuestionVersion(
        question_id=question_id,
        version=number,
        title="Private sentinel question",
        prompt="Explain an invariant for an owned record.",
        category="Private category",
        subtopic="Ownership",
        difficulty="medium",
        question_type=QuestionType.WRITTEN,
        status=PublicationStatus.DRAFT,
        source_classification="authored",
        provenance_reviewed=True,
        source_license="test",
        rubric_version="test",
    )
    session.add(version)
    await session.flush()
    session.add_all(
        [
            ExpectedConcept(question_version_id=version.id, position=1, text="Server owner checks"),
            QuestionTag(question_version_id=version.id, label="sentinel-tag"),
            QuestionRole(question_version_id=version.id, label="private-role"),
            QuestionRubricCriterion(
                question_version_id=version.id,
                code="owner",
                description="Owner checks",
                weight=1,
                anchor_0="None",
                anchor_1="Partial",
                anchor_2="Some",
                anchor_3="Complete",
                anchor_4="Complete with tests",
            ),
        ]
    )
    await session.flush()
    version.status = PublicationStatus.PUBLISHED
    await session.flush()
    return version


async def test_attempt_history_includes_submitted_assessments_across_versions_not_drafts(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    await sign_in(account_client)
    question = await pick(account_client)
    path = f"{BASE}/{question['id']}"
    await account_client.put(path + "/bookmark", json={})
    async with async_sessionmaker(database)() as session, session.begin():
        user = await session.scalar(select(User).where(User.subject == "alice"))
        assert user
        assessment = Assessment(
            owner_id=user.id,
            title="Owned assessment",
            status=AssessmentStatus.READY,
            context_version="test",
            policy_version="test",
        )
        session.add(assessment)
        await session.flush()
        allocation = AssessmentQuestion(
            owner_id=user.id,
            assessment_id=assessment.id,
            question_version_id=UUID(str(question["version_id"])),
            position=1,
        )
        session.add(allocation)
        await session.flush()
        attempt = AssessmentAttempt(
            owner_id=user.id,
            assessment_id=assessment.id,
            attempt_number=1,
            submission_key=uuid4(),
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        session.add(attempt)
        await session.flush()
        response = QuestionAttempt(
            owner_id=user.id,
            assessment_id=assessment.id,
            assessment_attempt_id=attempt.id,
            assessment_question_id=allocation.id,
            status=AnswerStatus.DRAFT,
            answer_text="Unsubmitted draft",
        )
        session.add(response)
        await session.flush()
        response_id = response.id
    assert not (await account_client.get(path)).json()["attempted"]
    async with async_sessionmaker(database)() as session, session.begin():
        draft = await session.get(QuestionAttempt, response_id)
        assert draft
        draft.status, draft.submitted_at = AnswerStatus.SUBMITTED, datetime.now(UTC)
    assert (await account_client.get(path)).json()["concepts_unlocked"]
    async with async_sessionmaker(database)() as session, session.begin():
        latest = await publish_question(session, question_id=UUID(str(question["id"])), number=3)
        latest_id = latest.id
    changed = (await account_client.get(path)).json()
    assert (
        changed["version_id"] == str(latest_id) and changed["attempted"] and changed["bookmarked"]
    )
    assert not changed["concepts_unlocked"] and changed["expected_concepts"] is None
    history = (await account_client.get(path + "/attempts")).json()
    assert history["total"] == 1 and history["items"][0]["channel"] == "assessment"
    assert history["items"][0]["question_version_id"] == question["version_id"]
    body = {
        "question_version_id": str(latest_id),
        "submission_key": str(uuid4()),
        "answer_text": "Owned answer",
    }
    await account_client.post(path + "/attempts", json=body)
    history = (await account_client.get(path + "/attempts", params={"limit": 1})).json()
    assert history["total"] == 2 and history["items"][0]["channel"] == "question_bank"
    assert (await account_client.get(path + "/attempts", params={"limit": 1, "offset": 1})).json()[
        "items"
    ][0]["channel"] == "assessment"
    async with async_sessionmaker(database)() as session, session.begin():
        version = await session.get(QuestionVersion, latest_id)
        assert version
        version.status = PublicationStatus.RETIRED
    assert (await account_client.get(BASE, params={"search": "Private sentinel"})).json()[
        "total"
    ] == 0
    assert (await account_client.get(BASE, params={"active": "false"})).json()["total"] == 1
    assert (
        await account_client.post(path + "/attempts", json=body)
    ).status_code == 200  # retry survives retirement
    assert (
        await account_client.post(path + "/attempts", json={**body, "submission_key": str(uuid4())})
    ).status_code == 409
    assert (await account_client.get(path + "/attempts")).json()["total"] == 2


async def test_private_content_and_facets_cannot_cross_accounts(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    async with async_sessionmaker(database)() as session, session.begin():
        user = await session.scalar(select(User).where(User.subject == "alice"))
        assert user
        version = await publish_question(session, owner=user.id)
        question_id = version.question_id
    assert (await account_client.get(BASE)).json()["total"] == 1
    await sign_in(account_client, "bob")
    assert (await account_client.get(BASE)).json()["total"] == 0
    assert (await account_client.get(BASE + "/facets")).json() == {
        "categories": [],
        "subtopics": [],
        "roles": [],
    }
    for resource in [str(question_id), str(uuid4())]:
        assert (await account_client.get(f"{BASE}/{resource}")).status_code == 404
        assert (await account_client.get(f"{BASE}/{resource}/attempts")).status_code == 404
        assert (await account_client.put(f"{BASE}/{resource}/bookmark", json={})).status_code == 404


async def test_demo_bookmark_and_attempt_require_csrf_and_remain_simulation(
    integration_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await seed(database)
    base = "/api/v1/demo/questions"
    assert (await integration_client.get(base)).status_code == 401
    origin = {"Origin": "http://localhost:3000"}
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=origin)
    item = (await integration_client.get(base)).json()["items"][0]
    path = f"{base}/{item['id']}"
    body = {
        "question_version_id": item["version_id"],
        "submission_key": str(uuid4()),
        "answer_text": "Fictional practice answer",
    }
    assert (
        await integration_client.post(path + "/attempts", json=body, headers=origin)
    ).status_code == 403
    assert (
        await integration_client.put(path + "/bookmark", json={}, headers=origin)
    ).status_code == 403
    headers = {**origin, "X-CSRF-Token": integration_client.cookies["interview_prep_csrf"]}
    assert (
        await integration_client.put(path + "/bookmark", json={}, headers=headers)
    ).status_code == 200
    response = await integration_client.post(path + "/attempts", json=body, headers=headers)
    assert response.status_code == 200 and response.json()["result_kind"] == "simulation"
    integration_client.cookies.clear()
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=origin)
    assert (await integration_client.get(base, params={"bookmarked": "true"})).json()["total"] == 0
    assert (await integration_client.get(path + "/attempts")).json()["total"] == 0
