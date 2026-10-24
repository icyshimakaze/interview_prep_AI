from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interview_prep.modules.context.models import EvidenceCategory, EvidenceOrigin, ReviewStatus


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    category: EvidenceCategory
    claim: str = Field(min_length=1, max_length=2000)
    review_status: ReviewStatus = ReviewStatus.CONFIRMED
    expected_revision: int = Field(ge=1, strict=True)

    @field_validator("claim")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        if any(ord(char) < 32 and char not in "\n\t" for char in value):
            raise ValueError("Unsupported control characters")
        return value


class EvidenceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: EvidenceCategory
    origin: EvidenceOrigin
    claim: str
    user_correction: str | None
    source_excerpt: str | None
    source_page: int | None
    source_start: int | None
    source_end: int | None
    review_status: ReviewStatus


class ResumeDetail(BaseModel):
    id: UUID
    label: str
    revision: int
    page_count: int | None
    extraction_note: str | None
    evidence: list[EvidenceView]
    is_sample: bool = False


class ResumeList(BaseModel):
    items: list[ResumeDetail]
