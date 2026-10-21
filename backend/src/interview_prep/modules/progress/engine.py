"""Pure aggregates of recorded facts, with explicit denominators and provenance."""

from collections import defaultdict
from datetime import UTC, datetime
from hashlib import sha256

from interview_prep.ai.schemas import AnswerEvaluation
from interview_prep.modules.progress.facts import ResultFact
from interview_prep.modules.progress.schemas import (
    Accuracy,
    AssessmentPoint,
    CategoryPerformance,
    EvidenceSummary,
    MissedConcept,
    RatingPoint,
    RatingSeries,
)
from interview_prep.modules.skills.schemas import SkillRow


def accuracy(values: list[bool]) -> Accuracy:
    correct = sum(values)
    return Accuracy(
        correct=correct,
        graded=len(values),
        percent=round(100 * correct / len(values), 1) if values else None,
    )


def enough_history(dates: list[datetime]) -> bool:
    return len(dates) >= 3 and len({at.astimezone(UTC).date() for at in dates}) >= 3


def assessment_summary(
    records: list[ResultFact],
) -> tuple[list[AssessmentPoint], list[CategoryPerformance]]:
    sessions: dict[str, list[ResultFact]] = defaultdict(list)
    categories: dict[str, list[bool]] = defaultdict(list)
    for record in {r.id: r for r in records if r.channel == "assessment"}.values():
        sessions[record.session_id].append(record)
        if record.objective_correct is not None:
            categories[record.category].append(record.objective_correct)
    points = []
    for identifier, answers in sessions.items():
        values = [r.objective_correct for r in answers if r.objective_correct is not None]
        points.append(
            AssessmentPoint(
                id=identifier,
                at=max(r.at for r in answers),
                excluded=len(answers) - len(values),
                grading_versions=sorted(
                    {r.grading_version for r in answers if r.objective_correct is not None}
                ),
                **accuracy(values).model_dump(),
            )
        )
    return sorted(points, key=lambda p: (p.at, p.id)), [
        CategoryPerformance(category=category, **accuracy(values).model_dump())
        for category, values in sorted(categories.items())
    ]


def assessment_chart_available(points: list[AssessmentPoint]) -> bool:
    graded = [p for p in points if p.graded]
    policies = {v for point in graded for v in point.grading_versions}
    return enough_history([p.at for p in graded]) and len(policies) == 1 and "" not in policies


def structured(record: ResultFact) -> AnswerEvaluation | None:
    if not record.completed or record.kind not in {"deterministic", "model_assisted"}:
        return None
    if not record.provider_version or not record.rubric_version:
        return None
    if record.kind == "model_assisted" and (not record.provider or not record.model):
        return None
    try:
        evaluation = AnswerEvaluation.model_validate(record.payload)
    except ValueError:
        return None
    if (
        evaluation.score_basis != "rubric_mean"
        or record.scale != 4
        or record.score != evaluation.score
        or record.rubric_version != evaluation.rubric_version
    ):
        return None
    return evaluation


def interview_summary(records: list[ResultFact]) -> tuple[list[RatingSeries], int]:
    groups: dict[tuple[str, ...], dict[str, list[ResultFact]]] = defaultdict(
        lambda: defaultdict(list),
    )
    excluded = 0
    for record in {r.id: r for r in records if r.channel == "interview"}.values():
        evaluation = structured(record)
        if evaluation is None:
            excluded += 1
            continue
        dimensions = tuple(r.dimension for r in evaluation.rubric_results if r.score is not None)
        key = (
            record.kind,
            record.provider,
            record.model or "",
            record.provider_version,
            record.rubric_version,
            evaluation.profile,
            *dimensions,
        )
        groups[key][record.session_id].append(record)
    result: list[RatingSeries] = []
    for key, sessions in sorted(groups.items()):
        points = [
            RatingPoint(
                session_id=identifier,
                at=max(r.at for r in answers),
                mean=round(sum(r.score for r in answers if r.score is not None) / len(answers), 2),
                answers=len(answers),
            )
            for identifier, answers in sessions.items()
        ]
        points.sort(key=lambda p: (p.at, p.session_id))
        result.append(
            RatingSeries(
                key=sha256("\0".join(key).encode()).hexdigest()[:20],
                label="Recorded rubric mean (0–4); model ratings are not independent validation.",
                kind=key[0],
                provider=key[1],
                model=key[2] or None,
                provider_version=key[3],
                rubric_version=key[4],
                profile=key[5],
                assessed_dimensions=list(key[6:]),
                points=points,
                chart_available=enough_history([p.at for p in points]),
            )
        )
    return result, excluded


def missed_concepts(records: list[ResultFact]) -> list[MissedConcept]:
    observations: dict[tuple[str, str], list[ResultFact]] = defaultdict(list)
    for record in {r.id: r for r in records}.values():
        if record.objective_correct is False and record.concept.strip():
            observations[(record.concept, "deterministic")].append(record)
        result = structured(record)
        if result is not None and record.kind == "model_assisted":
            for concept in set(result.missing_concepts):
                observations[(concept, "model_assisted")].append(record)
    result_rows = [
        MissedConcept(
            concept=concept,
            basis="deterministic" if basis == "deterministic" else "model_assisted",
            occurrences=len(rows),
            sessions=len({(r.channel, r.session_id) for r in rows}),
            last_seen=max(r.at for r in rows),
        )
        for (concept, basis), rows in observations.items()
        if len({(r.channel, r.session_id) for r in rows}) >= 2
    ]
    return sorted(result_rows, key=lambda r: (-r.sessions, -r.occurrences, r.concept))[:10]


def evidence_summaries(rows: list[SkillRow]) -> tuple[list[EvidenceSummary], list[EvidenceSummary]]:
    strengths = []
    validation = []
    for row in rows:
        count = len({s.id for s in row.sources if s.eligible})
        summary = EvidenceSummary(
            topic=row.name,
            description=row.explanation[0],
            source_count=count,
        )
        if row.action == "Maintain" and row.assessment_validated and count:
            strengths.append(summary)
        else:
            validation.append(summary)
    return strengths[:20], validation[:20]
