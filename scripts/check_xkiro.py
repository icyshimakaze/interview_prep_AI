"""One opt-in synthetic free-model request. Never prints keys, headers or raw output."""

import argparse
import asyncio
import json
import time
from typing import Literal

import httpx
from pydantic import ValidationError

from interview_prep.ai.errors import ProviderError
from interview_prep.ai.schemas import Contract
from interview_prep.ai.transport import request_json
from interview_prep.ai.xkiro import ChatResponse
from interview_prep.core.config import get_settings

FREE_MODEL = "qwen/qwen3.8-max:free"


class SmokeOutput(Contract):
    status: Literal["ok"]


async def check() -> dict[str, object]:
    settings = get_settings()
    if not settings.xkiro_api_key.get_secret_value().strip():
        return {"result": "skipped", "reason": "No configured backend xKiro key"}
    status: int | None = None

    async def record(response: httpx.Response) -> None:
        nonlocal status
        status = response.status_code

    started = time.monotonic()
    result: dict[str, object] = {"model": FREE_MODEL, "maximum_requests": 1}
    async with httpx.AsyncClient(
        trust_env=False,
        follow_redirects=False,
        event_hooks={"response": [record]},
    ) as client:
        try:
            raw = await request_json(
                client,
                settings.xkiro_base_url + "/chat/completions",
                {
                    "model": FREE_MODEL,
                    "stream": False,
                    "max_tokens": 128,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": 'Return only JSON: {"status":"ok"}'}],
                },
                {"Authorization": "Bearer " + settings.xkiro_api_key.get_secret_value()},
                60,
                0,
                distinguish_rate_limits=True,
            )
            response = ChatResponse.model_validate_json(raw)
            choice = response.choices[0]
            if (
                response.model != FREE_MODEL
                or choice.finish_reason != "stop"
                or choice.message.refusal
                or not choice.message.content
            ):
                result.update(result="failed", category="response_handling")
            else:
                SmokeOutput.model_validate_json(choice.message.content)
                result.update(
                    result="passed",
                    authentication=True,
                    model_accepted=True,
                    structured_output_valid=True,
                )
        except ValidationError:
            result.update(result="failed", category="response_handling")
        except ProviderError as error:
            category = (
                "authentication"
                if status in {401, 403}
                else "rate_limit"
                if status == 429
                else "model_or_request_configuration"
                if status in {400, 402, 404, 422}
                else "upstream_server"
                if status is not None and status >= 500
                else "timeout"
                if error.code == "ai_timeout"
                else "response_handling"
                if error.code == "ai_invalid_output"
                else "network_connectivity"
            )
            result.update(result="failed", category=category, safe_code=error.code)
    result.update(http_status=status, elapsed_seconds=round(time.monotonic() - started, 2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        required=True,
        help="Explicitly authorize one real free-model call (no retries)",
    )
    parser.parse_args()
    result = asyncio.run(check())
    print(json.dumps(result))
    if result["result"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
