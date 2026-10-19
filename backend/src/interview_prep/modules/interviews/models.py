from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import (
    OwnedRecord,
    enum_column,
    history_fk,
    owned_args,
    owned_fk,
)
from interview_prep.modules.assessments.models import AnswerStatus


class InterviewMode(StrEnum):
    MOCK_INTERVIEW = "mock_interview"
    PROJECT_DEFENSE = "project_defense"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class TurnStatus(StrEnum):
    AWAITING_ANSWER = "awaiting_answer"
    SUBMITTED = "submitted"
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
    EVALUATION_FAILED = "evaluation_failed"
    SKIPPED = "skipped"
    UNANSWERED = "unanswered"


class EvaluationKind(StrEnum):
    DETERMINISTIC = "deterministic"
    MODEL_ASSISTED = "model_assisted"
    SIMULATION = "simulation"
    SELF_REVIEW = "self_review"


class EvaluationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_EVALUABLE = "not_evaluable"


class InterviewSession(OwnedRecord):
    __tablename__ = "interview_sessions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("target_job_version_id", "job_target_versions", cascade=False),
        owned_fk("resume_version_id", "resume_versions", cascade=False),
        owned_fk("project_analysis_id", "project_analyses", cascade=False),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("main_question_limit BETWEEN 1 AND 10", name="question_limit"),
        CheckConstraint(
            "mode <> 'project_defense' OR project_analysis_id IS NOT NULL", name="project_context"
        ),
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)", name="completed_timestamp"
        ),
        Index("ix_interview_sessions_owner_status", "owner_id", "status", "created_at"),
        ForeignKeyConstraint(
            ["owner_id", "current_turn_id", "id"],
            [
                "interview_questions.owner_id",
                "interview_questions.id",
                "interview_questions.session_id",
            ],
            name="fk_interview_cursor",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "configuration IS NULL OR octet_length(configuration::text) <= 8192",
            name="configuration_size",
        ),
        CheckConstraint(
            "selection_context IS NULL OR octet_length(selection_context::text) <= 2097152",
            name="context_size",
        ),
    )
    mode: Mapped[InterviewMode] = mapped_column(enum_column(InterviewMode, "interview_mode"))
    status: Mapped[SessionStatus] = mapped_column(enum_column(SessionStatus, "interview_status"))
    target_job_version_id: Mapped[UUID | None] = mapped_column(index=True)
    resume_version_id: Mapped[UUID | None] = mapped_column(index=True)
    project_analysis_id: Mapped[UUID | None] = mapped_column(index=True)
    context_version: Mapped[str] = mapped_column(String(100))
    policy_version: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(200))
    main_question_limit: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_version: Mapped[str] = mapped_column(
        String(30), default="legacy", server_default="legacy"
    )
    configuration: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    selection_context: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    provider_descriptor: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    current_turn_id: Mapped[UUID | None] = mapped_column()
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_reason: Mapped[str | None] = mapped_column(String(40))
    finalization_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        viewonly=True,
        lazy="raise",
        foreign_keys="[InterviewQuestion.owner_id, InterviewQuestion.session_id]",
    )


class InterviewQuestion(OwnedRecord):
    __tablename__ = "interview_questions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("session_id", "interview_sessions"),
        owned_fk("project_question_id", "project_questions", cascade=False),
        UniqueConstraint("owner_id", "id", "session_id"),
        UniqueConstraint("session_id", "sequence"),
        UniqueConstraint("session_id", "question_version_id"),
        UniqueConstraint("parent_question_id"),
        ForeignKeyConstraint(
            ["owner_id", "parent_question_id", "session_id"],
            [
                "interview_questions.owner_id",
                "interview_questions.id",
                "interview_questions.session_id",
            ],
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("sequence > 0", name="sequence"),
        CheckConstraint(
            "parent_question_id IS NULL OR parent_question_id <> id", name="not_self_followup"
        ),
        CheckConstraint("source_kind IN ('bank','followup')", name="source_kind"),
        CheckConstraint(
            "(source_kind = 'bank' AND question_version_id IS NOT NULL "
            "AND followup_content_id IS NULL) OR (source_kind = 'followup' "
            "AND question_version_id IS NULL AND followup_content_id IS NOT NULL "
            "AND parent_question_id IS NOT NULL)",
            name="content_source",
        ),
        CheckConstraint("answering_ms >= 0", name="answering_time"),
        ForeignKeyConstraint(
            ["owner_id", "followup_content_id"],
            ["interview_followup_contents.owner_id", "interview_followup_contents.id"],
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index(
            "uq_interview_open_turn",
            "session_id",
            unique=True,
            postgresql_where=text("status = 'awaiting_answer' AND main_ordinal IS NOT NULL"),
        ),
        Index(
            "uq_interview_main_ordinal",
            "session_id",
            "main_ordinal",
            unique=True,
            postgresql_where=text("parent_question_id IS NULL"),
        ),
        UniqueConstraint("session_id", "stable_question_id"),
    )
    session_id: Mapped[UUID] = mapped_column(index=True)
    question_version_id: Mapped[UUID | None] = mapped_column(
        history_fk("question_versions.id"), index=True
    )
    project_question_id: Mapped[UUID | None] = mapped_column(index=True)
    parent_question_id: Mapped[UUID | None] = mapped_column()
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[TurnStatus] = mapped_column(enum_column(TurnStatus, "turn_status"))
    source_kind: Mapped[str] = mapped_column(String(20), default="bank", server_default="bank")
    followup_content_id: Mapped[UUID | None] = mapped_column()
    stable_question_id: Mapped[UUID | None] = mapped_column(history_fk("questions.id"))
    main_ordinal: Mapped[int | None] = mapped_column(Integer)
    presented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answering_ms: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    running_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    selection_trace: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    followup_decision: Mapped[str] = mapped_column(
        String(20), default="none", server_default="none"
    )
    answer: Mapped["InterviewAnswer | None"] = relationship(viewonly=True, lazy="raise")


class InterviewAnswer(OwnedRecord):
    __tablename__ = "interview_answers"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("interview_question_id", "interview_questions"),
        UniqueConstraint("interview_question_id"),
        UniqueConstraint("owner_id", "submission_key"),
        CheckConstraint(
            "(status = 'submitted') = (submitted_at IS NOT NULL)", name="submission_timestamp"
        ),
        CheckConstraint(
            "status <> 'submitted' OR answer_text IS NOT NULL", name="submitted_answer"
        ),
        CheckConstraint(
            "answer_text IS NULL OR length(answer_text) BETWEEN 1 AND 30000", name="answer_length"
        ),
        CheckConstraint("revision > 0", name="revision"),
    )
    interview_question_id: Mapped[UUID] = mapped_column(index=True)
    answer_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AnswerStatus] = mapped_column(
        enum_column(AnswerStatus, "interview_answer_status")
    )
    submission_key: Mapped[UUID | None] = mapped_column()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    evaluations: Mapped[list["AnswerEvaluation"]] = relationship(viewonly=True, lazy="raise")


class AnswerEvaluation(OwnedRecord):
    __tablename__ = "answer_evaluations"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("interview_answer_id", "interview_answers"),
        UniqueConstraint("owner_id", "id", "interview_answer_id"),
        UniqueConstraint("interview_answer_id", "version"),
        ForeignKeyConstraint(
            ["owner_id", "supersedes_id", "interview_answer_id"],
            [
                "answer_evaluations.owner_id",
                "answer_evaluations.id",
                "answer_evaluations.interview_answer_id",
            ],
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id", name="not_self_supersedes"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("status = 'completed' OR score IS NULL", name="score_availability"),
        CheckConstraint(
            "kind <> 'model_assisted' OR (provider IS NOT NULL AND model IS NOT NULL)",
            name="model_provenance",
        ),
        CheckConstraint(
            "input_digest IS NULL OR input_digest ~ '^[0-9a-f]{64}$'", name="input_digest"
        ),
        CheckConstraint(
            "usage_metadata IS NULL OR (jsonb_typeof(usage_metadata) = 'object' "
            "AND octet_length(usage_metadata::text) <= 8192)",
            name="bounded_usage",
        ),
        CheckConstraint(
            "score_scale_max IS NULL OR (score_scale_max = 4 AND (score IS "
            "NULL OR score BETWEEN 0 AND 4))",
            name="aggregate_scale",
        ),
        CheckConstraint(
            "result_payload IS NULL OR octet_length(result_payload::text) <= 16384",
            name="result_size",
        ),
    )
    interview_answer_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer)
    supersedes_id: Mapped[UUID | None] = mapped_column(index=True)
    kind: Mapped[EvaluationKind] = mapped_column(enum_column(EvaluationKind, "evaluation_kind"))
    status: Mapped[EvaluationStatus] = mapped_column(
        enum_column(EvaluationStatus, "evaluation_status")
    )
    evaluator_version: Mapped[str] = mapped_column(String(100))
    rubric_version: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(200))
    prompt_version: Mapped[str | None] = mapped_column(String(100))
    schema_version: Mapped[str | None] = mapped_column(String(100))
    input_digest: Mapped[str | None] = mapped_column(String(64))
    score: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    feedback: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(100))
    usage_metadata: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    score_scale_max: Mapped[int | None] = mapped_column(Integer)
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    dimensions: Mapped[list["EvaluationDimension"]] = relationship(viewonly=True, lazy="raise")


class EvaluationDimension(OwnedRecord):
    __tablename__ = "evaluation_dimensions"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("evaluation_id", "answer_evaluations"),
        UniqueConstraint("evaluation_id", "criterion_id"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 4", name="score_range"),
        CheckConstraint(
            ("(not_evaluable AND score IS NULL) OR (NOT not_evaluable AND score IS NOT NULL)"),
            name="evaluable_score",
        ),
        CheckConstraint(
            "(answer_start IS NULL AND answer_end IS NULL) OR (answer_start IS NOT NULL "
            "AND answer_end IS NOT NULL AND answer_start >= 0 AND answer_end > answer_start)",
            name="answer_span",
        ),
    )
    evaluation_id: Mapped[UUID] = mapped_column(index=True)
    criterion_id: Mapped[UUID] = mapped_column(
        history_fk("question_rubric_criteria.id"), index=True
    )
    score: Mapped[int | None] = mapped_column(Integer)
    not_evaluable: Mapped[bool] = mapped_column()
    feedback: Mapped[str] = mapped_column(String(4000))
    answer_start: Mapped[int | None] = mapped_column(Integer)
    answer_end: Mapped[int | None] = mapped_column(Integer)
