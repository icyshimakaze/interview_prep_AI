from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from interview_prep.db.base import Base


class OperationQuota(Base):
    __tablename__ = "operation_quotas"
    __table_args__ = (CheckConstraint("count > 0", name="positive_count"),)

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class EvaluationReceipt(Base):
    __tablename__ = "assessment_evaluation_receipts"
    __table_args__ = (
        CheckConstraint("attempts BETWEEN 1 AND 2", name="attempt_limit"),
        CheckConstraint("state IN ('started', 'failed', 'completed')", name="state"),
        CheckConstraint("(state = 'completed') = (result IS NOT NULL)", name="completed_result"),
        CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 20000", name="result_size"
        ),
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True
    )
    input_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(12))
    result: Mapped[dict[str, object] | None] = mapped_column(JSONB(none_as_null=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
