from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from interview_prep.modules.questions.models import Difficulty, QuestionType

AssessmentType = Literal["multiple_choice", "multiple_select", "short_answer", "written"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Configuration(Contract):
    category: str | None = Field(default=None, min_length=1, max_length=100)
    difficulty: Difficulty | None = None
    question_types: list[AssessmentType] = Field(min_length=1, max_length=4)
    question_count: int = Field(ge=1, le=12, strict=True)

    @model_validator(mode="after")
    def unique_types(self) -> "Configuration":
        if len(set(self.question_types)) != len(self.question_types):
            raise ValueError("Repeated question type")
        return self


class StartInput(Configuration):
    submission_key: UUID


class RevisionInput(Contract):
    revision: int = Field(ge=1, strict=True)


class ResponseInput(RevisionInput):
    answer_text: str | None = Field(default=None, max_length=10000)
    selected_option_ids: list[UUID] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def unique_options(self) -> "ResponseInput":
        if len(set(self.selected_option_ids)) != len(self.selected_option_ids):
            raise ValueError("Repeated selection")
        return self


class Inventory(Contract):
    category: str
    difficulty: Difficulty
    question_type: QuestionType
    count: int


class Options(Contract):
    inventory: list[Inventory]
    max_questions: int = 12
    duration_hours: int = 24
    conceptual_provider: str = "MockAIProvider"
    conceptual_kind: Literal["simulation", "model_assisted"] = "simulation"


class EvaluationMetadata(Contract):
    provider: str = Field(min_length=1, max_length=100)
    provider_version: str = Field(min_length=1, max_length=100)
    policy_version: str = Field(min_length=1, max_length=100)
    rubric_version: str | None = Field(default=None, max_length=100)
    evaluated_at: datetime
    matched_concepts: list[str] = Field(default_factory=list, max_length=12)


class Review(Contract):
    score: int | None
    max_score: int | None
    is_correct: bool | None
    result_kind: str | None
    feedback: str | None
    metadata: EvaluationMetadata | None
    expected_concepts: list[str]
    correct_option_ids: list[UUID]
    accepted_answers: list[str]


class PresentedOption(Contract):
    id: UUID
    text: str


class PresentedQuestion(Contract):
    id: UUID
    question_version_id: UUID
    position: int
    title: str
    prompt: str
    category: str
    difficulty: Difficulty | None
    question_type: QuestionType
    options: list[PresentedOption]
    answer_text: str | None
    selected_option_ids: list[UUID]
    saved_at: datetime | None
    skipped: bool
    review: Review | None


class CategoryPerformance(Contract):
    category: str
    questions: int
    answered: int
    skipped: int
    objective_correct: int
    objective_total: int
    conceptual_score: int
    conceptual_max: int
    conceptual_kind: str | None


class AttemptSummary(Contract):
    id: UUID
    title: str
    status: Literal["in_progress", "completed", "abandoned", "expired"]
    revision: int
    started_at: datetime
    completed_at: datetime | None
    deadline_at: datetime | None
    question_count: int
    answered: int
    simulated: bool


class AttemptView(AttemptSummary):
    configuration: Configuration | None
    questions: list[PresentedQuestion]
    categories: list[CategoryPerformance]


class AttemptPage(Contract):
    items: list[AttemptSummary]
    total: int
    offset: int
    limit: int
