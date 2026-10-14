"""Replaceable conceptual evaluator. Mock lexical coverage is simulation, not competence."""

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

POLICY_VERSION = "assessment-scoring-v1"


@dataclass(frozen=True)
class ConceptualInput:
    prompt: str
    response: str
    expected_concepts: tuple[str, ...]
    rubric: tuple[str, ...]


class ConceptualEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, revalidate_instances="always")
    score: int = Field(ge=0, le=4)
    kind: Literal["simulation", "model_assisted"]
    feedback: str = Field(min_length=1, max_length=4000)
    matched_concepts: list[str] = Field(max_length=12)


class EvaluationProvider(Protocol):
    name: str
    version: str
    kind: Literal["simulation", "model_assisted"]

    async def evaluate(self, content: ConceptualInput) -> object: ...


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


class MockAIProvider:
    name = "MockAIProvider"
    version = "mock-lexical-v1"
    kind: Literal["simulation", "model_assisted"] = "simulation"

    async def evaluate(self, content: ConceptualInput) -> ConceptualEvaluation:
        # A concept matches when at least half its distinct >=4-character words
        # occur literally in the response. Integer rounding is floor throughout.
        response_words = tokens(content.response)
        matched: list[str] = []
        for concept in content.expected_concepts:
            words = {word for word in tokens(concept) if len(word) >= 4}
            if words and 2 * len(words & response_words) >= len(words):
                matched.append(concept)
        score = 4 * len(matched) // max(1, len(content.expected_concepts))
        return ConceptualEvaluation(
            score=score,
            kind="simulation",
            matched_concepts=matched,
            feedback=(
                f"Mock simulation: lexical overlap with {len(matched)} of "
                f"{len(content.expected_concepts)} expected concepts. "
                "This does not judge correctness, reasoning, or demonstrated competence. "
                "Compare your response with the review concepts and practice explaining them."
            ),
        )


def validate_evaluation(
    raw: object, provider: EvaluationProvider, concepts: list[str]
) -> ConceptualEvaluation:
    result = ConceptualEvaluation.model_validate(raw)
    if result.kind != provider.kind or len(set(result.matched_concepts)) != len(
        result.matched_concepts
    ):
        raise ValueError("Invalid evaluation provenance")
    if not set(result.matched_concepts).issubset(concepts):
        raise ValueError("Provider returned unknown concepts")
    if not result.feedback.strip():
        raise ValueError("Empty evaluation feedback")
    if (
        not provider.name.strip()
        or len(provider.name) > 100
        or not provider.version.strip()
        or len(provider.version) > 100
    ):
        raise ValueError("Invalid provider identity")
    return result
