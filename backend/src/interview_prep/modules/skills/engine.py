"""Pure ordinal rules; no probabilities, weighted scores or learned parameters."""

from collections import defaultdict
from datetime import UTC, datetime

from interview_prep.modules.skills.schemas import (
    CompetenceState,
    EvidenceSource,
    Importance,
    SkillFact,
    SkillRow,
)

IMPORTANCE_ORDER: tuple[Importance, ...] = ("Required", "Preferred", "Mentioned", "Low relevance")
ACTION_ORDER = ("Practice", "Validate", "Maintain")


def source_order(source: EvidenceSource) -> tuple[datetime, str]:
    return (source.occurred_at or datetime.min.replace(tzinfo=UTC), source.id)


def build_matrix(facts: list[SkillFact]) -> list[SkillRow]:
    """Latest observation per channel/concept; a weakness in either channel wins.

    Duplicate evidence IDs never increase support. Sources remain visible even
    when superseded. Two distinct concepts support 'Strong evidence', not mastery.
    """
    grouped: dict[str, list[SkillFact]] = defaultdict(list)
    for fact in facts:
        grouped[fact.key].append(fact)
    rows: list[SkillRow] = []
    for key, items in grouped.items():
        sources = sorted(
            {fact.source.id: fact.source for fact in items}.values(),
            key=lambda source: (source.kind, source_order(source)),
        )
        importance: Importance = min(
            (s.importance for s in sources if s.kind == "job" and s.importance),
            key=IMPORTANCE_ORDER.index,
            default=IMPORTANCE_ORDER[-1],
        )
        resume = any(s.kind == "resume" for s in sources)
        latest: dict[tuple[str, str], EvidenceSource] = {}
        for source in sources:
            if (
                source.kind not in ("assessment", "interview")
                or not source.eligible
                or source.outcome is None
                or not source.concept
                or source.occurred_at is None
            ):
                continue
            identity = (source.kind, source.concept)
            if identity not in latest or source_order(source) > source_order(latest[identity]):
                latest[identity] = source
        current = list(latest.values())
        assessment_validated = any(
            s.kind == "assessment" and s.outcome == "met" for s in current
        ) and not any(s.kind == "assessment" and s.outcome == "practice" for s in current)
        concepts = {s.concept for s in current if s.outcome == "met"}
        state: CompetenceState
        if any(s.outcome == "practice" for s in current):
            state, action = "Needs additional practice", "Practice"
            reason = "A latest eligible result needs practice; positive results do not hide it."
        elif len(concepts) >= 2:
            state, action = "Strong evidence", "Maintain"
            reason = "Eligible results met the criteria for at least two distinct concepts."
        elif assessment_validated:
            state, action = "Validated by assessment", "Maintain"
            reason = "An eligible assessment result met its criteria in the tested scope."
        elif current:
            state, action = "Some evidence", "Validate"
            reason = (
                "An eligible interview result met its criteria; assessment validation is absent."
            )
        else:
            state, action = "Needs assessment validation", "Validate"
            reason = (
                "No eligible demonstrated result is available; this does not establish inability."
            )
        rows.append(
            SkillRow(
                key=key,
                name=min((f.name for f in items), key=lambda name: (name.casefold(), name)),
                importance=importance,
                resume_state="Some evidence" if resume else "No resume evidence",
                competence_state=state,
                assessment_validated=assessment_validated,
                action=action,
                explanation=[
                    reason,
                    "Resume mentions and profile labels never validate competence.",
                    f"Order: {importance}, then {action.lower()}, then skill name.",
                ],
                sources=sources,
            )
        )
    return sorted(
        rows,
        key=lambda row: (
            IMPORTANCE_ORDER.index(row.importance),
            ACTION_ORDER.index(row.action),
            row.name.casefold(),
            row.key,
        ),
    )
