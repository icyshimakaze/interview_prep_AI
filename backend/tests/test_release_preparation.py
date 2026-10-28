"""Read-only backup guards and exact production profile validation; no networking."""

import asyncio
from pathlib import Path

import backup_production_readonly as backup
import pytest
from backup_production_readonly import HOST, Source, validate_source
from interview_prep.core.config import Settings
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[2]


def test_missing_backup_connection_fails_before_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(backup, "SOURCE_FILE", tmp_path / "absent.local")
    with pytest.raises(SystemExit) as error:
        asyncio.run(backup.create_backup())
    assert error.value.code == 2


def test_backup_failure_diagnostics_never_echo_input() -> None:
    error = backup.BackupToolError(
        "pg_dump.exe", b"certificate verify failed: synthetic-sensitive-password"
    )
    assert error.tool == "pg_dump.exe"
    assert error.category == "certificate_verification_failed"
    assert "synthetic-sensitive-password" not in str(error)
    unknown = backup.BackupToolError("sensitive-command-argument", b"private-diagnostic")
    assert unknown.tool == "subprocess" and unknown.category == "unclassified"


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://owner:synthetic@127.0.0.1/neondb",
        f"postgresql://owner:synthetic@{HOST.replace('ep-square', 'ep-other')}/neondb",
        f"postgresql://owner:synthetic@{HOST.replace('.c-4', '-pooler.c-4')}/neondb",
        f"postgresql://owner:synthetic@{HOST}/another_database",
        f"postgresql://owner:synthetic@{HOST}:5440/neondb",
        f"postgresql://owner@{HOST}/neondb",
        f"postgresql://owner:synthetic@{HOST}/neondb?options=write",
        f"postgresql://owner:synthetic@{HOST}/neondb?sslmode=require&sslmode=disable",
        f"postgresql://owner:synthetic@{HOST}/neondb#fragment",
    ],
)
def test_backup_rejects_wrong_source_before_connecting(value: str) -> None:
    with pytest.raises(ValueError):
        validate_source(value)


def test_backup_accepts_only_exact_target_and_does_not_repr_password() -> None:
    source = validate_source(f"postgresql://backup:synthetic%21value@{HOST}/neondb")
    assert source.user == "backup"
    assert source.password == "synthetic!value"
    assert source.url().host == HOST
    assert source.url().database == "neondb"
    assert "synthetic" not in repr(source)
    assert "synthetic" not in repr(Source("backup", "synthetic"))


def test_backend_release_profile_matches_canonical_trust(monkeypatch: pytest.MonkeyPatch) -> None:
    values = dict(
        line.split("=", 1)
        for line in (ROOT / "deploy/backend.oauth.production.env.example").read_text().splitlines()
        if line and not line.startswith("#")
    )
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("BACKEND_PROXY_SECRET", "synthetic-gateway-secret-at-least-32-characters")
    settings = Settings.model_validate(
        {"demo_rate_limit_key": SecretStr("synthetic-demo-key-at-least-32-characters")}
    )
    assert settings.auth_enabled and settings.auth_provider == "better_auth"
    assert not settings.public_demo_only
    assert settings.auth_issuer == "https://interviewprepai.webredirect.org"
    assert str(settings.auth_jwks_endpoint) == settings.auth_issuer + "/api/auth/jwks"
    assert settings.allowed_origins == [settings.auth_issuer]
    assert settings.database_ssl_mode == "verify-full"
