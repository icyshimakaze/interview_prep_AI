import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from interview_prep.modules.questions.content import read_manifest
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    PublicationStatus,
    Question,
    QuestionVersion,
)
from interview_prep.modules.questions.seed import BANK_PATH, LEGACY_PATH, load_bank_seed


def test_small_catalogue_is_complete_and_preserves_all_original_titles() -> None:
    manifest, legacy = read_manifest(BANK_PATH, LEGACY_PATH)
    assert len(manifest.questions) == 23
    assert {q.legacy_title for q in manifest.questions if q.legacy_title} == {
        q.title for q in legacy.questions
    }
    assert {q.difficulty.value for q in manifest.questions} == {"easy", "medium", "hard"}
    assert {q.question_type.value for q in manifest.questions} == {
        "written",
        "multiple_choice",
        "short_answer",
        "design",
        "behavioral",
    }
    assert all(q.prompt and q.expected_concepts and q.tags and q.roles for q in manifest.questions)


@pytest.mark.parametrize(
    "problem", ["duplicate", "empty", "missing_legacy", "bad_options", "bad_source"]
)
async def test_bad_manifest_is_rejected_before_any_writes(
    database: AsyncEngine, tmp_path: Path, problem: str
) -> None:
    data = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    if problem == "duplicate":
        data["questions"][1]["key"] = data["questions"][0]["key"]
    elif problem == "empty":
        data["questions"][0]["expected_concepts"] = [" "]
    elif problem == "missing_legacy":
        data["questions"].pop(0)
    elif problem == "bad_options":
        data["questions"][16]["options"][1]["is_correct"] = True
    else:
        data["questions"][0]["source_classification"] = "external_reviewed"
    path = tmp_path / "bad-content.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    async with async_sessionmaker(database)() as session:
        with pytest.raises((ValidationError, ValueError)):
            async with session.begin():
                await load_bank_seed(session, path)
        assert await session.scalar(select(func.count()).select_from(Question)) == 0


async def test_seed_preserves_drafts_versions_and_retirement_and_freezes_concepts(
    database: AsyncEngine,
) -> None:
    async with async_sessionmaker(database)() as session:
        async with session.begin():
            assert await load_bank_seed(session) == 23
        assert await session.scalar(select(func.count()).select_from(QuestionVersion)) == 38
        original = list(
            (
                await session.scalars(
                    select(QuestionVersion).where(QuestionVersion.source_file == "questions.json")
                )
            ).all()
        )
        assert len(original) == 15
        assert all(
            v.prompt is None and v.status == PublicationStatus.DRAFT and v.category is None
            for v in original
        )
        authored = await session.scalar(
            select(QuestionVersion)
            .where(QuestionVersion.status == PublicationStatus.PUBLISHED)
            .limit(1)
        )
        assert authored
        authored.status = PublicationStatus.RETIRED
        await session.commit()
        async with session.begin():
            assert await load_bank_seed(session) == 0
        await session.refresh(authored)
        assert authored.status == PublicationStatus.RETIRED
        assert await session.scalar(select(func.count()).select_from(Question)) == 23
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(
                    ExpectedConcept(
                        question_version_id=authored.id, position=10, text="Late modification"
                    )
                )
                await session.flush()
