from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interview_prep.modules.questions.models import Difficulty, QuestionType, SourceClassification


class BankFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    search: str = Field(default="", max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    subtopic: str | None = Field(default=None, min_length=1, max_length=100)
    difficulty: Difficulty | None = None
    question_type: QuestionType | None = None
    role: str | None = Field(default=None, min_length=1, max_length=80)
    bookmarked: bool | None = None
    attempted: bool | None = None
    active: bool = True
    offset: int = Field(default=0, ge=0, le=100000)
    limit: int = Field(default=12, ge=1, le=50)

    @field_validator("search", "category", "subtopic", "role")
    @classmethod
    def trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class BankQuestion(BaseModel):
    id: UUID
    version_id: UUID
    version: int
    title: str
    category: str
    subtopic: str
    difficulty: Difficulty
    question_type: QuestionType
    tags: list[str]
    roles: list[str]
    source_classification: SourceClassification
    active: bool
    bookmarked: bool
    attempted: bool


class BankPage(BaseModel):
    items: list[BankQuestion]
    total: int
    offset: int
    limit: int


class BankFacets(BaseModel):
    categories: list[str]
    subtopics: list[str]
    roles: list[str]


class BankOption(BaseModel):
    id: UUID
    text: str


class BankDetail(BankQuestion):
    prompt: str
    options: list[BankOption]
    concepts_unlocked: bool
    expected_concepts: list[str] | None
    source_file: str | None
    original_topic: str | None


class PracticeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_version_id: UUID
    submission_key: UUID
    answer_text: str = Field(min_length=1, max_length=10000, strict=True)

    @field_validator("answer_text")
    @classmethod
    def answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A response is required")
        return value


class PracticeView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    question_version_id: UUID
    answer_text: str
    submitted_at: datetime
    result_kind: Literal["self_review", "simulation"]


class AttemptHistoryItem(BaseModel):
    id: UUID
    question_version_id: UUID
    channel: Literal["question_bank", "assessment", "interview"]
    submitted_at: datetime
    result_kind: str | None
    response: str | None


class AttemptHistory(BaseModel):
    items: list[AttemptHistoryItem]
    total: int
    offset: int
    limit: int


class BookmarkState(BaseModel):
    bookmarked: bool
