"""xKiro quotes evidence; source positions are calculated locally, never guessed."""

import json
from typing import Literal

from pydantic import Field, ValidationError

from interview_prep.ai.errors import InvalidProviderOutput
from interview_prep.ai.prompts import SYSTEM
from interview_prep.ai.schemas import Concept, Contract, JobInput, Label, ResumeInput, Text


class SkillQuote(Contract):
    name: Label
    evidence: Concept


class RequirementQuote(SkillQuote):
    importance: Literal["required", "preferred", "mentioned"]


class ResumeDraft(Contract):
    summary: Text
    skills: list[SkillQuote] = Field(max_length=30)
    suggestions: list[Text] = Field(min_length=1, max_length=6)


class JobDraft(Contract):
    summary: Text
    requirements: list[RequirementQuote] = Field(max_length=30)
    review_notes: list[Text] = Field(min_length=1, max_length=6)


def document_contract(content: ResumeInput | JobInput) -> tuple[type[Contract], str]:
    task = (
        "Summarize supplied resume claims and extract at most 30 distinct skill mentions. "
        "A mention is not demonstrated skill. Suggest concrete improvements "
        "without inventing facts. Include languages, frameworks, tools, projects and "
        "experience where supplied. Missing resume evidence never means lack of competence. "
        if isinstance(content, ResumeInput)
        else "Summarize the supplied job description and extract at most 30 distinct skill "
        "requirements. Classify required/preferred only when explicit; otherwise mentioned. "
        "Use summary for responsibilities and review_notes for technical concepts and likely "
        "interview topics grounded in those requirements. All extraction needs human review. "
    )
    return (
        ResumeDraft if isinstance(content, ResumeInput) else JobDraft,
        SYSTEM + "\n\n" + task + "Each evidence must be a short, exact, case-sensitive substring "
        "of input.text, not a paraphrase. Do not return start/end positions: the server calculates "
        "them from the quoted evidence. Keep the entire response concise.",
    )


def ground_document(content: ResumeInput | JobInput, raw: str) -> str:
    if len(raw.encode("utf-8")) > 131072:
        raise InvalidProviderOutput()
    try:
        draft = (
            ResumeDraft.model_validate_json(raw)
            if isinstance(content, ResumeInput)
            else JobDraft.model_validate_json(raw)
        )
    except ValidationError:
        raise InvalidProviderOutput() from None
    quotes = draft.skills if isinstance(draft, ResumeDraft) else draft.requirements
    grounded: list[dict[str, object]] = []
    for quote in quotes:
        # Use the first exact occurrence, in Unicode code points. No fuzzy matching,
        # case folding, invented excerpts or model-supplied positions are accepted.
        start = content.text.find(quote.evidence)
        if start < 0:
            raise InvalidProviderOutput()
        grounded.append({**quote.model_dump(), "start": start, "end": start + len(quote.evidence)})
    payload = draft.model_dump()
    payload["skills" if isinstance(draft, ResumeDraft) else "requirements"] = grounded
    # BaseProvider still validates the public schema, uniqueness and source spans.
    return json.dumps(payload)
