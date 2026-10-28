"""Recovery guard failures occur before Docker or any database connection."""

import pytest
from check_auth_recovery import owned_target


@pytest.mark.parametrize(
    "target,container",
    [
        (
            "postgresql+asyncpg://test:test@production.example/neondb",
            "interview-prep-auth-123456789abc",
        ),
        (
            "postgresql+asyncpg://test:test@127.0.0.1/existing_test",
            "interview-prep-auth-123456789abc",
        ),
        (
            "postgresql+asyncpg://test:test@127.0.0.1/interview_prep_123456789abc_test",
            "existing-container",
        ),
    ],
)
def test_recovery_rejects_unowned_or_remote_targets(
    monkeypatch: pytest.MonkeyPatch, target: str, container: str
) -> None:
    monkeypatch.setenv("TEST_DATABASE_URL", target)
    monkeypatch.setenv("AUTH_RECOVERY_TEST_CONTAINER", container)
    with pytest.raises(ValueError, match="owned loopback"):
        owned_target()
