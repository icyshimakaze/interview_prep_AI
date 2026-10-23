"""Owned, bounded analysis receipts; source deletion cascades saved feedback."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from interview_prep.db.base import Base
from interview_prep.db.model_support import owned_fk


class AIAnalysis(Base):
    __tablename__ = "ai_analysis_receipts"
    __table_args__ = (
        owned_fk("resume_id", "resumes"),
        owned_fk("defense_answer_id", "project_defense_answers"),
        owned_fk("target_version_id", "job_target_versions"),
        owned_fk("roadmap_id", "roadmaps"),
        owned_fk("project_analysis_id", "project_analyses"),
        CheckConstraint(
            "num_nonnulls(resume_id, defense_answer_id, target_version_id, "
            "roadmap_id, project_analysis_id) = 1",
            name="one_source",
        ),
        CheckConstraint("attempts BETWEEN 1 AND 2", name="attempt_limit"),
        CheckConstraint("state IN ('started', 'failed', 'completed')", name="state"),
        CheckConstraint("(state = 'completed') = (result IS NOT NULL)", name="completed_result"),
        CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 131072", name="result_size"
        ),
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True
    )
    input_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    dispatch_token: Mapped[UUID] = mapped_column(default=uuid4)
    resume_id: Mapped[UUID | None] = mapped_column()
    defense_answer_id: Mapped[UUID | None] = mapped_column()
    target_version_id: Mapped[UUID | None] = mapped_column()
    roadmap_id: Mapped[UUID | None] = mapped_column()
    project_analysis_id: Mapped[UUID | None] = mapped_column()
    attempts: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(12))
    result: Mapped[dict[str, object] | None] = mapped_column(JSONB(none_as_null=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
