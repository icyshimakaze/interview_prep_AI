import asyncio

import httpx
import pytest

from interview_prep.ai.errors import ProviderTimeout
from interview_prep.ai.transport import MAX_CONCURRENT_CALLS, request_json


async def test_shared_client_bounds_concurrency_and_times_out_queued_work() -> None:
    entered = 0
    all_entered, release = asyncio.Event(), asyncio.Event()

    async def handle(request: httpx.Request) -> httpx.Response:
        nonlocal entered
        entered += 1
        if entered == MAX_CONCURRENT_CALLS:
            all_entered.set()
        await release.wait()
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        tasks = [
            asyncio.create_task(
                request_json(
                    client,
                    "https://provider.invalid/chat",
                    {},
                    {},
                    3,
                    0,
                )
            )
            for _ in range(MAX_CONCURRENT_CALLS)
        ]
        try:
            await asyncio.wait_for(all_entered.wait(), 2)
            with pytest.raises(ProviderTimeout):
                await request_json(client, "https://provider.invalid/chat", {}, {}, 0.05, 0)
            assert entered == MAX_CONCURRENT_CALLS  # Queued timeout never reached the provider.
        finally:
            release.set()
            await asyncio.gather(*tasks)
        assert await request_json(client, "https://provider.invalid/chat", {}, {}, 1, 0)
