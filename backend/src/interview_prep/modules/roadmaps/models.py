from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import OwnedRecord, enum_column, owned_args, owned_fk
from interview_prep.modules.interviews.models import EvaluationKind


class RoadmapStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ProgressEventType(StrEnum):
    ASSESSMENT_COMPLETED = "assessment_completed"
    INTERVIEW_COMPLETED = "interview_completed"
    ROADMAP_ITEM_COMPLETED = "roadmap_item_completed"


class Roadmap(OwnedRecord):
    __tablename__ = "roadmaps"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("target_job_version_id", "job_target_versions", cascade=False),
        CheckConstraint("weekly_minutes BETWEEN 15 AND 10080", name="study_budget"),
        CheckConstraint("revision > 0", name="revision"),
        Index("ix_roadmaps_owner_status", "owner_id", "status"),
    )
    target_job_version_id: Mapped[UUID | None] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[RoadmapStatus] = mapped_column(enum_column(RoadmapStatus, "roadmap_status"))
    policy_version: Mapped[str] = mapped_column(String(100))
    context_version: Mapped[str] = mapped_column(String(100))
    weekly_minutes: Mapped[int] = mapped_column(Integer)
    timezone: Mapped[str] = mapped_column(String(100))
    starts_on: Mapped[date] = mapped_column(Date)
    target_date: Mapped[date | None] = mapped_column(Date)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    items: Mapped[list["RoadmapItem"]] = relationship(viewonly=True, lazy="raise")


class RoadmapItem(OwnedRecord):
    __tablename__ = "roadmap_items"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("roadmap_id", "roadmaps"),
        UniqueConstraint("roadmap_id", "position"),
        CheckConstraint("position > 0 AND estimated_minutes BETWEEN 1 AND 10080", name="effort"),
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)", name="completed_timestamp"
        ),
        CheckConstraint(
            "resource_url IS NULL OR resource_url LIKE 'https://%'", name="resource_https"
        ),
        Index("ix_roadmap_items_owner_due", "owner_id", "status", "scheduled_on"),
    )
    roadmap_id: Mapped[UUID] = mapped_column(index=True)
    skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    resource_url: Mapped[str | None] = mapped_column(String(2000))
    resource_review_version: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    scheduled_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[TaskStatus] = mapped_column(enum_column(TaskStatus, "roadmap_item_status"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProgressEvent(OwnedRecord):
    "Append-only facts with real relational origins, never synthetic metrics."

    __tablename__ = "progress_events"
    __table_args__ = owned_args(
        __tablename__,
        owned_fk("assessment_attempt_id", "assessment_attempts"),
        owned_fk("interview_session_id", "interview_sessions"),
        owned_fk("roadmap_item_id", "roadmap_items"),
        UniqueConstraint("owner_id", "deduplication_key"),
        CheckConstraint(
            "(event_type = 'assessment_completed' AND assessment_attempt_id IS NOT NULL "
            "AND interview_session_id IS NULL AND roadmap_item_id IS NULL) OR "
            "(event_type = 'interview_completed' AND interview_session_id IS NOT NULL "
            "AND assessment_attempt_id IS NULL AND roadmap_item_id IS NULL) OR "
            "(event_type = 'roadmap_item_completed' AND roadmap_item_id IS NOT NULL "
            "AND assessment_attempt_id IS NULL AND interview_session_id IS NULL)",
            name="event_origin",
        ),
        CheckConstraint(
            "details IS NULL OR (jsonb_typeof(details) = 'object' "
            "AND octet_length(details::text) <= 8192)",
            name="bounded_details",
        ),
        Index("ix_progress_events_owner_occurred", "owner_id", "occurred_at"),
    )
    event_type: Mapped[ProgressEventType] = mapped_column(
        enum_column(ProgressEventType, "progress_event_type")
    )
    result_kind: Mapped[EvaluationKind | None] = mapped_column(
        enum_column(EvaluationKind, "progress_result_kind")
    )
    assessment_attempt_id: Mapped[UUID | None] = mapped_column(index=True)
    interview_session_id: Mapped[UUID | None] = mapped_column(index=True)
    roadmap_item_id: Mapped[UUID | None] = mapped_column(index=True)
    deduplication_key: Mapped[UUID] = mapped_column()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    details: Mapped[dict[str, object] | None] = mapped_column(JSONB)
