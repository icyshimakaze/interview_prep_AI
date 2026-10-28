"Verify an API-template JWT against operator-configured trust, never token URLs."

import asyncio
import time
from dataclasses import dataclass
from typing import cast

import httpx
import jwt
from jwt import PyJWK
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from interview_prep.core.config import Settings


class AuthenticationError(Exception):
    pass


class AuthenticationUnavailable(Exception):
    pass


class Claims(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    iss: str
    sub: str = Field(min_length=1, max_length=255)
    azp: str
    exp: int
    iat: int
    nbf: int
    sid: str | None = Field(default=None, min_length=1, max_length=255)


@dataclass(frozen=True)
class VerifiedIdentity:
    issuer: str
    subject: str
    session_id: str | None = None


class TokenVerifier:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.client = client
        self.keys: dict[str, PyJWK] = {}
        self.expires_at = 0.0
        self.last_unknown_refresh = -float("inf")
        self.last_failure = -float("inf")
        self.lock = asyncio.Lock()

    async def refresh(self) -> None:
        if time.monotonic() - self.last_failure < 5:
            raise AuthenticationUnavailable()
        try:
            async with (
                asyncio.timeout(3),
                self.client.stream(
                    "GET",
                    self.settings.auth_jwks_url,
                    headers={"Accept-Encoding": "identity"},
                    follow_redirects=False,
                    timeout=3,
                ) as response,
            ):
                response.raise_for_status()
                if response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise ValueError("Encoded JWKS unsupported")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > 65536:
                        raise ValueError("JWKS exceeds budget")
                    body.extend(chunk)
            import json

            payload: object = json.loads(body)
            if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
                raise ValueError("Invalid JWKS")
            raw_keys = payload["keys"]
            if not 1 <= len(raw_keys) <= 10:
                raise ValueError("Invalid JWKS key count")
            keys: dict[str, PyJWK] = {}
            for raw in raw_keys:
                if not isinstance(raw, dict):
                    raise ValueError("Invalid JWKS key")
                if (
                    raw.get("kty") != "RSA"
                    or raw.get("use", "sig") != "sig"
                    or raw.get("alg", "RS256") != "RS256"
                ):
                    continue
                kid = raw.get("kid")
                if (
                    not isinstance(kid, str)
                    or not 1 <= len(kid) <= 128
                    or kid in keys
                    or "d" in raw
                ):
                    raise ValueError("Invalid JWKS identity")
                key = PyJWK.from_dict(raw, algorithm="RS256")
                if cast(int, key.key.key_size) < 2048:
                    raise ValueError("Signing key too small")
                keys[kid] = key
            if not keys:
                raise ValueError("No permitted signing key")
            self.keys = keys
            self.expires_at = time.monotonic() + self.settings.auth_jwks_cache_seconds
        except (
            httpx.HTTPError,
            ValueError,
            TypeError,
            jwt.PyJWTError,
            TimeoutError,
            RecursionError,
        ):
            self.last_failure = time.monotonic()
            raise AuthenticationUnavailable() from None

    async def verify(self, token: str) -> VerifiedIdentity:
        if not self.settings.auth_enabled or not 1 <= len(token) <= 8192:
            raise AuthenticationError()
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if (
                header.get("alg") != "RS256"
                or header.get("typ", "JWT") != "JWT"
                or any(field in header for field in ("jku", "x5u", "jwk", "crit"))
                or not isinstance(kid, str)
                or not 1 <= len(kid) <= 128
            ):
                raise AuthenticationError()
            async with self.lock:
                refreshed = False
                if time.monotonic() >= self.expires_at:
                    await self.refresh()
                    refreshed = True
                if (
                    kid not in self.keys
                    and not refreshed
                    and time.monotonic() - self.last_unknown_refresh >= 30
                ):
                    self.last_unknown_refresh = time.monotonic()
                    await self.refresh()
                key = self.keys.get(kid)
            if key is None:
                raise AuthenticationError()
            payload = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self.settings.auth_issuer,
                audience=self.settings.auth_audience,
                leeway=5,
                options={
                    "require": ["iss", "sub", "aud", "exp", "iat", "nbf", "azp"],
                    "strict_aud": True,
                },
            )
            claims = Claims.model_validate(payload)
            if (
                claims.azp not in self.settings.allowed_origins
                or not 0 < claims.exp - claims.iat <= 60
                or claims.nbf > claims.exp
                or payload.get("sts") == "pending"
            ):
                raise AuthenticationError()
            if self.settings.auth_provider == "better_auth" and claims.sid is None:
                raise AuthenticationError()
            return VerifiedIdentity(issuer=claims.iss, subject=claims.sub, session_id=claims.sid)
        except (jwt.PyJWTError, ValidationError, ValueError, TypeError):
            raise AuthenticationError() from None
