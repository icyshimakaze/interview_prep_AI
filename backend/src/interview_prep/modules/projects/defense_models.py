from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from interview_prep.db.model_support import OwnedRecord, owned_args, owned_fk


class DefenseRun(OwnedRecord):
    __tablename__ = "project_defense_runs"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("analysis_id", "project_analyses"),
        UniqueConstraint("owner_id", "id", "analysis_id"),
        UniqueConstraint("owner_id", "command_key"),
        CheckConstraint("status IN ('active','paused','completed')", name="status"),
        CheckConstraint(
            "question_count BETWEEN 1 AND 10 AND current_position BETWEEN 1 AND question_count + 1",
            name="position",
        ),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("(status = 'completed') = (completed_at IS NOT NULL)", name="completion"),
    )
    analysis_id: Mapped[UUID] = mapped_column()
    command_key: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(String(20))
    question_count: Mapped[int] = mapped_column(Integer)
    current_position: Mapped[int] = mapped_column(Integer, default=1)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DefenseAnswer(OwnedRecord):
    __tablename__ = "project_defense_answers"
    __table_args__ = owned_args(
        __tablename__,
        ForeignKeyConstraint(
            ["owner_id", "run_id", "analysis_id"],
            [
                "project_defense_runs.owner_id",
                "project_defense_runs.id",
                "project_defense_runs.analysis_id",
            ],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["owner_id", "question_id", "analysis_id"],
            ["project_questions.owner_id", "project_questions.id", "project_questions.analysis_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("run_id", "position"),
        UniqueConstraint("run_id", "question_id"),
        CheckConstraint("position BETWEEN 1 AND 10", name="position"),
        CheckConstraint("status IN ('draft','submitted','skipped')", name="status"),
        CheckConstraint("(status <> 'draft') = (submitted_at IS NOT NULL)", name="submission"),
        CheckConstraint(
            "status <> 'submitted' OR (answer_text IS NOT NULL AND length(trim(answer_text)) > 0)",
            name="submitted_text",
        ),
        CheckConstraint("answer_text IS NULL OR length(answer_text) <= 10000", name="text_size"),
    )
    run_id: Mapped[UUID] = mapped_column()
    analysis_id: Mapped[UUID] = mapped_column()
    question_id: Mapped[UUID] = mapped_column()
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    answer_text: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
