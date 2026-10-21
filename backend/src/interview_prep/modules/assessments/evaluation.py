"""Replaceable conceptual evaluator. Mock lexical coverage is simulation, not competence."""

from dataclasses import dataclass
from typing import Literal, Protocol

from interview_prep.ai.mock import MockAIProvider as SharedMockAIProvider
from interview_prep.ai.provider import AIProvider
from interview_prep.ai.rubric import Profile
from interview_prep.ai.schemas import AnswerEvaluation, AnswerInput
from interview_prep.ai.validation import validate_domain

POLICY_VERSION = "assessment-scoring-v1"


@dataclass(frozen=True)
class ConceptualInput:
    prompt: str
    response: str
    expected_concepts: tuple[str, ...]
    rubric: tuple[str, ...]
    profile: Profile = "general"


class ConceptualEvaluation(AnswerEvaluation):
    kind: Literal["simulation", "model_assisted"]


class EvaluationProvider(Protocol):
    name: str
    version: str
    kind: Literal["simulation", "model_assisted"]

    async def evaluate(self, content: ConceptualInput) -> object: ...


class ProviderEvaluationAdapter:
    """Keep the assessment contract while using the application's shared provider."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.name, self.version, self.kind = provider.name, provider.version, provider.kind
        self.timeout_seconds = provider.timeout_seconds
        self.model = provider.model

    async def evaluate(self, content: ConceptualInput) -> ConceptualEvaluation:
        result = await self.provider.evaluate_answer(
            AnswerInput(
                question=content.prompt,
                answer=content.response,
                expected_concepts=list(content.expected_concepts),
                rubric=list(content.rubric),
                profile=content.profile,
            )
        )
        validate_domain(
            AnswerInput(
                question=content.prompt,
                answer=content.response,
                expected_concepts=list(content.expected_concepts),
                rubric=list(content.rubric),
                profile=content.profile,
            ),
            result.data,
        )
        return ConceptualEvaluation(
            **result.data.model_dump(),
            kind=result.provenance.kind,
        )


class MockAIProvider(ProviderEvaluationAdapter):
    """Compatibility name for the existing assessment dependency and its test seams."""

    def __init__(self) -> None:
        super().__init__(SharedMockAIProvider())


def validate_evaluation(
    raw: object, provider: EvaluationProvider, concepts: list[str]
) -> ConceptualEvaluation:
    result = ConceptualEvaluation.model_validate(raw)
    if result.score_basis != (
        "lexical_coverage" if provider.kind == "simulation" else "rubric_mean"
    ):
        raise ValueError("Invalid score basis for provider")
    if result.kind != provider.kind or len(set(result.matched_concepts)) != len(
        result.matched_concepts
    ):
        raise ValueError("Invalid evaluation provenance")
    if not set(result.matched_concepts).issubset(concepts):
        raise ValueError("Provider returned unknown concepts")
    if result.missing_concepts != [c for c in concepts if c not in result.matched_concepts]:
        raise ValueError("Provider returned inconsistent missing concepts")
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
