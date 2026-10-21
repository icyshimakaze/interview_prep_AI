from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Accuracy(Contract):
    correct: int
    graded: int
    percent: float | None


class AssessmentPoint(Accuracy):
    id: str
    at: datetime
    excluded: int
    grading_versions: list[str]


class CategoryPerformance(Accuracy):
    category: str


class RatingPoint(Contract):
    session_id: str
    at: datetime
    mean: float
    answers: int


class RatingSeries(Contract):
    key: str
    label: str
    kind: str
    provider: str
    model: str | None
    provider_version: str
    rubric_version: str
    profile: str
    assessed_dimensions: list[str]
    chart_available: bool
    points: list[RatingPoint]


class MissedConcept(Contract):
    concept: str
    basis: Literal["deterministic", "model_assisted"]
    occurrences: int
    sessions: int
    last_seen: datetime


class Activity(Contract):
    id: str
    channel: Literal["assessment", "interview", "project_defense"]
    title: str
    status: str
    at: datetime


class EvidenceSummary(Contract):
    topic: str
    description: str
    source_count: int


class Completion(Contract):
    current_total: int = 0
    current_completed: int = 0
    historical_items: int = 0
    historical_completed: int = 0
    completion_events: int = 0


class ProgressAnalytics(Contract):
    policy_version: Literal["progress-analytics-v1"] = "progress-analytics-v1"
    mode: Literal["account", "demo"]
    generated_at: datetime
    assessment_chart_available: bool
    assessments: list[AssessmentPoint]
    categories: list[CategoryPerformance]
    interview_series: list[RatingSeries]
    excluded_interview_evaluations: int
    frequently_missed: list[MissedConcept]
    roadmap: Completion
    recent_sessions: list[Activity]
    validated_strengths: list[EvidenceSummary]
    requires_validation: list[EvidenceSummary]
    notices: list[str]
