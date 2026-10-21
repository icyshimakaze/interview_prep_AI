"""Minimal owned metadata for analytics. No answer text is copied into the report."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResultFact:
    id: str
    session_id: str
    at: datetime
    channel: str
    category: str
    concept: str
    objective_correct: bool | None = None
    # Structured model feedback is kept separate from objective accuracy.
    payload: dict[str, object] | None = None
    kind: str = "ungraded"
    provider: str = ""
    model: str | None = None
    provider_version: str = ""
    rubric_version: str = ""
    completed: bool = False
    scale: int | None = None
    score: float | None = None
    grading_version: str = ""
