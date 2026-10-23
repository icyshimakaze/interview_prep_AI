from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from interview_prep.core.config import Settings


def test_absolute_dotenv_paths_and_override_precedence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    backend = root / "backend"
    backend.mkdir(parents=True)
    (root / ".env").write_text(
        "DATABASE_URL=postgresql+asyncpg://test:test@localhost/unit_test\n"
        "DEMO_RATE_LIMIT_KEY=test-only-key-with-more-than-32-characters\n"
        "XKIRO_API_KEY=fictional-root-key\nAI_PROVIDER=mock\n",
        encoding="utf-8",
    )
    local = backend / ".env"
    local.write_text(
        "AI_PROVIDER=xkiro\nXKIRO_API_KEY=fictional-backend-key\n"
        "XKIRO_MODEL_SMART=qwen/custom-smart:free\n"
        "XKIRO_MODEL_MULTIMODAL=qwen/custom-omni:free\n",
        encoding="utf-8",
    )
    for name in (
        "DATABASE_URL",
        "DEMO_RATE_LIMIT_KEY",
        "AI_PROVIDER",
        "XKIRO_API_KEY",
        "XKIRO_MODEL_SMART",
        "XKIRO_MODEL_MULTIMODAL",
        "XKIRO_REASONING_MODEL",
        "XKIRO_MULTIMODAL_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", (root / ".env", local))
    monkeypatch.chdir(tmp_path)
    loaded = Settings()
    assert loaded.ai_provider == "xkiro"
    assert loaded.xkiro_api_key.get_secret_value() == "fictional-backend-key"
    assert loaded.xkiro_reasoning_model == "qwen/custom-smart:free"
    assert loaded.xkiro_multimodal_model == "qwen/custom-omni:free"
    # Production process variables override files, including a legacy model name.
    monkeypatch.setenv("XKIRO_API_KEY", "fictional-process-key")
    monkeypatch.setenv("XKIRO_REASONING_MODEL", "qwen/process-smart:free")
    loaded = Settings()
    assert loaded.xkiro_api_key.get_secret_value() == "fictional-process-key"
    assert loaded.xkiro_reasoning_model == "qwen/process-smart:free"
    assert "fictional-" not in loaded.model_dump_json() + repr(loaded)
    assert local.read_text(encoding="utf-8").startswith("AI_PROVIDER=xkiro\n")


def test_requested_model_names_and_legacy_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XKIRO_MODEL_SMART", "qwen/canonical:free")
    monkeypatch.setenv("XKIRO_MODEL_MULTIMODAL", "qwen/canonical-omni:free")
    configured = Settings(
        _env_file=None,
        database_url=SecretStr("postgresql+asyncpg://x:x@localhost/x_test"),
        demo_rate_limit_key=SecretStr("x" * 32),
    )
    assert configured.xkiro_reasoning_model == "qwen/canonical:free"
    assert configured.xkiro_multimodal_model == "qwen/canonical-omni:free"
    # Explicit Python configuration remains stronger than process defaults.
    configured = Settings(
        _env_file=None,
        database_url=SecretStr("postgresql+asyncpg://x:x@localhost/x_test"),
        demo_rate_limit_key=SecretStr("x" * 32),
        xkiro_reasoning_model="qwen/explicit:free",
    )
    assert configured.xkiro_reasoning_model == "qwen/explicit:free"


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
