"""Reproduce six synthetic mock cases, or explicitly sample one real free-model case."""

import argparse
import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field

from interview_prep.ai.errors import ProviderError
from interview_prep.ai.mock import MockAIProvider
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.schemas import AnswerInput, Contract
from interview_prep.ai.xkiro import XkiroProvider
from interview_prep.core.config import Settings, get_settings

ROOT = Path(__file__).resolve().parents[1]
FREE_MODEL = "qwen/qwen3.8-max:free"


class EvaluationCase(Contract):
    id: str = Field(pattern=r"^[a-z_]+$")
    content: AnswerInput
    expected_mock_matches: list[str]
    human_review: list[str] = Field(min_length=1)


class EvaluationSet(Contract):
    version: Literal["answer-quality-v1"]
    cases: list[EvaluationCase] = Field(min_length=6, max_length=6)


def load_cases() -> EvaluationSet:
    return EvaluationSet.model_validate_json(
        (ROOT / "content/evaluation/answer-quality-v1.json").read_text(encoding="utf-8")
    )


def live_settings(settings: Settings) -> Settings:
    # Diagnostic override only: never mutate dotenv, enable a paid route, or retry.
    return Settings(
        _env_file=None,
        database_url=settings.database_url,
        demo_rate_limit_key=settings.demo_rate_limit_key,
        app_env="test",
        auth_enabled=False,
        public_demo_only=False,
        ai_provider="xkiro",
        ai_timeout_seconds=60,
        ai_max_retries=0,
        xkiro_api_key=settings.xkiro_api_key,
        xkiro_base_url="https://api.xkiro.com/v1",
        xkiro_reasoning_model=FREE_MODEL,
        xkiro_multimodal_model="qwen/qwen3.8-omni-flash:free",
        xkiro_model_routes={},
        xkiro_allow_paid_models=False,
    )


async def sample(provider: AIProvider, case: EvaluationCase) -> dict[str, object]:
    started = time.monotonic()
    try:
        result = await provider.evaluate_answer(case.content)
    except ProviderError as error:
        return {"case": case.id, "result": "failed", "safe_code": error.code}
    return {
        "case": case.id,
        "result": "schema_and_domain_valid",
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "output": result.model_dump(mode="json"),
        "human_review_required": case.human_review,
    }


async def check(live_case: str | None) -> dict[str, object]:
    dataset = load_cases()
    report: dict[str, object] = {
        "dataset": dataset.version,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "mode": "live_single_sample" if live_case else "deterministic_mock",
        "semantic_accuracy_established": False,
    }
    if live_case:
        case = next(case for case in dataset.cases if case.id == live_case)
        settings = live_settings(get_settings())
        if not settings.xkiro_api_key.get_secret_value().strip():
            return {
                **report,
                "result": "skipped",
                "reason": "No configured backend xKiro key",
            }
        async with httpx.AsyncClient(trust_env=False, follow_redirects=False) as client:
            rows = [await sample(XkiroProvider(client, settings), case)]
        report["maximum_requests"] = 1
        # Output is synthetic, but do not write a provider-echoed credential.
        if settings.xkiro_api_key.get_secret_value() in json.dumps(rows):
            return {**report, "result": "failed", "reason": "Unsafe provider response"}
    else:
        rows = [await sample(MockAIProvider(), case) for case in dataset.cases]
        report["maximum_requests"] = 0
    report["cases"] = rows
    report["result"] = "failed" if any(row["result"] == "failed" for row in rows) else "completed"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-case",
        choices=[case.id for case in load_cases().cases],
        help="Authorize exactly one synthetic Max-free evaluation, no retries",
    )
    arguments = parser.parse_args()
    report = asyncio.run(check(arguments.live_case))
    destination = (
        ROOT
        / ".cache"
        / ("ai-quality-live.json" if arguments.live_case else "ai-quality-mock.json")
    )
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}))
    if report["result"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
