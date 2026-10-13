from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interview_prep.modules.context.models import TargetPriority, TargetStatus
from interview_prep.modules.identity.schemas import TargetView


class TargetInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    organization: str | None = Field(default=None, max_length=200)
    description: str = Field(min_length=1, max_length=30000)
    source_url: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=5000)
    priority: TargetPriority = TargetPriority.NORMAL
    status: TargetStatus = TargetStatus.SAVED

    @field_validator("organization", "source_url", "notes", mode="before")
    @classmethod
    def optional_text(cls, value: object) -> object:
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("source_url")
    @classmethod
    def safe_source_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(char.isspace() or ord(char) < 32 for char in value)
            or "\\" in value
        ):
            raise ValueError("Use an HTTP(S) URL without credentials")
        _ = parsed.port
        return value


class TargetUpdate(TargetInput):
    expected_revision: int = Field(ge=1, strict=True)


class TargetList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[TargetView]
    total: int
    offset: int
    limit: int
