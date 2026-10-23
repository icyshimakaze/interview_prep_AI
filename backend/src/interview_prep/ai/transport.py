"""Bounded JSON transport with a total deadline and narrowly scoped retries."""

import asyncio
import json
import math
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from weakref import WeakKeyDictionary

import httpx

from interview_prep.ai.errors import (
    InvalidProviderOutput,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)

MAX_RESPONSE_BYTES = 262144
TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
MAX_CONCURRENT_CALLS = 4
_CLIENT_SLOTS: WeakKeyDictionary[httpx.AsyncClient, asyncio.Semaphore] = WeakKeyDictionary()


def provider_slots(client: httpx.AsyncClient) -> asyncio.Semaphore:
    """Share a bounded pool across provider instances using the application client."""
    if client not in _CLIENT_SLOTS:
        _CLIENT_SLOTS[client] = asyncio.Semaphore(MAX_CONCURRENT_CALLS)
    return _CLIENT_SLOTS[client]


def retry_delay(header: str | None, attempt: int) -> float:
    if header:
        try:
            delay = float(header)
            if math.isfinite(delay):
                return max(0.0, delay)
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(header) - datetime.now(UTC)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 0.25 * (2.0**attempt)


def quota_exhausted(body: bytes) -> bool:
    try:
        data: object = json.loads(body)
        if isinstance(data, dict):
            error: object = data.get("error")
            return isinstance(error, dict) and error.get("code") == "insufficient_quota"
    except (ValueError, RecursionError):
        pass
    return False


async def request_json(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, object],
    headers: dict[str, str],
    deadline_seconds: float,
    retries: int,
    *,
    distinguish_rate_limits: bool = False,
) -> bytes:
    try:
        async with asyncio.timeout(deadline_seconds), provider_slots(client):
            for attempt in range(retries + 1):
                try:
                    async with client.stream(
                        "POST",
                        url,
                        json=payload,
                        headers={**headers, "Accept-Encoding": "identity"},
                        timeout=deadline_seconds,
                        follow_redirects=False,
                    ) as response:
                        if (
                            response.headers.get("content-encoding", "identity").lower()
                            != "identity"
                        ):
                            raise InvalidProviderOutput()
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                                raise InvalidProviderOutput()
                            body.extend(chunk)
                        if response.status_code == 200:
                            return bytes(body)
                        if (
                            response.status_code not in TRANSIENT_STATUS
                            or attempt == retries
                            or quota_exhausted(bytes(body))
                        ):
                            if response.status_code == 429 and distinguish_rate_limits:
                                raise ProviderRateLimited()
                            raise ProviderUnavailable()
                        delay = retry_delay(response.headers.get("Retry-After"), attempt)
                        # Never retry earlier than a server's long backoff request.
                        if delay >= deadline_seconds:
                            if response.status_code == 429 and distinguish_rate_limits:
                                raise ProviderRateLimited()
                            raise ProviderUnavailable()
                except (httpx.ConnectError, httpx.ConnectTimeout):
                    if attempt == retries:
                        raise ProviderUnavailable() from None
                    delay = retry_delay(None, attempt)
                except httpx.TimeoutException:
                    # Ambiguous post-send timeout: do not duplicate potentially billed generation.
                    raise ProviderTimeout() from None
                except httpx.HTTPError:
                    raise ProviderUnavailable() from None
                await asyncio.sleep(delay)
    except TimeoutError:
        raise ProviderTimeout() from None
    raise ProviderUnavailable()
