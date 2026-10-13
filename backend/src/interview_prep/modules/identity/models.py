from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import OwnedRecord, Record, enum_column, owned_args


class PrincipalKind(StrEnum):
    ACCOUNT = "account"
    DEMO = "demo"


class PrincipalStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETING = "deleting"


class ExperienceBand(StrEnum):
    STUDENT = "student"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"


class User(Record):
    """Local principal, never a password store or an email-based identity."""

    __tablename__ = "principals"
    __table_args__ = (
        UniqueConstraint("issuer", "subject"),
        CheckConstraint(
            "(kind = 'account' AND issuer IS NOT NULL AND subject IS NOT NULL "
            "AND expires_at IS NULL) OR (kind = 'demo' AND issuer IS NULL "
            "AND subject IS NULL AND expires_at IS NOT NULL AND expires_at > created_at)",
            name="identity_kind",
        ),
        CheckConstraint("deletion_generation >= 0", name="deletion_generation"),
        CheckConstraint("updated_at >= created_at", name="timestamp_order"),
    )

    kind: Mapped[PrincipalKind] = mapped_column(enum_column(PrincipalKind, "principal_kind"))
    status: Mapped[PrincipalStatus] = mapped_column(
        enum_column(PrincipalStatus, "principal_status"),
        default=PrincipalStatus.ACTIVE,
        server_default="active",
    )
    issuer: Mapped[str | None] = mapped_column(String(500))
    subject: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deletion_generation: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    profile: Mapped["Profile | None"] = relationship(viewonly=True, lazy="raise")


class Profile(OwnedRecord):
    __tablename__ = "candidate_profiles"
    __table_args__ = owned_args(
        __tablename__,
        UniqueConstraint("owner_id"),
        CheckConstraint("weekly_minutes BETWEEN 15 AND 10080", name="study_budget"),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("length(trim(target_role)) > 0", name="target_role"),
        CheckConstraint("length(trim(timezone)) > 0", name="timezone"),
    )

    target_role: Mapped[str] = mapped_column(String(200))
    display_name: Mapped[str | None] = mapped_column(String(150))
    experience_band: Mapped[ExperienceBand] = mapped_column(
        enum_column(ExperienceBand, "experience_band")
    )
    timezone: Mapped[str] = mapped_column(String(100))
    weekly_minutes: Mapped[int] = mapped_column(Integer)
    target_date: Mapped[date | None] = mapped_column(Date)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
