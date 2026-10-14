from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_candidate_context import PROFILE, sign_in

from interview_prep.modules.context.models import (
    JobSkillRequirement,
    RequirementPriority,
    ResumeSkillEvidence,
    ReviewStatus,
    Skill,
    TargetJobVersion,
)
from interview_prep.modules.skills.schemas import SkillMatrix


async def test_matrix_authentication_and_account_isolation(
    account_client: httpx.AsyncClient,
) -> None:
    path = "/api/v1/account/skill-evidence"
    assert (await account_client.get(path)).status_code == 401
    await sign_in(account_client)
    await account_client.put("/api/v1/account/profile", json={**PROFILE, "interests": ["Python"]})
    created = (
        await account_client.post(
            "/api/v1/account/targets",
            json={
                "title": "Backend",
                "description": "Python required. No Java experience needed.",
            },
        )
    ).json()
    response = await account_client.get(path, params={"target_id": created["id"]})
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    matrix = SkillMatrix.model_validate(response.json())
    assert matrix.target_id == UUID(created["id"])
    assert {row.importance for row in matrix.rows} == {"Mentioned"}
    assert all(row.competence_state == "Needs assessment validation" for row in matrix.rows)
    assert (await account_client.get(path, params={"target_id": "invalid"})).status_code == 422
    await sign_in(account_client, "bob")
    assert (await account_client.get(path)).json()["rows"] == []
    assert (await account_client.get(path)).json()["targets"] == []
    for id in [created["id"], str(uuid4())]:
        assert (await account_client.get(path, params={"target_id": id})).status_code == 404
    assert (await account_client.get(path, params={"owner_id": "alice"})).json()["rows"] == []


async def test_reviewed_requirements_and_latest_job_version(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await sign_in(account_client)
    await account_client.put(
        "/api/v1/account/profile",
        json={
            **PROFILE,
            "interests": ["Python", "SQL", "Rust"],
        },
    )
    target = (
        await account_client.post(
            "/api/v1/account/targets",
            json={
                "title": "Backend",
                "description": "Python SQL Rust",
            },
        )
    ).json()
    async with async_sessionmaker(database)() as session, session.begin():
        version = await session.scalar(
            select(TargetJobVersion).where(TargetJobVersion.target_job_id == UUID(target["id"]))
        )
        assert version
        for name, priority, review in [
            ("Python", RequirementPriority.ESSENTIAL, ReviewStatus.CONFIRMED),
            ("SQL", RequirementPriority.DESIRABLE, ReviewStatus.CONFIRMED),
            ("Rust", RequirementPriority.ESSENTIAL, ReviewStatus.REJECTED),
        ]:
            skill = Skill(name=name, slug=name.lower())
            session.add(skill)
            await session.flush()
            session.add(
                JobSkillRequirement(
                    owner_id=version.owner_id,
                    target_job_version_id=version.id,
                    skill_id=skill.id,
                    source_excerpt=name,
                    source_start=version.description.index(name),
                    source_end=version.description.index(name) + len(name),
                    priority=priority,
                    review_status=review,
                )
            )
    path = f"/api/v1/account/skill-evidence?target_id={target['id']}"
    matrix = SkillMatrix.model_validate((await account_client.get(path)).json())
    assert {row.name: row.importance for row in matrix.rows} == {
        "Python": "Required",
        "SQL": "Preferred",
        "Rust": "Low relevance",
    }
    assert (
        await account_client.put(
            f"/api/v1/account/targets/{target['id']}",
            json={
                "title": "Backend",
                "description": "Only Python",
                "expected_revision": 1,
            },
        )
    ).status_code == 200
    matrix = SkillMatrix.model_validate((await account_client.get(path)).json())
    assert {row.name: row.importance for row in matrix.rows} == {
        "Python": "Mentioned",
        "SQL": "Low relevance",
        "Rust": "Low relevance",
    }


async def test_demo_matrix_claims_never_validate_and_foreign_target_is_hidden(
    integration_client: httpx.AsyncClient,
) -> None:
    await integration_client.post(
        "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
    )
    path = "/api/v1/demo/skill-evidence"
    matrix = SkillMatrix.model_validate((await integration_client.get(path)).json())
    assert matrix.mode == "demo" and matrix.rows
    assert all(not row.assessment_validated for row in matrix.rows)
    assert any(row.resume_state == "Some evidence" for row in matrix.rows)
    target_id = matrix.targets[0].id
    integration_client.cookies.clear()
    await integration_client.post(
        "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
    )
    assert (
        await integration_client.get(path, params={"target_id": str(target_id)})
    ).status_code == 404


@pytest.mark.parametrize(
    "review,correction",
    [
        (ReviewStatus.REJECTED, None),
        (ReviewStatus.CONFIRMED, "Rust instead of the original claim"),
    ],
)
async def test_resume_rejection_and_correction_replace_matching(
    integration_client: httpx.AsyncClient,
    database: AsyncEngine,
    review: ReviewStatus,
    correction: str | None,
) -> None:
    await integration_client.post(
        "/api/v1/demo/sessions", json={}, headers={"Origin": "http://localhost:3000"}
    )
    async with async_sessionmaker(database)() as session, session.begin():
        item = await session.scalar(select(ResumeSkillEvidence))
        assert item
        item.review_status, item.user_correction = review, correction
    matrix = SkillMatrix.model_validate(
        (await integration_client.get("/api/v1/demo/skill-evidence")).json()
    )
    assert [row.name for row in matrix.rows] == ([] if correction is None else ["Rust"])
    if correction:
        assert "Python and SQL" in matrix.rows[0].sources[0].detail
