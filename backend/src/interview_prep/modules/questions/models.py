from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.db.model_support import OwnedRecord, Record, enum_column, owned_args


class QuestionVisibility(StrEnum):
    GLOBAL = "global"
    PRIVATE = "private"


class PublicationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    WRITTEN = "written"
    DESIGN = "design"
    BEHAVIORAL = "behavioral"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(Record):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "(visibility = 'global' AND owner_id IS NULL) OR "
            "(visibility = 'private' AND owner_id IS NOT NULL)",
            name="visibility_owner",
        ),
        UniqueConstraint("owner_id", "id"),
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), index=True
    )
    visibility: Mapped[QuestionVisibility] = mapped_column(
        enum_column(QuestionVisibility, "question_visibility")
    )
    canonical_concept: Mapped[str] = mapped_column(String(200), index=True)
    versions: Mapped[list["QuestionVersion"]] = relationship(viewonly=True, lazy="raise")


class QuestionVersion(Record):
    __tablename__ = "question_versions"
    __table_args__ = (
        UniqueConstraint("question_id", "version"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("length(trim(title)) > 0", name="title"),
        CheckConstraint(
            "prompt IS NULL OR length(prompt) BETWEEN 1 AND 30000", name="prompt_length"
        ),
        CheckConstraint(
            "status <> 'published' OR (prompt IS NOT NULL AND question_type IS NOT NULL "
            "AND difficulty IS NOT NULL AND provenance_reviewed AND source_license IS NOT NULL)",
            name="published_content",
        ),
    )
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    prompt: Mapped[str | None] = mapped_column(Text)
    question_type: Mapped[QuestionType | None] = mapped_column(
        enum_column(QuestionType, "question_type")
    )
    difficulty: Mapped[Difficulty | None] = mapped_column(
        enum_column(Difficulty, "question_difficulty")
    )
    status: Mapped[PublicationStatus] = mapped_column(
        enum_column(PublicationStatus, "publication_status"), index=True
    )
    language: Mapped[str] = mapped_column(String(20), default="en", server_default="en")
    source_file: Mapped[str | None] = mapped_column(String(500))
    source_commit: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(2000))
    source_license: Mapped[str | None] = mapped_column(String(200))
    original_topic: Mapped[str | None] = mapped_column(String(150))
    provenance_reviewed: Mapped[bool] = mapped_column(default=False, server_default="false")
    rubric_version: Mapped[str | None] = mapped_column(String(100))
    skills: Mapped[list["QuestionSkill"]] = relationship(viewonly=True, lazy="raise")
    options: Mapped[list["QuestionOption"]] = relationship(viewonly=True, lazy="raise")
    criteria: Mapped[list["QuestionRubricCriterion"]] = relationship(viewonly=True, lazy="raise")


class QuestionSkill(Record):
    __tablename__ = "question_skills"
    __table_args__ = (UniqueConstraint("question_version_id", "skill_id"),)
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), index=True)


class QuestionOption(Record):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_version_id", "position"),
        UniqueConstraint("question_version_id", "id"),
        CheckConstraint("position > 0", name="position"),
        CheckConstraint("length(trim(text)) > 0", name="option_text"),
    )
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(4000))
    is_correct: Mapped[bool] = mapped_column()


class ShortAnswerKey(Record):
    __tablename__ = "short_answer_keys"
    __table_args__ = (
        UniqueConstraint("question_version_id", "normalized_answer"),
        CheckConstraint("length(trim(normalized_answer)) > 0", name="answer_text"),
    )
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    normalized_answer: Mapped[str] = mapped_column(String(2000))
    normalization_version: Mapped[str] = mapped_column(String(100))


class QuestionRubricCriterion(Record):
    __tablename__ = "question_rubric_criteria"
    __table_args__ = (
        UniqueConstraint("question_version_id", "code"),
        UniqueConstraint("question_version_id", "id"),
        CheckConstraint("weight > 0 AND weight <= 1", name="weight"),
    )
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(2000))
    weight: Mapped[float] = mapped_column(Numeric(6, 5, asdecimal=False))
    anchor_0: Mapped[str] = mapped_column(String(2000))
    anchor_1: Mapped[str] = mapped_column(String(2000))
    anchor_2: Mapped[str] = mapped_column(String(2000))
    anchor_3: Mapped[str] = mapped_column(String(2000))
    anchor_4: Mapped[str] = mapped_column(String(2000))


class Bookmark(OwnedRecord):
    __tablename__ = "bookmarks"
    __table_args__ = owned_args(__tablename__, UniqueConstraint("owner_id", "question_version_id"))
    question_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_versions.id", ondelete="CASCADE"), index=True
    )
    note: Mapped[str | None] = mapped_column(String(2000))
