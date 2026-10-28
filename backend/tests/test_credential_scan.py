import pytest
from credential_scan import contains_server_credential


@pytest.mark.parametrize(
    "payload,secrets,expected",
    [
        (b'apiKey.startsWith("sk_live_")', (), False),
        (b'"sk_test_" + runtimeValue', (), False),
        (b"sk_live_SYNTHETIC_not_a_real_key_0123456789", (), True),
        (b"sk_test_SYNTHETIC_not_a_real_key_0123456789", (), True),
        (b"postgresql://synthetic:secret@127.0.0.1/disposable_test", (), True),
        (b"postgresql+asyncpg://synthetic:secret@127.0.0.1/disposable_test", (), True),
        (b"a captured private marker", (b"private marker",), True),
        (b"ordinary browser source", (b"", b"absent marker"), False),
    ],
)
def test_artifact_scan_detects_values_without_confusing_sdk_prefix_constants(
    payload: bytes, secrets: tuple[bytes, ...], expected: bool
) -> None:
    assert contains_server_credential(payload, secrets) is expected
