from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

VERSION = "project-static-v1"
Short = Annotated[str, StringConstraints(min_length=1, max_length=500, pattern=r"\S")]
FactKind = Literal[
    "manifest",
    "dependency",
    "framework",
    "database",
    "route",
    "schema",
    "tests",
    "ci",
    "docker",
    "documentation",
    "component",
    "authentication",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class FileFact(Contract):
    path: Short
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_count: int = Field(ge=0, le=262144)
    line_count: int = Field(ge=1, le=262145)
    language: str | None = Field(max_length=50)


class StaticFact(Contract):
    path: Short
    kind: FactKind
    description: Short
    line: int = Field(ge=1, le=262145)
    inferred: bool


class AnalysisSummary(Contract):
    version: Literal["project-static-v1"] = "project-static-v1"
    languages: dict[str, int] = Field(max_length=30)
    skipped_files: int = Field(ge=0, le=3000)
    truncated: bool
    notes: list[Short] = Field(max_length=10)


class StaticAnalysis(Contract):
    summary: AnalysisSummary
    files: list[FileFact] = Field(max_length=500)
    facts: list[StaticFact] = Field(max_length=600)


class GithubInput(Contract):
    url: str = Field(min_length=1, max_length=250)


class ProjectSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    analysis_id: UUID
    name: str
    origin: str
    github_url: str | None
    commit_sha: str | None
    created_at: datetime
    analysis_version: str
    example: bool


class DefensePrompt(BaseModel):
    id: UUID
    focus: str
    prompt: str
    path: str
    line: int
    evidence: str
    inferred: bool


class ProjectDetail(ProjectSummary):
    summary: AnalysisSummary
    files: list[FileFact]
    facts: list[StaticFact]
    questions: list[DefensePrompt]


class ProjectList(BaseModel):
    items: list[ProjectSummary]


class StartDefense(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command_key: UUID
    question_count: int = Field(default=8, ge=1, le=10, strict=True)


class DefenseCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, strict=True)
    action: Literal["save", "submit", "skip", "pause", "resume", "end"]
    answer_text: str | None = Field(default=None, max_length=10000)


class DefenseResponse(BaseModel):
    question: DefensePrompt
    position: int
    answer_text: str | None
    status: Literal["draft", "submitted", "skipped"]
    submitted_at: datetime | None


class DefenseView(BaseModel):
    id: UUID
    project_id: UUID
    revision: int
    status: Literal["active", "paused", "completed"]
    current_position: int
    created_at: datetime
    completed_at: datetime | None
    responses: list[DefenseResponse]


class DefenseHistory(BaseModel):
    items: list[DefenseView]
