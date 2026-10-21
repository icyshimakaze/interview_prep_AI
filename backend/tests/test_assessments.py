import asyncio
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import sign_in

from interview_prep.modules.assessments.evaluation import (
    ConceptualInput,
    MockAIProvider,
    validate_evaluation,
)
from interview_prep.modules.assessments.models import AssessmentAttempt, QuestionAttempt
from interview_prep.modules.assessments.schemas import AttemptView, StartInput
from interview_prep.modules.assessments.scoring import score_options, score_short_answer
from interview_prep.modules.questions.models import (
    PublicationStatus,
    QuestionOption,
    QuestionVersion,
)
from interview_prep.modules.questions.seed import load_assessment_seed, load_bank_seed
from interview_prep.modules.roadmaps.models import ProgressEvent

BASE = "/api/v1/account/assessments"


async def seed(database: AsyncEngine) -> None:
    async with async_sessionmaker(database)() as session, session.begin():
        await load_bank_seed(session)
        assert await load_assessment_seed(session) == 6
        assert await load_assessment_seed(session) == 0


def configuration(
    category: str | None = "DBMS",
    difficulty: str = "easy",
    kind: str = "multiple_select",
    count: int = 1,
) -> dict[str, object]:
    return {
        "category": category,
        "difficulty": difficulty,
        "question_types": [kind],
        "question_count": count,
        "submission_key": str(uuid4()),
    }


async def start(client: httpx.AsyncClient, config: dict[str, object] | None = None) -> AttemptView:
    response = await client.post(BASE, json=config or configuration())
    assert response.status_code == 200, response.text
    return AttemptView.model_validate(response.json())


async def save(
    client: httpx.AsyncClient,
    attempt: AttemptView,
    *,
    selections: list[UUID] | None = None,
    answer: str | None = None,
    index: int = 0,
) -> AttemptView:
    response = await client.put(
        f"{BASE}/{attempt.id}/questions/{attempt.questions[index].id}",
        json={
            "revision": attempt.revision,
            "answer_text": answer,
            "selected_option_ids": [str(s) for s in selections or []],
        },
    )
    assert response.status_code == 200, response.text
    return AttemptView.model_validate(response.json())


async def correct_options(database: AsyncEngine, version: UUID) -> list[UUID]:
    async with async_sessionmaker(database)() as session:
        return list(
            (
                await session.scalars(
                    select(QuestionOption.id).where(
                        QuestionOption.question_version_id == version,
                        QuestionOption.is_correct.is_(True),
                    )
                )
            ).all()
        )


@pytest.mark.parametrize(
    ("response", "expected"), [("2", 1), (" 2 ", 1), ("2.0", 0), ("Two", 0), ("", 0)]
)
def test_literal_short_answer_scoring(response: str, expected: int) -> None:
    assert score_short_answer(response, [("2", "literal-v1")]) == expected


def test_objective_sets_and_unsupported_normalization() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    assert score_options([b, a], [a, b]) == 1
    assert score_options([a], [a, b]) == 0
    assert score_options([a, b, c], [a, b]) == 0
    assert score_options([], []) == 0
    with pytest.raises(ValueError):
        score_short_answer("2", [("2", "unknown")])


async def test_mock_provider_formula_and_output_validation() -> None:
    provider = MockAIProvider()
    concepts = ["Writes maintain index entries", "Indexes consume storage"]
    result = await provider.evaluate(
        ConceptualInput(
            prompt="Explain indexes",
            response="Writes maintain index entries.",
            expected_concepts=tuple(concepts),
            rubric=("Reasoning",),
        )
    )
    assert result.score == 2 and result.kind == "simulation"
    assert (
        result.matched_concepts == concepts[:1] and "does not judge correctness" in result.feedback
    )
    assert validate_evaluation(result, provider, concepts) == result
    with pytest.raises(ValueError):
        validate_evaluation(
            result.model_copy(update={"score": 99}),
            provider,
            concepts,
        )
    patches: list[dict[str, object]] = [
        {"score": 5},
        {"score": True},
        {"kind": "model_assisted"},
        {"matched_concepts": ["invented"]},
        {"matched_concepts": [concepts[0], concepts[0]]},
        {"extra": "unsafe"},
    ]
    for patch in patches:
        with pytest.raises(ValueError):
            validate_evaluation({**result.model_dump(), **patch}, provider, concepts)


async def test_configure_filter_start_resume_and_disclosure(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    assert (await account_client.get(BASE + "/options")).status_code == 401
    await sign_in(account_client)
    options = (await account_client.get(BASE + "/options")).json()
    assert options["conceptual_provider"] == "MockAIProvider"
    assert any(
        i["difficulty"] == "hard" and i["question_type"] == "multiple_select"
        for i in options["inventory"]
    )
    config = configuration(difficulty="hard")
    attempt = await start(account_client, config)
    question = attempt.questions[0]
    assert question.difficulty == "hard" and question.category == "DBMS"
    assert question.question_type == "multiple_select" and question.review is None
    response = await account_client.get(f"{BASE}/{attempt.id}")
    assert response.json() == attempt.model_dump(mode="json")
    for forbidden in (
        "is_correct",
        "accepted_answers",
        "expected_concepts",
        "correct_option_ids",
        "rubric",
        "evaluation_metadata",
    ):
        assert forbidden not in response.text
    repeated = await start(account_client, config)
    assert repeated.id == attempt.id
    conflict = await account_client.post(BASE, json={**config, "question_count": 2})
    assert conflict.status_code == 409 and conflict.json()["code"] == "submission_conflict"
    unavailable = await account_client.post(
        BASE, json=configuration("SQL", "hard", "multiple_choice")
    )
    assert unavailable.status_code == 409 and unavailable.json()["code"] == "assessment_pool"


@pytest.mark.parametrize(
    "kind,category",
    [
        ("multiple_choice", "Operating Systems"),
        ("multiple_select", "DBMS"),
        ("short_answer", "SQL"),
    ],
)
async def test_objective_submit_review_replay_and_persistence(
    account_client: httpx.AsyncClient, database: AsyncEngine, kind: str, category: str
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client, configuration(category, "easy", kind))
    if kind == "short_answer":
        attempt = await save(account_client, attempt, answer=" 2 ")
    else:
        choices = await correct_options(database, attempt.questions[0].question_version_id)
        attempt = await save(account_client, attempt, selections=choices)
    assert attempt.status == "in_progress" and attempt.questions[0].review is None
    response = await account_client.post(
        f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
    )
    assert response.status_code == 200, response.text
    completed = AttemptView.model_validate(response.json())
    review = completed.questions[0].review
    assert completed.status == "completed" and completed.completed_at and review
    assert review.score == review.max_score == 1 and review.is_correct
    assert (
        review.result_kind == "deterministic"
        and review.metadata
        and review.metadata.provider == "deterministic"
    )
    assert completed.categories[0].objective_correct == completed.categories[0].objective_total == 1
    retry = await account_client.post(f"{BASE}/{attempt.id}/submit", json={"revision": 1})
    assert retry.json() == response.json()
    assert (
        await account_client.put(
            f"{BASE}/{attempt.id}/questions/{attempt.questions[0].id}",
            json={"revision": completed.revision, "answer_text": "changed"},
        )
    ).status_code == 409
    async with async_sessionmaker(database)() as session:
        answer = await session.scalar(
            select(QuestionAttempt).where(QuestionAttempt.assessment_attempt_id == attempt.id)
        )
        assert answer and answer.score == 1 and answer.submitted_at and answer.evaluation_metadata
        assert (
            await session.scalar(
                select(func.count())
                .select_from(ProgressEvent)
                .where(ProgressEvent.assessment_attempt_id == attempt.id)
            )
            == 1
        )
        with pytest.raises(IntegrityError):
            answer.score = 0
            await session.flush()


async def test_multiselect_partial_wrong_and_invalid_options(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client)
    q = attempt.questions[0]
    for selections in [[str(uuid4())], [str(q.options[0].id)] * 2]:
        response = await account_client.put(
            f"{BASE}/{attempt.id}/questions/{q.id}",
            json={"revision": 1, "selected_option_ids": selections},
        )
        assert response.status_code == 422
    attempt = await save(
        account_client,
        attempt,
        selections=(await correct_options(database, q.question_version_id))[:1],
    )
    completed = AttemptView.model_validate(
        (
            await account_client.post(
                f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
            )
        ).json()
    )
    assert completed.questions[0].review and completed.questions[0].review.score == 0
    assert completed.categories[0].objective_correct == 0


async def test_saved_navigation_skips_conceptual_category_and_history(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client, configuration(None, "easy", "written", 2))
    attempt = await save(
        account_client,
        attempt,
        answer="Hostname resolution returns address records; caching reduces repeated lookups. "
        "TLS establishes encryption separately.",
    )
    reread = AttemptView.model_validate((await account_client.get(f"{BASE}/{attempt.id}")).json())
    assert reread.questions[0].answer_text == attempt.questions[0].answer_text
    stale = await account_client.put(
        f"{BASE}/{attempt.id}/questions/{attempt.questions[1].id}",
        json={"revision": 1, "answer_text": "stale"},
    )
    assert stale.status_code == 409 and stale.json()["code"] == "assessment_revision"
    completed = AttemptView.model_validate(
        (
            await account_client.post(
                f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
            )
        ).json()
    )
    assert (
        completed.questions[1].skipped
        and completed.questions[1].review
        and completed.questions[1].review.score is None
    )
    review = completed.questions[0].review
    assert review and review.result_kind == "simulation" and review.is_correct is None
    assert (
        review.max_score == 4 and review.metadata and review.metadata.provider == "MockAIProvider"
    )
    assert sum(c.skipped for c in completed.categories) == 1
    assert sum(c.conceptual_max for c in completed.categories) == 4
    assert all(c.objective_total == 0 for c in completed.categories)
    page = (await account_client.get(BASE, params={"limit": 1})).json()
    assert page["total"] == 1 and page["items"][0]["simulated"] is True
    assert (await account_client.get(BASE, params={"offset": 1})).json()["items"] == []


async def test_expiry_abandon_invalid_state_and_ownership(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client)
    async with async_sessionmaker(database)() as session, session.begin():
        row = await session.get(AssessmentAttempt, attempt.id)
        assert row
        row.deadline_at = datetime.now(UTC) - timedelta(seconds=1)
    assert (await account_client.get(f"{BASE}/{attempt.id}")).json()["status"] == "expired"
    for path in (f"{BASE}/{attempt.id}/submit",):
        response = await account_client.post(path, json={"revision": 1})
        assert response.status_code == 409 and response.json()["code"] == "assessment_expired"
    assert (
        await account_client.put(
            f"{BASE}/{attempt.id}/questions/{attempt.questions[0].id}", json={"revision": 1}
        )
    ).status_code == 409
    abandoned = await account_client.post(f"{BASE}/{attempt.id}/abandon", json={"revision": 1})
    assert abandoned.json()["status"] == "abandoned"
    assert (
        await account_client.post(f"{BASE}/{attempt.id}/submit", json={"revision": 2})
    ).status_code == 409
    await sign_in(account_client, "bob")
    assert (await account_client.get(BASE)).json()["total"] == 0
    assert (await account_client.get(f"{BASE}/{attempt.id}")).status_code == 404
    assert (
        await account_client.post(f"{BASE}/{attempt.id}/submit", json={"revision": 2})
    ).status_code == 404
    assert (
        await account_client.post(f"{BASE}/{attempt.id}/abandon", json={"revision": 2})
    ).status_code == 404
    assert (
        await account_client.put(
            f"{BASE}/{attempt.id}/questions/{attempt.questions[0].id}", json={"revision": 2}
        )
    ).status_code == 404


class InvalidProvider:
    name = "InvalidProvider"
    version = "test-v1"
    kind: Literal["simulation", "model_assisted"] = "simulation"

    async def evaluate(self, content: ConceptualInput) -> object:
        return {"score": 99, "kind": "simulation", "feedback": "bad", "matched_concepts": []}


class UnavailableProvider(InvalidProvider):
    async def evaluate(self, content: ConceptualInput) -> object:
        raise RuntimeError("private-provider-error")


class TimedOutProvider(InvalidProvider):
    async def evaluate(self, content: ConceptualInput) -> object:
        raise TimeoutError("private-provider-timeout")


class InvalidRubricProvider(InvalidProvider):
    async def evaluate(self, content: ConceptualInput) -> object:
        from interview_prep.ai.mock import evaluate
        from interview_prep.ai.schemas import AnswerInput

        result = evaluate(
            AnswerInput(
                question=content.prompt,
                answer=content.response,
                expected_concepts=list(content.expected_concepts),
                profile=content.profile,
            )
        ).model_dump()
        result["kind"] = "simulation"
        result["rubric_results"][0]["score"] = 4  # Mock cannot assess correctness.
        return result


@pytest.mark.parametrize(
    "provider_class",
    [InvalidProvider, UnavailableProvider, TimedOutProvider, InvalidRubricProvider],
)
async def test_provider_failure_rolls_back_and_retries(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
    provider_class: type[InvalidProvider],
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client, configuration("DBMS", "medium", "written"))
    attempt = await save(
        account_client, attempt, answer="Writes maintain index entries and indexes consume storage."
    )
    with monkeypatch.context() as patch:
        patch.setattr(MockAIProvider, "evaluate", provider_class.evaluate)
        response = await account_client.post(
            f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
        )
        assert response.status_code == 503
        assert "private-provider" not in response.text
        current = AttemptView.model_validate(
            (await account_client.get(f"{BASE}/{attempt.id}")).json()
        )
        assert (
            current.status == "in_progress"
            and current.revision == attempt.revision
            and current.questions[0].review is None
        )
        async with async_sessionmaker(database)() as session:
            stored = await session.scalar(
                select(QuestionAttempt).where(QuestionAttempt.assessment_attempt_id == attempt.id)
            )
            assert stored and stored.score is None and stored.evaluation_metadata is None
            assert stored.answer_text == attempt.questions[0].answer_text
            assert stored.status == "draft" and stored.submitted_at is None
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(ProgressEvent)
                    .where(ProgressEvent.assessment_attempt_id == attempt.id)
                )
                == 0
            )
    assert (
        await account_client.post(
            f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision}
        )
    ).json()["status"] == "completed"


async def test_retired_content_remains_frozen_for_started_attempt(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client)
    attempt = await start(account_client)
    async with async_sessionmaker(database)() as session, session.begin():
        version = await session.get(QuestionVersion, attempt.questions[0].question_version_id)
        assert version
        version.status = PublicationStatus.RETIRED
    assert (await account_client.post(BASE, json=configuration())).status_code == 409
    completed = await account_client.post(f"{BASE}/{attempt.id}/submit", json={"revision": 1})
    assert completed.status_code == 200 and completed.json()["questions"][0]["skipped"]


async def test_concurrent_start_and_submit_have_one_result(
    account_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    await sign_in(account_client)
    config = configuration("SQL", "easy", "short_answer")
    first, second = await asyncio.gather(
        start(account_client, config), start(account_client, config)
    )
    assert first.id == second.id
    attempt = await save(account_client, first, answer="2")
    responses = await asyncio.gather(
        *[
            account_client.post(f"{BASE}/{attempt.id}/submit", json={"revision": attempt.revision})
            for _ in range(2)
        ]
    )
    assert all(r.status_code == 200 for r in responses)
    assert responses[0].json() == responses[1].json()
    assert (await account_client.get(BASE)).json()["total"] == 1


async def test_mcq_cardinality_text_validation_and_attempt_limits(
    account_client: httpx.AsyncClient, database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    await seed(database)
    await sign_in(account_client)
    monkeypatch.setattr("interview_prep.modules.assessments.service.MAX_UNFINISHED", 1)
    attempt = await start(account_client, configuration("Algorithms", "easy", "multiple_choice"))
    q = attempt.questions[0]
    invalid_bodies: list[dict[str, object]] = [
        {"selected_option_ids": [str(o.id) for o in q.options[:2]]},
        {"answer_text": "unsupported text"},
        {"answer_text": "x" * 10001},
    ]
    for body in invalid_bodies:
        response = await account_client.put(
            f"{BASE}/{attempt.id}/questions/{q.id}", json={"revision": attempt.revision, **body}
        )
        assert response.status_code == 422
    assert (await account_client.post(BASE, json=configuration())).json()[
        "code"
    ] == "assessment_limit"
    assert (
        await account_client.put(f"{BASE}/{attempt.id}/questions/{uuid4()}", json={"revision": 1})
    ).status_code == 404
    await account_client.post(f"{BASE}/{attempt.id}/abandon", json={"revision": 1})
    assert (await account_client.post(BASE, json=configuration())).status_code == 200
    monkeypatch.setattr("interview_prep.modules.assessments.service.MAX_ATTEMPTS", 2)
    assert (await account_client.post(BASE, json=configuration())).status_code == 409


async def test_demo_csrf_and_account_separation(
    integration_client: httpx.AsyncClient, database: AsyncEngine
) -> None:
    await seed(database)
    client = integration_client
    assert (
        await client.post(
            "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
        )
    ).status_code == 200
    demo = "/api/v1/demo/assessments"
    assert (await client.get(demo + "/options")).status_code == 200
    history = (await client.get(demo)).json()
    old = AttemptView.model_validate(
        (await client.get(f"{demo}/{history['items'][0]['id']}")).json()
    )
    assert old.simulated and all(c.objective_total == 0 for c in old.categories)
    assert all(q.review and q.review.score is None for q in old.questions)
    assert (await client.post(demo, json=configuration())).status_code == 403
    headers = {
        "Origin": "http://localhost:3000",
        "X-CSRF-Token": client.cookies["interview_prep_csrf"],
    }
    started = await client.post(demo, json=configuration(), headers=headers)
    assert started.status_code == 200, started.text
    attempt = AttemptView.model_validate(started.json())
    assert (
        await client.post(f"{demo}/{attempt.id}/submit", json={"revision": 1})
    ).status_code == 403
    assert (
        await client.post(f"{demo}/{attempt.id}/submit", json={"revision": 1}, headers=headers)
    ).status_code == 200
    assert (await client.get(f"{BASE}/{attempt.id}")).status_code == 401


@pytest.mark.parametrize(
    "patch",
    [
        {"question_count": 0},
        {"question_count": 13},
        {"question_count": True},
        {"question_types": ["design"]},
        {"difficulty": "expert"},
        {"owner_id": str(uuid4())},
    ],
)
def test_configuration_bounds(patch: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        StartInput.model_validate({**configuration(), **patch})
