from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from interview_prep.modules.questions.models import Difficulty
from interview_prep.modules.skills.schemas import Importance


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Candidate(Contract):
    question_id: UUID
    version_id: UUID
    topic: str = Field(min_length=1, max_length=100)
    concept: str = Field(min_length=1, max_length=200)
    skills: tuple[str, ...] = Field(max_length=100)
    difficulty: Difficulty


class SkillContext(Contract):
    key: str = Field(min_length=1, max_length=100)
    importance: Importance = "Low relevance"
    need: Literal["practice", "unknown", "maintain"] = "unknown"


class Performance(Contract):
    id: str = Field(min_length=1, max_length=150)
    skill: str = Field(min_length=1, max_length=100)
    concept: str = Field(min_length=1, max_length=200)
    difficulty: Difficulty
    outcome: Literal["met", "practice"]
    occurred_at: AwareDatetime
    channel: Literal["assessment", "interview"]
    eligible: bool = False


class Exposure(Contract):
    question_id: UUID
    topic: str = Field(min_length=1, max_length=100)
    concept: str = Field(min_length=1, max_length=200)


class SelectionInput(Contract):
    candidates: tuple[Candidate, ...] = Field(max_length=1000)
    skills: tuple[SkillContext, ...] = Field(default=(), max_length=1000)
    performance: tuple[Performance, ...] = Field(default=(), max_length=2000)
    # Oldest to newest; includes allocations/skips, not just successful answers.
    history: tuple[Exposure, ...] = Field(default=(), max_length=1000)
    history_count: int | None = Field(default=None, ge=0, strict=True)
    count: int = Field(default=1, ge=1, le=12, strict=True)
    seed: str = Field(default="adaptive-v1", min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_inputs(self) -> "SelectionInput":
        if self.history_count is not None and self.history_count < len(self.history):
            raise ValueError("History count cannot be smaller than the supplied window")
        for ids in (
            [c.question_id for c in self.candidates],
            [s.key for s in self.skills],
            [p.id for p in self.performance],
        ):
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate adaptive input identity")
        return self


class Choice(Contract):
    question_id: UUID
    version_id: UUID
    topic: str
    skill: str | None
    difficulty: Difficulty
    target_difficulty: Difficulty
    score: float
    components: dict[str, float]
    reasons: tuple[str, ...]


class Selection(Contract):
    policy_version: Literal["adaptive-v1"] = "adaptive-v1"
    choices: tuple[Choice, ...]
    notices: tuple[str, ...] = ()
