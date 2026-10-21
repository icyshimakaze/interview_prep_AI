from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

VERSION = "personal-roadmap-v1"
Priority = Literal["high", "medium", "low"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Recommendation(Contract):
    key: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=300)
    reason: str = Field(min_length=1, max_length=2000)
    priority: Priority
    objective: str = Field(min_length=1, max_length=1000)
    activity: str = Field(min_length=1, max_length=1000)
    source_ids: list[str] = Field(default_factory=list, max_length=12)


class GenerateRoadmap(Contract):
    command_key: UUID
    expected_id: UUID | None = None
    expected_revision: int | None = Field(default=None, ge=1, strict=True)
    target_id: UUID | None = None
    weekly_minutes: int = Field(ge=15, le=10080, strict=True)
    interview_date: date | None = None


class ChangeItem(Contract):
    revision: int = Field(ge=1, strict=True)
    action: Literal["complete", "reopen"]


class PlanItem(Contract):
    id: UUID
    topic: str
    reason: str
    priority: Priority | None
    objective: str | None
    activity: str | None
    estimated_minutes: int
    scheduled_on: date | None
    status: str
    completed_at: datetime | None


class PlanView(Contract):
    id: UUID
    revision: int
    title: str
    status: str
    policy_version: str
    created_at: datetime
    weekly_minutes: int
    interview_date: date | None
    starts_on: date
    target_id: UUID | None
    target_priority: str | None
    notices: list[str]
    items: list[PlanItem]


class PlanTarget(Contract):
    id: UUID
    title: str
    priority: str


class RoadmapWorkspace(Contract):
    mode: Literal["account", "demo"]
    current: PlanView | None
    history: list[PlanView]
    targets: list[PlanTarget]
    weekly_minutes: int
    interview_date: date | None
    notices: list[str]
