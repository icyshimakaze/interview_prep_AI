from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    weekly_minutes: int = Field(ge=15, le=10080)
    expected_revision: int | None = Field(default=None, ge=1)


class ProfileView(StrictModel):
    display_name: str | None
    target_role: str
    experience_band: ExperienceBand
    timezone: str
    weekly_minutes: int
    revision: int


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
