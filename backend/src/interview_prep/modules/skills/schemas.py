from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from interview_prep.modules.questions.models import Difficulty

Importance = Literal["Required", "Preferred", "Mentioned", "Low relevance"]
ResumeState = Literal["Some evidence", "No resume evidence"]
CompetenceState = Literal[
    "Strong evidence",
    "Some evidence",
    "Needs assessment validation",
    "Validated by assessment",
    "Needs additional practice",
]
SourceKind = Literal["profile", "resume", "user", "job", "assessment", "interview"]


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: SourceKind
    detail: str
    review: str
    eligible: bool = False
    outcome: Literal["met", "practice"] | None = None
    concept: str | None = None
    occurred_at: datetime | None = None
    importance: Importance | None = None
    difficulty: Difficulty | None = None


class SkillFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    name: str
    source: EvidenceSource


class SkillRow(BaseModel):
    key: str
    name: str
    importance: Importance
    resume_state: ResumeState
    competence_state: CompetenceState
    assessment_validated: bool
    action: str
    explanation: list[str]
    sources: list[EvidenceSource]


class SkillTarget(BaseModel):
    id: UUID
    title: str


class SkillMatrix(BaseModel):
    policy_version: Literal["skill-evidence-v1"] = "skill-evidence-v1"
    mode: Literal["account", "demo"]
    target_id: UUID | None
    targets: list[SkillTarget]
    rows: list[SkillRow]
    notices: list[str] = Field(default_factory=list)
