from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from interview_prep.ai.schemas import Operation

ROOT = Path(__file__).resolve().parents[4]
ENV_FILES = (ROOT / ".env", ROOT / "backend" / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES, extra="ignore", hide_input_in_errors=True, populate_by_name=True
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr
    database_ssl_mode: Literal["disable", "verify-full"] = "disable"
    database_ssl_ca_file: Path | None = None
    database_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    demo_rate_limit_key: SecretStr = Field(min_length=32)
    demo_ttl_seconds: int = Field(default=86400, ge=60, le=86400)
    auth_enabled: bool = False
    public_demo_only: bool = False
    backend_proxy_secret: SecretStr = Field(default_factory=lambda: SecretStr(""), exclude=True)
    auth_issuer: str | None = None
    auth_audience: str = "interview-prep-api"
    auth_jwks_cache_seconds: int = Field(default=300, ge=30, le=900)
    ai_provider: Literal["mock", "xkiro", "ollama", "openai"] = "mock"
    ai_timeout_seconds: float = Field(default=30, ge=0.1, le=60)
    ai_max_retries: int = Field(default=1, ge=0, le=2)
    ai_owner_hourly_calls: int = Field(default=60, ge=1, le=10000)
    ai_owner_daily_calls: int = Field(default=200, ge=1, le=100000)
    ai_global_daily_calls: int = Field(default=2000, ge=1, le=1000000)
    interview_worker_enabled: bool = True
    interview_poll_seconds: int = Field(default=1, ge=1, le=3600)
    cleanup_enabled: bool = False
    file_worker_slots: int = Field(default=2, ge=1, le=2)
    ollama_base_url: str = Field(default="", max_length=2000)
    ollama_model: str = Field(default="", max_length=100, pattern=r"^[^\r\n]*$")
    openai_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""), exclude=True)
    openai_model: str = Field(default="", max_length=100, pattern=r"^[^\r\n]*$")
    xkiro_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""), exclude=True)
    xkiro_base_url: Literal["https://api.xkiro.com/v1"] = "https://api.xkiro.com/v1"
    xkiro_reasoning_model: str = Field(
        default="qwen/qwen3.8-max:free",
        validation_alias=AliasChoices("XKIRO_MODEL_SMART", "XKIRO_REASONING_MODEL"),
    )
    xkiro_multimodal_model: str = Field(
        default="qwen/qwen3.8-omni-flash:free",
        validation_alias=AliasChoices("XKIRO_MODEL_MULTIMODAL", "XKIRO_MULTIMODAL_MODEL"),
    )
    xkiro_model_routes: dict[Operation, str] = Field(default_factory=dict)
    xkiro_allow_paid_models: bool = False

    @model_validator(mode="after")
    def xkiro_models(self) -> "Settings":
        import re

        models = [self.xkiro_reasoning_model, self.xkiro_multimodal_model]
        models.extend(self.xkiro_model_routes.values())
        for model in models:
            if len(model) > 100 or not re.fullmatch(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.:-]+", model):
                raise ValueError("xKiro models must be explicit vendor/model IDs")
            if not self.xkiro_allow_paid_models and not model.endswith(":free"):
                raise ValueError("Non-free xKiro models require XKIRO_ALLOW_PAID_MODELS=true")
        return self

    @field_validator("database_ssl_ca_file", mode="before")
    @classmethod
    def optional_ca_file(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("ollama_base_url")
    @classmethod
    def ollama_origin(cls, value: str) -> str:
        from urllib.parse import urlsplit

        value = value.strip().rstrip("/")
        if not value:
            return ""
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or any(c.isspace() for c in value)
        ):
            raise ValueError(
                "OLLAMA_BASE_URL must be an HTTP(S) origin without credentials or paths"
            )
        _ = parsed.port  # Reject malformed/out-of-range ports without echoing input.
        return value

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except Exception:
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
        if url.drivername != "postgresql+asyncpg" or not url.database:
            raise ValueError("DATABASE_URL must use postgresql+asyncpg and name a database")
        if any(key in url.query for key in ("sslmode", "ssl", "sslrootcert", "channel_binding")):
            raise ValueError("Use DATABASE_SSL_MODE/CA_FILE instead of database URL SSL parameters")
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
        proxy_secret = self.backend_proxy_secret.get_secret_value()
        if proxy_secret and not 32 <= len(proxy_secret) <= 256:
            raise ValueError("BACKEND_PROXY_SECRET must contain 32 to 256 characters")
        if self.public_demo_only and (self.ai_provider != "mock" or self.auth_enabled):
            raise ValueError("PUBLIC_DEMO_ONLY requires AI_PROVIDER=mock and AUTH_ENABLED=false")
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
            if self.database_ssl_mode != "verify-full":
                raise ValueError("Production requires DATABASE_SSL_MODE=verify-full")
            if not proxy_secret:
                raise ValueError("Production requires BACKEND_PROXY_SECRET")
            if "replace-with" in proxy_secret:
                raise ValueError("Production requires a generated BACKEND_PROXY_SECRET")
            url = make_url(self.database_url.get_secret_value())
            if not url.host or not url.username or not url.password:
                raise ValueError("Production DATABASE_URL requires host, role and password")
            if "URL_ENCODED_PASSWORD" in url.password:
                raise ValueError("Replace the production DATABASE_URL password placeholder")
            if not self.public_demo_only and not self.auth_enabled:
                raise ValueError("Production account profile requires AUTH_ENABLED=true")
            if self.ai_provider == "xkiro" and not self.xkiro_api_key.get_secret_value().strip():
                raise ValueError("Production xKiro requires XKIRO_API_KEY")
            if self.ai_provider == "openai" and (
                not self.openai_api_key.get_secret_value().strip() or not self.openai_model.strip()
            ):
                raise ValueError("Production OpenAI requires OPENAI_API_KEY and OPENAI_MODEL")
            if self.ai_provider == "ollama" and not self.ollama_model.strip():
                raise ValueError("Production Ollama requires OLLAMA_MODEL")
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
