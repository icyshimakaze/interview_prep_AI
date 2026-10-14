"""Validate the small authored catalogue before opening a write transaction."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from interview_prep.modules.questions.models import Difficulty, QuestionType, SourceClassification
from interview_prep.seeding import LegacyManifest


class SeedOption(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=1000)
    is_correct: bool


class BankEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(pattern=r"^[a-z][a-z0-9-]{0,99}$")
    title: str = Field(min_length=1, max_length=300)
    legacy_title: str | None
    category: str = Field(min_length=1, max_length=100)
    subtopic: str = Field(min_length=1, max_length=100)
    difficulty: Difficulty
    question_type: QuestionType
    prompt: str = Field(min_length=40, max_length=10000)
    expected_concepts: list[str] = Field(min_length=1, max_length=12)
    tags: list[str] = Field(min_length=1, max_length=10)
    roles: list[str] = Field(min_length=1, max_length=10)
    source_classification: SourceClassification
    accepted_answers: list[str] = Field(max_length=10)
    options: list[SeedOption] = Field(max_length=6)

    @model_validator(mode="after")
    def validate_content(self) -> "BankEntry":
        for values, maximum in [(self.expected_concepts, 1000), (self.tags, 80), (self.roles, 80)]:
            if any(not value.strip() or len(value) > maximum for value in values):
                raise ValueError("Empty or excessive content label")
            if len(set(v.casefold() for v in values)) != len(values):
                raise ValueError("Duplicate content labels")
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if len(self.options) < 2 or sum(o.is_correct for o in self.options) != 1:
                raise ValueError("Single-choice content needs exactly one correct option")
        elif self.question_type == QuestionType.MULTIPLE_SELECT:
            if len(self.options) < 3 or not 2 <= sum(o.is_correct for o in self.options) < len(
                self.options
            ):
                raise ValueError(
                    "Multiple-select content needs at least two correct options and a distractor"
                )
        elif self.options:
            raise ValueError("Options are only allowed for multiple-choice content")
        if self.question_type == QuestionType.SHORT_ANSWER:
            if not self.accepted_answers or any(
                not a.strip() or len(a) > 2000 for a in self.accepted_answers
            ):
                raise ValueError("Short-answer content needs bounded answer keys")
        elif self.accepted_answers:
            raise ValueError("Answer keys are only allowed for short-answer content")
        expected = (
            SourceClassification.LEGACY_ADAPTED
            if self.legacy_title
            else SourceClassification.AUTHORED
        )
        if self.source_classification != expected:
            raise ValueError("Unexpected authored-content provenance")
        return self


class BankManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    content_version: Literal["question-bank-v1", "assessment-bank-v1"]
    questions: list[BankEntry] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def unique(self) -> "BankManifest":
        if len({q.key for q in self.questions}) != len(self.questions):
            raise ValueError("Duplicate content identity")
        if len({q.title for q in self.questions}) != len(self.questions):
            raise ValueError("Duplicate titles")
        return self


def read_manifest(path: Path, legacy_path: Path) -> tuple[BankManifest, LegacyManifest]:
    manifest = BankManifest.model_validate_json(path.read_text(encoding="utf-8"))
    legacy = LegacyManifest.model_validate_json(legacy_path.read_text(encoding="utf-8"))
    titles = [q.legacy_title for q in manifest.questions if q.legacy_title]
    if manifest.content_version == "question-bank-v1" and (
        len(titles) != 15 or set(titles) != {q.title for q in legacy.questions}
    ):
        raise ValueError("Authored adaptations must preserve every original title exactly once")
    if manifest.content_version == "assessment-bank-v1" and titles:
        raise ValueError("Supplemental assessment content must be newly authored")
    return manifest, legacy
