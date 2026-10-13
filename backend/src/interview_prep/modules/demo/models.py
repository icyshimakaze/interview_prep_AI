from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from interview_prep.db.base import Base


class DemoWorkspace(Base):
    __tablename__ = "demo_workspaces"
    __table_args__ = (CheckConstraint("expires_at > created_at", name="valid_expiry"),)

    id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True, default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DemoSession(Base):
    __tablename__ = "demo_sessions"
    __table_args__ = (
        CheckConstraint("length(token_hash) = 64", name="token_hash_length"),
        CheckConstraint("length(csrf_hash) = 64", name="csrf_hash_length"),
    )

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("demo_workspaces.id", ondelete="CASCADE"), unique=True
    )


class DemoCreationLimit(Base):
    __tablename__ = "demo_creation_limits"
    __table_args__ = (CheckConstraint("count BETWEEN 1 AND 2", name="creation_quota"),)

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
