"""Immutable editorial rubric definitions; changing semantics requires a new version."""

from typing import Literal

RUBRIC_VERSION = "answer-rubric-v1"
EVALUATION_PROMPT_VERSION: Literal["answer-evaluation-v2"] = "answer-evaluation-v2"
Profile = Literal["general", "technical", "behavioral"]
Dimension = Literal[
    "correctness",
    "relevance",
    "completeness",
    "depth",
    "communication_structure",
    "technical_accuracy",
    "important_concepts",
    "trade_offs",
    "complexity",
    "star_structure",
    "specificity",
    "ownership",
    "impact",
    "reflection",
]
GENERAL: tuple[Dimension, ...] = (
    "correctness",
    "relevance",
    "completeness",
    "depth",
    "communication_structure",
)
TECHNICAL: tuple[Dimension, ...] = (
    "technical_accuracy",
    "important_concepts",
    "trade_offs",
    "complexity",
)
BEHAVIORAL: tuple[Dimension, ...] = (
    "star_structure",
    "specificity",
    "ownership",
    "impact",
    "reflection",
)
SCORE_MEANINGS = (
    "Absent or incorrect: no usable evidence for this criterion, or a central error.",
    "Limited: some relevant evidence, with major gaps or errors.",
    "Partial: the central idea is present, with significant gaps or weak support.",
    "Sound: accurate and supported for the question, with only minor gaps.",
    "Thorough: accurate, well supported and complete for the requested scope.",
)


def dimensions(profile: Profile) -> tuple[Dimension, ...]:
    return GENERAL + (
        TECHNICAL if profile == "technical" else BEHAVIORAL if profile == "behavioral" else ()
    )


def profile_for(question_type: str) -> Profile:
    return "behavioral" if question_type == "behavioral" else "technical"
