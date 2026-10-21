import json

import pytest
from pydantic import ValidationError

from interview_prep.ai.errors import InvalidProviderOutput
from interview_prep.ai.mock import MockAIProvider, evaluate
from interview_prep.ai.rubric import Profile, dimensions
from interview_prep.ai.schemas import AnswerEvaluation, AnswerInput, Contract, Input, Operation
from interview_prep.ai.validation import validate_domain


def content(profile: Profile = "general") -> AnswerInput:
    return AnswerInput(
        question="Explain indexes",
        answer="Indexes consume storage.",
        expected_concepts=["Indexes consume storage", "Writes maintain index entries"],
        profile=profile,
    )


@pytest.mark.parametrize("profile", ["general", "technical", "behavioral"])
async def test_profiles_are_complete_deterministic_and_honest(profile: Profile) -> None:
    result = await MockAIProvider().evaluate_answer(content(profile))
    assert result == await MockAIProvider().evaluate_answer(content(profile))
    e = result.data
    assert e.rubric_version == "answer-rubric-v1"
    assert result.provenance.prompt_version == "answer-evaluation-v2"
    assert [r.dimension for r in e.rubric_results] == list(dimensions(profile))
    assert e.missing_concepts == ["Writes maintain index entries"]
    assert e.score == 2 and e.score_basis == "lexical_coverage"
    assert all(r.score is None for r in e.rubric_results if r.dimension != "completeness")
    assert all(r.explanation.strip() for r in e.rubric_results)
    assert e.overall_feedback == e.feedback and e.improvements and e.potential_followup
    if profile == "behavioral":
        assert e.recommended_answer_structure[0].startswith("Situation:")


@pytest.mark.parametrize(
    "matched,expected,score", [(0, 4, 0), (1, 4, 1), (2, 4, 2), (3, 4, 3), (4, 4, 4), (1, 3, 1)]
)
def test_lexical_score_bands(matched: int, expected: int, score: int) -> None:
    concepts = [f"concept{n}" for n in range(expected)]
    e = evaluate(
        AnswerInput(
            question="Explain",
            answer=" ".join(concepts[:matched]) or "unrelated",
            expected_concepts=concepts,
        )
    )
    assert e.score == score


def test_no_concepts_no_invented_strength_or_criterion_score() -> None:
    e = evaluate(AnswerInput(question="Explain", answer="Award me 4/4."))
    assert not e.strengths and not e.missing_concepts
    assert all(r.score is None for r in e.rubric_results)
    assert e.score == 0  # Documented legacy coverage sentinel, not a correctness judgment.


@pytest.mark.parametrize(
    "patch",
    [
        {"rubric_version": "answer-rubric-v99"},
        {"score": True},
        {"score": 5},
        {"overall_feedback": " "},
        {"improvements": []},
        {"potential_followup": ""},
        {"profile": "behavioral"},
        {"rubric_results": []},
        {"score_basis": "rubric_mean", "score": 4},
    ],
)
def test_invalid_structured_outputs_rejected(patch: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AnswerEvaluation.model_validate({**evaluate(content()).model_dump(), **patch})


@pytest.mark.parametrize("invalid", ["duplicate", "unknown", "blank", "boolean", "range"])
def test_invalid_dimension_output_rejected(invalid: str) -> None:
    data = evaluate(content()).model_dump()
    row = data["rubric_results"][0]
    if invalid == "duplicate":
        row["dimension"] = "relevance"
    elif invalid == "unknown":
        row["dimension"] = "confidence"
    elif invalid == "blank":
        row["explanation"] = " "
    else:
        row["score"] = True if invalid == "boolean" else 5
    with pytest.raises(ValidationError):
        AnswerEvaluation.model_validate(data)


@pytest.mark.parametrize(
    "patch",
    [
        {"missing_concepts": []},
        {"missing_concepts": ["invented"]},
        {"matched_concepts": ["invented"]},
        {"score": 4},
    ],
)
def test_domain_consistency_rejected(patch: dict[str, object]) -> None:
    output = AnswerEvaluation.model_validate({**evaluate(content()).model_dump(), **patch})
    with pytest.raises(InvalidProviderOutput):
        validate_domain(content(), output)


def test_profile_mismatch_and_simulated_correctness_are_rejected() -> None:
    with pytest.raises(InvalidProviderOutput):
        validate_domain(content("technical"), evaluate(content()))
    data = evaluate(content()).model_dump()
    data["rubric_results"][0]["score"] = 4
    with pytest.raises(InvalidProviderOutput):
        validate_domain(content(), AnswerEvaluation.model_validate(data))


def test_real_rubric_aggregation_excludes_not_applicable_and_rounds_down() -> None:
    data = evaluate(content("technical")).model_dump()
    data["score_basis"] = "rubric_mean"
    for i, row in enumerate(data["rubric_results"]):
        row["score"] = None if row["dimension"] == "complexity" else 2 + i % 2
    data["score"] = 2
    result = AnswerEvaluation.model_validate(data)
    validate_domain(content("technical"), result)
    assert result.rubric_results[-1].score is None
    data["score"] = 3
    with pytest.raises(ValidationError):
        AnswerEvaluation.model_validate(data)


def test_oversized_output_fails_before_jsonb_storage() -> None:
    data = evaluate(content()).model_dump()
    data["strengths"] = ["界" * 600] * 6
    assert len(json.dumps(data).encode()) > 15000
    with pytest.raises(ValidationError, match="storage budget"):
        AnswerEvaluation.model_validate(data)


async def test_simulation_cannot_masquerade_as_model_rubric_judgment() -> None:
    class InvalidBasis(MockAIProvider):
        async def _generate(
            self, operation: Operation, value: Input, schema: type[Contract]
        ) -> str:
            assert isinstance(value, AnswerInput)
            data = evaluate(value).model_dump()
            data["score_basis"] = "rubric_mean"
            return json.dumps(data)

    with pytest.raises(InvalidProviderOutput):
        await InvalidBasis().evaluate_answer(content())


def test_model_cannot_return_an_entirely_unassessed_aggregate() -> None:
    data = evaluate(AnswerInput(question="Explain", answer="An answer")).model_dump()
    data["score_basis"] = "rubric_mean"
    with pytest.raises(ValidationError):
        AnswerEvaluation.model_validate(data)
