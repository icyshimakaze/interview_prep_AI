"""Bounded artifact credential checks without printing matched bytes."""

import re
from collections.abc import Sequence

CLERK_KEY = re.compile(rb"\bsk_(?:live|test)_[A-Za-z0-9_+/=-]{16,}")
DATABASE_CREDENTIAL = re.compile(rb"postgres(?:ql)?(?:\+asyncpg)?://[^\s\"<>/:]+:[^\s\"<>@]+@")


def contains_server_credential(payload: bytes, secrets: Sequence[bytes]) -> bool:
    # SDK source contains bare key prefixes; those are not secret key values.
    # Keep exact generated-secret checks and require a plausible key suffix.
    return (
        any(secret in payload for secret in secrets if secret)
        or CLERK_KEY.search(payload) is not None
        or DATABASE_CREDENTIAL.search(payload) is not None
    )
