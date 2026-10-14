"""Explicit, transactional catalogue publication; never runs during API reads."""

import argparse
import asyncio
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.core.config import ROOT, get_settings
from interview_prep.db.models import Base
from interview_prep.db.session import create_engine
from interview_prep.modules.context.models import Skill
from interview_prep.modules.questions.content import BankManifest, read_manifest
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    PublicationStatus,
    Question,
    QuestionOption,
    QuestionRole,
    QuestionRubricCriterion,
    QuestionSkill,
    QuestionTag,
    QuestionType,
    QuestionVersion,
    QuestionVisibility,
    ShortAnswerKey,
)
from interview_prep.seeding import LegacyManifest, load_legacy_seed, seed_id

CONTENT_DIRECTORY = Path(os.environ.get("QUESTION_CONTENT_DIR", str(ROOT / "content")))
BANK_PATH = CONTENT_DIRECTORY / "question-bank-v1.json"
LEGACY_PATH = CONTENT_DIRECTORY / "legacy-v1.json"
ASSESSMENT_PATH = CONTENT_DIRECTORY / "assessment-bank-v1.json"


def bank_id(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"interview-prep/question-bank-v1/{name}")


async def publish_manifest(
    session: AsyncSession,
    manifest: BankManifest,
    legacy: LegacyManifest,
) -> int:
    # Serialize global publication, including concurrent reruns of the operator command.
    await session.execute(text("SELECT pg_advisory_xact_lock(7345015)"))
    legacy_by_title = {entry.title: entry for entry in legacy.questions}
    published = 0
    source_file = f"content/{manifest.content_version}.json"
    for entry in manifest.questions:
        original = legacy_by_title.get(entry.legacy_title or "")
        question_id = original.id if original else bank_id(f"question/{entry.key}")
        number = 2 if original else 1
        version_id = bank_id(f"version/{entry.key}/{number}")
        await session.execute(
            insert(Question)
            .values(
                id=question_id,
                visibility=QuestionVisibility.GLOBAL,
                canonical_concept=entry.key,
            )
            .on_conflict_do_nothing(index_elements=[Question.id])
        )
        question = await session.get(Question, question_id)
        if (
            question is None
            or question.owner_id is not None
            or question.visibility != QuestionVisibility.GLOBAL
        ):
            raise ValueError("Conflicting catalogue ownership")
        existing = await session.get(QuestionVersion, version_id)
        if existing:
            if existing.question_id != question_id or existing.source_file != source_file:
                raise ValueError("Conflicting catalogue version")
            continue  # Preserve retired content and later editorial versions.
        if await session.scalar(
            select(QuestionVersion.id)
            .where(
                QuestionVersion.question_id == question_id,
                QuestionVersion.version >= number,
            )
            .limit(1)
        ):
            raise ValueError("Editorial version collision; create a reviewed new manifest version")
        version = QuestionVersion(
            id=version_id,
            question_id=question_id,
            version=number,
            title=entry.title,
            prompt=entry.prompt,
            question_type=entry.question_type,
            difficulty=entry.difficulty,
            status=PublicationStatus.DRAFT,
            category=entry.category,
            subtopic=entry.subtopic,
            source_classification=entry.source_classification,
            source_file=source_file,
            source_commit="48fcd90" if original else None,
            original_topic=original.original_topic if original else None,
            source_license="project-authored prompt and concepts",
            provenance_reviewed=True,
            rubric_version="bank-concepts-v1",
        )
        session.add(version)
        await session.flush()
        for position, concept in enumerate(entry.expected_concepts, 1):
            session.add(
                ExpectedConcept(question_version_id=version.id, position=position, text=concept)
            )
        session.add_all([QuestionTag(question_version_id=version.id, label=t) for t in entry.tags])
        session.add_all(
            [QuestionRole(question_version_id=version.id, label=r) for r in entry.roles]
        )
        if original:
            skill_id = seed_id(f"skill/{original.topic_id}")
        else:
            skill_id = bank_id(f"skill/{entry.category}")
            await session.execute(
                insert(Skill)
                .values(id=skill_id, slug="bank-" + entry.key, name=entry.category)
                .on_conflict_do_nothing(index_elements=[Skill.id])
            )
        session.add(QuestionSkill(question_version_id=version.id, skill_id=skill_id))
        if entry.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT):
            session.add_all(
                [
                    QuestionOption(
                        question_version_id=version.id,
                        position=index,
                        text=o.text,
                        is_correct=o.is_correct,
                    )
                    for index, o in enumerate(entry.options, 1)
                ]
            )
        elif entry.question_type == QuestionType.SHORT_ANSWER:
            session.add_all(
                [
                    ShortAnswerKey(
                        question_version_id=version.id,
                        normalized_answer=a,
                        normalization_version="literal-v1",
                    )
                    for a in entry.accepted_answers
                ]
            )
        else:
            session.add(
                QuestionRubricCriterion(
                    question_version_id=version.id,
                    code="reasoning",
                    description="Explain: " + "; ".join(entry.expected_concepts),
                    weight=1,
                    anchor_0="No relevant response",
                    anchor_1="Names a relevant idea without explanation",
                    anchor_2="Explains some expected concepts but misses a key constraint",
                    anchor_3="Explains expected concepts and handles the stated constraints",
                    anchor_4="Explains concepts, constraints, edge cases and tradeoffs clearly",
                )
            )
        await session.flush()
        version.status = PublicationStatus.PUBLISHED
        await session.flush()
        published += 1
    return published


async def load_bank_seed(session: AsyncSession, path: Path = BANK_PATH) -> int:
    manifest, legacy = await asyncio.to_thread(read_manifest, path, LEGACY_PATH)
    await session.execute(text("SELECT pg_advisory_xact_lock(7345015)"))
    await load_legacy_seed(session, LEGACY_PATH)
    return await publish_manifest(session, manifest, legacy)


async def load_assessment_seed(session: AsyncSession) -> int:
    manifest, legacy = await asyncio.to_thread(read_manifest, ASSESSMENT_PATH, LEGACY_PATH)
    return await publish_manifest(session, manifest, legacy)


async def run_seed(path: Path, apply: bool) -> None:
    manifest, _ = await asyncio.to_thread(read_manifest, path, LEGACY_PATH)
    supplemental, legacy = await asyncio.to_thread(read_manifest, ASSESSMENT_PATH, LEGACY_PATH)
    include_supplemental = manifest.content_version != supplemental.content_version
    if not apply:
        print(
            json.dumps(
                {
                    "validated_questions": len(manifest.questions)
                    + (len(supplemental.questions) if include_supplemental else 0),
                    "writes": False,
                }
            )
        )
        return
    Base.registry.configure()
    engine = create_engine(get_settings())
    try:
        async with async_sessionmaker(engine)() as session, session.begin():
            count = await load_bank_seed(session, path)
            if include_supplemental:
                count += await publish_manifest(session, supplemental, legacy)
        print(json.dumps({"new_versions": count}))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate/publish the reviewed small question bank"
    )
    parser.add_argument("--manifest", type=Path, default=BANK_PATH)
    parser.add_argument(
        "--apply", action="store_true", help="Publish transactionally to configured DB"
    )
    args = parser.parse_args()
    asyncio.run(run_seed(args.manifest, args.apply))


if __name__ == "__main__":
    main()
