from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InterviewType(StrEnum):
    FUNDAMENTALS = "technical_fundamentals"
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULL_STACK = "full_stack"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    MIXED = "mixed"


class InterviewConfiguration(Contract):
    target_id: UUID | None = None
    interview_type: InterviewType = InterviewType.FUNDAMENTALS
    difficulty: Literal["auto", "easy", "medium", "hard"] = "auto"
    question_count: int = Field(default=5, ge=1, le=10, strict=True)

    @model_validator(mode="after")
    def full_stack_count(self) -> "InterviewConfiguration":
        if self.interview_type == InterviewType.FULL_STACK and self.question_count < 2:
            raise ValueError("Full Stack requires at least two main questions")
        return self


class CreateInterview(Contract):
    command_key: UUID
    configuration: InterviewConfiguration


class InterviewMutation(Contract):
    command_key: UUID
    revision: int = Field(ge=1, strict=True)


class ConfigureInterview(InterviewMutation):
    configuration: InterviewConfiguration


class InterviewText(InterviewMutation):
    answer_text: str | None = Field(max_length=10000)


class AdvanceInterview(InterviewMutation):
    from_turn_id: UUID
    next_kind: Literal["main", "followup"]


class InterviewDraft(Contract):
    turn_id: UUID
    answer_text: str | None = Field(max_length=10000)


class PauseInterview(InterviewMutation):
    draft: InterviewDraft | None


class EndInterview(PauseInterview):
    current_answer_action: Literal["keep_draft", "submit", "skip", "none"]


class RetryInterviewEvaluation(InterviewMutation):
    evaluation_id: UUID


class InterviewProvider(Contract):
    name: str
    version: str
    kind: str
    model: str | None
    disclosure: str


class InterviewInventory(Contract):
    interview_type: InterviewType
    label: str
    difficulty: str
    available_count: int
    max_questions: int
    min_questions: int


class InterviewOptions(Contract):
    inventory: list[InterviewInventory]
    provider: InterviewProvider
    targets: list["InterviewTarget"]
    max_followups: int = 3
    answer_limit: int = 10000
    notices: list[str]


class InterviewTarget(Contract):
    id: UUID
    title: str


class InterviewTurnView(Contract):
    id: UUID
    sequence: int
    main_ordinal: int | None
    parent_id: UUID | None
    kind: str
    prompt: str
    category: str
    difficulty: str | None
    status: str
    answer_text: str | None
    answer_revision: int
    answering_ms: int
    running_since: datetime | None
    context_excerpt: str | None
    evaluation_status: str | None
    evaluation_id: UUID | None = None
    evaluation_version: int | None = None


class InterviewProgress(Contract):
    requested: int
    presented: int
    resolved: int
    answered: int
    skipped: int
    followups_reserved: int
    followups_presented: int
    evaluation_pending: int
    evaluation_failed: int


class InterviewSessionView(Contract):
    id: UUID
    revision: int
    contract_version: str
    status: str
    phase: str | None
    configuration: InterviewConfiguration | None
    provider: InterviewProvider
    target_title: str | None
    started_at: datetime | None
    deadline_at: datetime | None
    ended_at: datetime | None
    completed_at: datetime | None
    end_reason: str | None
    expired: bool
    server_time: datetime
    current_turn: InterviewTurnView | None
    followup_decision: str
    progress: InterviewProgress
    allowed_actions: list[str]
    notices: list[str]


class InterviewReceipt(Contract):
    command_key: UUID
    operation: str
    session_id: UUID
    applied_revision: int


class InterviewCommandResponse(Contract):
    receipt: InterviewReceipt
    session: InterviewSessionView


class InterviewHistory(Contract):
    items: list[InterviewSessionView]
    total: int
    offset: int
    limit: int


class InterviewEvaluationView(Contract):
    id: UUID
    version: int
    status: str
    kind: str
    score: float | None
    score_scale_max: int | None
    feedback: str | None
    error_code: str | None
    provider: str | None
    model: str | None
    prompt_version: str | None


class InterviewReviewTurn(Contract):
    turn: InterviewTurnView
    expected_concepts: list[str]
    rubric: list[str]
    rationale: str | None
    evaluation: InterviewEvaluationView | None


class InterviewReview(Contract):
    session: InterviewSessionView
    review_status: Literal["provisional", "final"]
    evaluation_coverage: Literal["complete", "partial", "none"]
    submitted_main: int
    evaluated_main: int
    unasked_main: int
    turns: list[InterviewReviewTurn]
    notices: list[str]
