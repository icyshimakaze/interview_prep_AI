"""Owned durable commands, frozen candidates, generated content and work."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from interview_prep.db.model_support import OwnedRecord, history_fk, owned_args, owned_fk


class InterviewCandidate(OwnedRecord):
    __tablename__ = "interview_candidates"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("session_id", "interview_sessions"),
        UniqueConstraint("session_id", "question_id"),
        UniqueConstraint("session_id", "question_version_id"),
    )
    session_id: Mapped[UUID] = mapped_column(index=True)
    question_id: Mapped[UUID] = mapped_column(history_fk("questions.id"))
    question_version_id: Mapped[UUID] = mapped_column(history_fk("question_versions.id"))


class FollowupContent(OwnedRecord):
    __tablename__ = "interview_followup_contents"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("session_id", "interview_sessions"),
        owned_fk("parent_id", "interview_questions", cascade=False),
        UniqueConstraint("parent_id"),
        CheckConstraint("length(prompt) BETWEEN 1 AND 4000", name="prompt_length"),
    )
    session_id: Mapped[UUID] = mapped_column(index=True)
    parent_id: Mapped[UUID] = mapped_column()
    prompt: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(String(200))
    provenance: Mapped[dict[str, object]] = mapped_column(JSONB)


class InterviewCommand(OwnedRecord):
    __tablename__ = "interview_commands"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("session_id", "interview_sessions"),
        UniqueConstraint("owner_id", "command_key"),
    )
    session_id: Mapped[UUID] = mapped_column(index=True)
    command_key: Mapped[UUID] = mapped_column()
    digest: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(150))
    applied_revision: Mapped[int] = mapped_column(Integer)
    response_status: Mapped[int] = mapped_column(Integer)


class InterviewWork(OwnedRecord):
    __tablename__ = "interview_work"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("session_id", "interview_sessions"),
        owned_fk("turn_id", "interview_questions"),
        owned_fk("evaluation_id", "answer_evaluations", cascade=False),
        UniqueConstraint("session_id", "dedupe_key"),
        CheckConstraint("operation IN ('evaluate','followup')", name="operation"),
        CheckConstraint(
            "state IN ('pending','running','succeeded','failed','cancelled')", name="state"
        ),
    )
    session_id: Mapped[UUID] = mapped_column(index=True)
    turn_id: Mapped[UUID] = mapped_column(index=True)
    evaluation_id: Mapped[UUID | None] = mapped_column()
    operation: Mapped[str] = mapped_column(String(20))
    dedupe_key: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(20), default="pending")
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[UUID | None] = mapped_column()
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
