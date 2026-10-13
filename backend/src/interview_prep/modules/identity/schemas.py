from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interview_prep.modules.context.models import TargetPriority, TargetStatus
from interview_prep.modules.identity.models import ExperienceBand


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EmptyRequest(StrictModel):
    pass


class ProfileInput(StrictModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1, max_length=150)
    target_role: str = Field(min_length=1, max_length=200)
    experience_band: ExperienceBand
    timezone: str = Field(min_length=1, max_length=100)
    weekly_minutes: int = Field(ge=15, le=10080, strict=True)
    expected_revision: int | None = Field(default=None, ge=1, strict=True)
    expected_id: UUID | None = None
    education: str | None = Field(default=None, max_length=300)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100, strict=True)
    interests: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(
        default_factory=list, max_length=20
    )
    interview_date: date | None = None

    @field_validator("interview_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> object:
        if value is not None:
            if not isinstance(value, (str, date)):
                raise ValueError("Use a calendar date")
            parsed = date.fromisoformat(value) if isinstance(value, str) else value
            if not 1900 <= parsed.year <= 2100:
                raise ValueError("Date is out of range")
        return value

    @field_validator("display_name", "education", mode="before")
    @classmethod
    def optional_text(cls, value: object) -> object:
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("interests")
    @classmethod
    def supplied_interests(cls, value: list[str]) -> list[str]:
        if len({label.casefold() for label in value}) != len(value):
            raise ValueError("Interests must be distinct")
        return value


class ProfileView(StrictModel):
    id: UUID
    display_name: str | None
    target_role: str
    experience_band: ExperienceBand
    timezone: str
    weekly_minutes: int
    revision: int
    education: str | None
    graduation_year: int | None
    interests: list[str]
    interview_date: date | None


class SessionView(StrictModel):
    mode: Literal["account"] = "account"


class ResumeView(StrictModel):
    id: UUID
    label: str
    evidence: list[str]


class TargetView(StrictModel):
    id: UUID
    title: str
    organization: str | None
    description: str | None
    source_url: str | None
    notes: str | None
    priority: TargetPriority
    status: TargetStatus
    revision: int


class AssessmentView(StrictModel):
    id: UUID
    title: str
    completed_at: datetime | None
    answered: int
    correct: int
    result_kind: str


class InterviewView(StrictModel):
    id: UUID
    completed_at: datetime | None
    status: str
    feedback: list[str]
    result_kind: str


class RoadmapItemView(StrictModel):
    id: UUID
    title: str
    status: str
    estimated_minutes: int


class ProgressView(StrictModel):
    event_type: str
    occurred_at: datetime
    result_kind: str | None


class DashboardView(StrictModel):
    mode: Literal["account", "demo"]
    data_label: str
    expires_at: datetime | None
    profile: ProfileView | None
    targets: list[TargetView]
    resumes: list[ResumeView]
    assessments: list[AssessmentView]
    interviews: list[InterviewView]
    roadmap_items: list[RoadmapItemView]
    progress: list[ProgressView]
