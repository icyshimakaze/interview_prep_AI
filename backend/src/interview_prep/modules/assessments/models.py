from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import (
    OwnedRecord,
    enum_column,
    history_fk,
    owned_args,
    owned_fk,
)


class AssessmentStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AnswerStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    SKIPPED = "skipped"


class Assessment(OwnedRecord):
    __tablename__ = "assessments"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("target_job_version_id", "job_target_versions", cascade=False),
        owned_fk("resume_version_id", "resume_versions", cascade=False),
        CheckConstraint("revision > 0", name="revision"),
        Index("ix_assessments_owner_status", "owner_id", "status"),
    )
    title: Mapped[str] = mapped_column(String(200))
    target_job_version_id: Mapped[UUID | None] = mapped_column(index=True)
    resume_version_id: Mapped[UUID | None] = mapped_column(index=True)
    status: Mapped[AssessmentStatus] = mapped_column(
        enum_column(AssessmentStatus, "assessment_status")
    )
    context_version: Mapped[str] = mapped_column(String(100))
    policy_version: Mapped[str] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    questions: Mapped[list["AssessmentQuestion"]] = relationship(viewonly=True, lazy="raise")
    attempts: Mapped[list["AssessmentAttempt"]] = relationship(viewonly=True, lazy="raise")


class AssessmentQuestion(OwnedRecord):
    __tablename__ = "assessment_questions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("assessment_id", "assessments"),
        UniqueConstraint("owner_id", "id", "assessment_id"),
        UniqueConstraint("assessment_id", "position"),
        UniqueConstraint("assessment_id", "question_version_id"),
        CheckConstraint("position BETWEEN 1 AND 12", name="position"),
    )
    assessment_id: Mapped[UUID] = mapped_column(index=True)
    question_version_id: Mapped[UUID] = mapped_column(
        history_fk("question_versions.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    option_order_version: Mapped[str | None] = mapped_column(String(100))
    options: Mapped[list["AssessmentQuestionOption"]] = relationship(viewonly=True, lazy="raise")


class AssessmentQuestionOption(OwnedRecord):
    "Actual presented order, relationally tied to the selected content version."

    __tablename__ = "assessment_question_options"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("assessment_question_id", "assessment_questions"),
        ForeignKeyConstraint(
            ["question_version_id", "option_id"],
            ["question_options.question_version_id", "question_options.id"],
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint("assessment_question_id", "position"),
        UniqueConstraint("assessment_question_id", "option_id"),
        CheckConstraint("position > 0", name="position"),
    )
    assessment_question_id: Mapped[UUID] = mapped_column(index=True)
    question_version_id: Mapped[UUID] = mapped_column()
    option_id: Mapped[UUID] = mapped_column(index=True)
    position: Mapped[int] = mapped_column(Integer)


class AssessmentAttempt(OwnedRecord):
    __tablename__ = "assessment_attempts"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("assessment_id", "assessments"),
        UniqueConstraint("owner_id", "id", "assessment_id"),
        UniqueConstraint("owner_id", "assessment_id", "attempt_number"),
        UniqueConstraint("owner_id", "submission_key"),
        CheckConstraint("attempt_number > 0 AND revision > 0", name="positive_versions"),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at", name="completion_time"
        ),
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)", name="completed_timestamp"
        ),
        Index("ix_assessment_attempts_owner_status", "owner_id", "status", "started_at"),
    )
    assessment_id: Mapped[UUID] = mapped_column(index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    submission_key: Mapped[UUID] = mapped_column()
    status: Mapped[AttemptStatus] = mapped_column(enum_column(AttemptStatus, "attempt_status"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    answers: Mapped[list["QuestionAttempt"]] = relationship(viewonly=True, lazy="raise")


class QuestionAttempt(OwnedRecord):
    __tablename__ = "question_attempts"
    __table_args__ = owned_args(
        __tablename__,
        ForeignKeyConstraint(
            ["owner_id", "assessment_attempt_id", "assessment_id"],
            [
                "assessment_attempts.owner_id",
                "assessment_attempts.id",
                "assessment_attempts.assessment_id",
            ],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["owner_id", "assessment_question_id", "assessment_id"],
            [
                "assessment_questions.owner_id",
                "assessment_questions.id",
                "assessment_questions.assessment_id",
            ],
            ondelete="CASCADE",
        ),
        UniqueConstraint("assessment_attempt_id", "assessment_question_id"),
        UniqueConstraint("owner_id", "submission_key"),
        CheckConstraint(
            "(status = 'submitted') = (submitted_at IS NOT NULL)", name="submission_timestamp"
        ),
        CheckConstraint(
            ("status <> 'submitted' OR answer_text IS NOT NULL OR selected_option_id IS NOT NULL"),
            name="submitted_answer",
        ),
        CheckConstraint(
            "answer_text IS NULL OR length(answer_text) <= 30000", name="answer_length"
        ),
        CheckConstraint(
            (
                "result_kind IS NULL OR result_kind IN ('deterministic', 'simulati"
                "on', 'self_review')"
            ),
            name="result_kind",
        ),
        CheckConstraint(
            "is_correct IS NULL OR (status = 'submitted' AND result_kind IS NOT NULL "
            "AND grading_version IS NOT NULL)",
            name="grading_provenance",
        ),
        CheckConstraint("revision > 0", name="revision"),
    )
    assessment_id: Mapped[UUID] = mapped_column(index=True)
    assessment_attempt_id: Mapped[UUID] = mapped_column(index=True)
    assessment_question_id: Mapped[UUID] = mapped_column(index=True)
    status: Mapped[AnswerStatus] = mapped_column(
        enum_column(AnswerStatus, "question_attempt_status")
    )
    answer_text: Mapped[str | None] = mapped_column(Text)
    selected_option_id: Mapped[UUID | None] = mapped_column(
        history_fk("question_options.id"), index=True
    )
    submission_key: Mapped[UUID | None] = mapped_column()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_correct: Mapped[bool | None] = mapped_column()
    result_kind: Mapped[str | None] = mapped_column(String(20))
    grading_version: Mapped[str | None] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
