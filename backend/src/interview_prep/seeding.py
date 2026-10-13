"Versioned editorial seeds, loaded transactionally without invented curriculum."

import argparse
import asyncio
import json
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interview_prep.core.config import ROOT, get_settings
from interview_prep.db.models import Base
from interview_prep.db.session import create_engine
from interview_prep.modules.context.models import Skill, SkillAlias
from interview_prep.modules.questions.models import (
    PublicationStatus,
    Question,
    QuestionSkill,
    QuestionVersion,
    QuestionVisibility,
)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: Literal["questions.json"]
    commit: Literal["48fcd90"]


class LegacyQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    topic_id: str = Field(min_length=1, max_length=100)
    original_topic: str = Field(min_length=1, max_length=150)
    title: str = Field(min_length=1, max_length=300)
    status: Literal["draft"]
    difficulty: None
    prompt: None
    rubric: None
    source: Source
    provenance_review: Literal["required"]


class LegacyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    source_commit: Literal["48fcd90"]
    source_sha256: dict[str, str]
    usage: str
    topic_aliases: dict[str, str]
    questions: list[LegacyQuestion]
    roadmap_suggestions: list[dict[str, object]]

    @model_validator(mode="after")
    def reconcile(self) -> "LegacyManifest":
        if len(self.questions) != 15 or len({q.id for q in self.questions}) != 15:
            raise ValueError("Legacy seed requires exactly 15 unique titles")
        for q in self.questions:
            expected = uuid5(
                NAMESPACE_URL, f"interview-prep/legacy-v1/{q.original_topic}/{q.title}"
            )
            if q.id != expected or self.topic_aliases.get(q.original_topic) != q.topic_id:
                raise ValueError("Legacy seed identity or topic mismatch")
        expected_hash = "8324fd68ac2c257b5d5c0d4f82406e16b2eb62ea22fbd7a4ffb618ba856a95b9"
        if self.source_sha256.get("questions.json") != expected_hash:
            raise ValueError("Unexpected legacy provenance")
        return self


class SeedSummary(BaseModel):
    schema_version: Literal[1] = 1
    questions: int
    skills: int


def seed_id(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"interview-prep/content-v1/{name}")


async def load_legacy_seed(session: AsyncSession, path: Path) -> SeedSummary:
    """Caller owns the transaction. Re-runs preserve editorial changes."""
    content = await asyncio.to_thread(path.read_text, encoding="utf-8")
    manifest = LegacyManifest.model_validate_json(content)
    names = {
        "arrays": "Arrays",
        "linked-list": "Linked List",
        "stack": "Stack",
        "queue": "Queue",
        "dbms": "DBMS",
        "operating-system": "Operating System",
    }
    for slug, name in names.items():
        skill_id = seed_id(f"skill/{slug}")
        await session.execute(
            insert(Skill)
            .values(id=skill_id, slug=slug, name=name)
            .on_conflict_do_nothing(index_elements=[Skill.id])
        )
        skill = await session.get(Skill, skill_id)
        if skill is None or skill.slug != slug:
            raise ValueError("Conflicting seed skill identity")
    for alias, slug in manifest.topic_aliases.items():
        await session.execute(
            insert(SkillAlias)
            .values(id=seed_id(f"alias/{alias}"), skill_id=seed_id(f"skill/{slug}"), alias=alias)
            .on_conflict_do_nothing(index_elements=[SkillAlias.id])
        )
    for entry in manifest.questions:
        await session.execute(
            insert(Question)
            .values(
                id=entry.id, visibility=QuestionVisibility.GLOBAL, canonical_concept=str(entry.id)
            )
            .on_conflict_do_nothing(index_elements=[Question.id])
        )
        question = await session.get(Question, entry.id)
        if (
            question is None
            or question.owner_id is not None
            or question.visibility != QuestionVisibility.GLOBAL
        ):
            raise ValueError("Conflicting seed question ownership")
        version_id = seed_id(f"question/{entry.id}/1")
        await session.execute(
            insert(QuestionVersion)
            .values(
                id=version_id,
                question_id=entry.id,
                version=1,
                title=entry.title,
                status=PublicationStatus.DRAFT,
                source_file=entry.source.file,
                source_commit=entry.source.commit,
                original_topic=entry.original_topic,
                provenance_reviewed=False,
            )
            .on_conflict_do_nothing(index_elements=[QuestionVersion.id])
        )
        version = await session.get(QuestionVersion, version_id)
        if (
            version is None
            or version.question_id != entry.id
            or version.source_commit != entry.source.commit
        ):
            raise ValueError("Conflicting seed content provenance")
        link_id = seed_id(f"question-skill/{entry.id}")
        if await session.get(QuestionSkill, link_id) is None:
            await session.execute(
                insert(QuestionSkill)
                .values(
                    id=link_id,
                    question_version_id=version_id,
                    skill_id=seed_id(f"skill/{entry.topic_id}"),
                )
                .on_conflict_do_nothing(index_elements=[QuestionSkill.id])
            )
    return SeedSummary(questions=len(manifest.questions), skills=len(names))


async def run_seed(path: Path) -> None:
    settings = get_settings()
    if settings.app_env == "production":
        raise ValueError("Development seed command is disabled in production")
    Base.registry.configure()
    engine = create_engine(settings)
    try:
        async with async_sessionmaker(engine)() as session, session.begin():
            summary = await load_legacy_seed(session, path)
        print(json.dumps(summary.model_dump(), sort_keys=True))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load 15 legacy question-title drafts")
    parser.add_argument("--manifest", type=Path, default=ROOT / "content" / "legacy-v1.json")
    args = parser.parse_args()
    asyncio.run(run_seed(args.manifest))


if __name__ == "__main__":
    main()
