import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.modules.context.models import Skill, SkillAlias
from interview_prep.modules.questions.models import Question, QuestionSkill, QuestionVersion
from interview_prep.seeding import load_legacy_seed

MANIFEST = Path(__file__).resolve().parents[2] / "content" / "legacy-v1.json"


async def test_load_exact_legacy_drafts_idempotently_and_preserve_review(
    database: AsyncEngine,
) -> None:
    async with async_sessionmaker(database)() as session:
        async with session.begin():
            summary = await load_legacy_seed(session, MANIFEST)
        assert summary.questions == 15 and summary.skills == 6
        version = await session.scalar(select(QuestionVersion).limit(1))
        assert version is not None
        assert version.prompt is None and version.difficulty is None
        assert version.source_commit == "48fcd90" and not version.provenance_reviewed
        await session.execute(
            update(QuestionVersion)
            .where(QuestionVersion.id == version.id)
            .values(prompt="Editorial work in progress")
        )
        await session.commit()
        async with session.begin():
            await load_legacy_seed(session, MANIFEST)
        for model, expected in [
            (Question, 15),
            (QuestionVersion, 15),
            (QuestionSkill, 15),
            (Skill, 6),
            (SkillAlias, 7),
        ]:
            assert await session.scalar(select(func.count()).select_from(model)) == expected
        await session.refresh(version)
        assert version.prompt == "Editorial work in progress"
        assert (
            await session.scalar(
                select(func.count())
                .select_from(QuestionVersion)
                .where(QuestionVersion.status == "published")
            )
            == 0
        )


@pytest.mark.parametrize("mutation", ["count", "identity", "version", "provenance"])
async def test_reject_invalid_seed_before_writing(
    database: AsyncEngine, tmp_path: Path, mutation: str
) -> None:
    data = json.loads(MANIFEST.read_text())
    if mutation == "count":
        data["questions"].pop()
    if mutation == "identity":
        data["questions"][0]["id"] = "00000000-0000-0000-0000-000000000000"
    if mutation == "version":
        data["schema_version"] = 2
    if mutation == "provenance":
        data["source_sha256"]["questions.json"] = "bad"
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data))
    async with async_sessionmaker(database)() as session:
        with pytest.raises((ValidationError, ValueError)):
            async with session.begin():
                await load_legacy_seed(session, path)
        assert await session.scalar(select(func.count()).select_from(Question)) == 0
