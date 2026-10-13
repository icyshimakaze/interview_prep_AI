import pytest
from pydantic import SecretStr, ValidationError

from interview_prep.core.config import Settings


@pytest.mark.parametrize(
    "issuer",
    [
        None,
        "http://insecure.example",
        "https://trusted.example/path",
        "https://user:password@trusted.example",
    ],
)
def test_account_mode_requires_explicit_trusted_issuer(issuer: str | None) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url=SecretStr("postgresql+asyncpg://x:x@localhost/x_test"),
            demo_rate_limit_key=SecretStr("x" * 32),
            auth_enabled=True,
            auth_issuer=issuer,
        )


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.test",
        "https://example.test/",
        "https://example.test/path",
        "https://user@host.test",
    ],
)
def test_rejects_unsafe_origins(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url=SecretStr("postgresql+asyncpg://test:test@localhost/unit_test"),
            demo_rate_limit_key=SecretStr("test-only-key-with-more-than-32-characters"),
            allowed_origins=[origin],
        )


def test_config_hides_secret_values_in_validation_errors() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            database_url=SecretStr("sqlite:///sensitive-password"),
            demo_rate_limit_key=SecretStr("test-only-key-with-more-than-32-characters"),
        )
    assert "sensitive-password" not in str(error.value)


def test_production_requires_https() -> None:
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url=SecretStr("postgresql+asyncpg://test:test@localhost/unit_test"),
            demo_rate_limit_key=SecretStr("test-only-key-with-more-than-32-characters"),
        )
