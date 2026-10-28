"""Manual live OAuth tooling must refuse ambient databases and malformed cohorts."""

import json
import subprocess
from pathlib import Path

import local_social
import pytest


@pytest.mark.parametrize(
    "target",
    [
        "postgresql+asyncpg://test:synthetic@remote.example.invalid/app_test",
        "postgresql+asyncpg://test:synthetic@127.0.0.1/app",
    ],
)
def test_manual_fixture_refuses_non_disposable_target(
    monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    monkeypatch.setenv("TEST_DATABASE_URL", target)
    with pytest.raises(ValueError, match="disposable"):
        local_social.main()


def test_credentials_are_selected_without_reusing_database_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend/.env.local").write_text(
        "GOOGLE_CLIENT_ID=synthetic-google\nGOOGLE_CLIENT_SECRET=synthetic-secret\n"
        "GITHUB_CLIENT_ID=synthetic-github\nGITHUB_CLIENT_SECRET=synthetic-secret\n"
        "AUTH_DATABASE_URL=never-reuse-ambient-database\n",
        encoding="utf-8",
    )
    (tmp_path / "cohort.json").write_text(
        json.dumps({"google": ["synthetic-sub"], "github": ["10001"]}), encoding="utf-8"
    )
    monkeypatch.setattr(local_social, "ROOT", tmp_path)
    monkeypatch.setattr(local_social, "CONTROL", tmp_path)
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0)
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: b"")
    result = local_social.local_credentials()
    assert "AUTH_DATABASE_URL" not in result
    assert result["GITHUB_ALLOWED_SUBJECTS"] == '["10001"]'
    (tmp_path / "cohort.json").write_text(
        json.dumps({"google": ["synthetic-sub"], "github": ["mutable-login"]}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="stable"):
        local_social.local_credentials()
