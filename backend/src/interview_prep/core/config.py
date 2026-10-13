from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", extra="ignore", hide_input_in_errors=True
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    demo_rate_limit_key: SecretStr = Field(min_length=32)
    demo_ttl_seconds: int = Field(default=86400, ge=60, le=86400)
    auth_enabled: bool = False
    auth_issuer: str | None = None
    auth_audience: str = "interview-prep-api"
    auth_jwks_cache_seconds: int = Field(default=300, ge=30, le=900)

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except Exception:
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
        if url.drivername != "postgresql+asyncpg" or not url.database:
            raise ValueError("DATABASE_URL must use postgresql+asyncpg and name a database")
        return value

    @field_validator("allowed_origins")
    @classmethod
    def exact_origins(cls, value: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        if not value:
            raise ValueError("At least one explicit origin is required")
        for origin in value:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or "*" in parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("Origins must be exact HTTP(S) origins without paths or wildcards")
        return value

    @model_validator(mode="after")
    def production_configuration(self) -> "Settings":
        if self.auth_enabled:
            from urllib.parse import urlsplit

            parsed = urlsplit(self.auth_issuer or "")
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.port not in {None, 443}
                or not self.auth_audience.strip()
            ):
                raise ValueError("Account mode requires a trusted HTTPS issuer origin and audience")
        if self.app_env == "production":
            if any(not origin.startswith("https://") for origin in self.allowed_origins):
                raise ValueError("Production requires HTTPS origins")
            if "replace-with" in self.demo_rate_limit_key.get_secret_value():
                raise ValueError("Production requires a random demo rate-limit key")
        return self

    @property
    def secure_cookies(self) -> bool:
        return self.app_env == "production"

    @property
    def auth_jwks_url(self) -> str:
        if not self.auth_enabled or not self.auth_issuer:
            raise ValueError("Account authentication is not configured")
        return self.auth_issuer + "/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
