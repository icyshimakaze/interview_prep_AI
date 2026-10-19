"""Freeze owned inputs, then allocate one explainable main question at a time."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.ai.schemas import AnswerInput
from interview_prep.modules.adaptive.engine import select_questions
from interview_prep.modules.adaptive.schemas import (
    Candidate,
    Exposure,
    Performance,
    SelectionInput,
    SkillContext,
)
from interview_prep.modules.adaptive.service import exposures
from interview_prep.modules.context.models import TargetJob, TargetJobVersion
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import InterviewQuestion, InterviewSession
from interview_prep.modules.interviews.policy import CATEGORIES, conflict, feasible
from interview_prep.modules.interviews.schemas import InterviewConfiguration, InterviewType
from interview_prep.modules.interviews.work_models import InterviewCandidate
from interview_prep.modules.questions.models import (
    ExpectedConcept,
    PublicationStatus,
    Question,
    QuestionRubricCriterion,
    QuestionSkill,
    QuestionType,
    QuestionVersion,
)
from interview_prep.modules.questions.queries import visible_versions
from interview_prep.modules.skills.service import skill_matrix


async def concepts(session: AsyncSession, version_id: UUID) -> tuple[list[str], list[str]]:
    expected = list(
        (
            await session.scalars(
                select(ExpectedConcept.text)
                .where(ExpectedConcept.question_version_id == version_id)
                .order_by(ExpectedConcept.position)
            )
        ).all()
    )
    rubric = list(
        (
            await session.scalars(
                select(QuestionRubricCriterion.description)
                .where(QuestionRubricCriterion.question_version_id == version_id)
                .order_by(QuestionRubricCriterion.code)
            )
        ).all()
    )
    return expected, rubric


async def pool(
    session: AsyncSession, owner: UUID, config: InterviewConfiguration
) -> list[QuestionVersion]:
    query = visible_versions(owner).where(
        QuestionVersion.status == PublicationStatus.PUBLISHED,
        QuestionVersion.category.in_(CATEGORIES[config.interview_type]),
        QuestionVersion.question_type.in_(
            [QuestionType.WRITTEN, QuestionType.DESIGN, QuestionType.BEHAVIORAL]
        ),
    )
    if config.difficulty != "auto":
        query = query.where(QuestionVersion.difficulty == config.difficulty)
    if config.interview_type == InterviewType.SYSTEM_DESIGN:
        query = query.where(QuestionVersion.question_type == QuestionType.DESIGN)
    if config.interview_type == InterviewType.BEHAVIORAL:
        query = query.where(QuestionVersion.question_type == QuestionType.BEHAVIORAL)
    versions = list((await session.scalars(query.order_by(QuestionVersion.id).limit(1001))).all())
    if len(versions) > 1000:
        conflict("interview_context_limit")
    eligible: list[QuestionVersion] = []
    for version in versions:
        expected, rubric = await concepts(session, version.id)
        if not expected or not rubric:
            continue
        try:
            AnswerInput(
                question=version.prompt or "",
                answer="eligibility check",
                expected_concepts=expected,
                rubric=rubric,
            )
        except ValueError:
            continue
        eligible.append(version)
    return eligible


async def validate_target(
    session: AsyncSession, owner: UUID, target_id: UUID | None
) -> tuple[UUID | None, str | None]:
    if target_id is None:
        return None, None
    target = await session.scalar(
        select(TargetJob).where(TargetJob.id == target_id, TargetJob.owner_id == owner)
    )
    if target is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    version = await session.scalar(
        select(TargetJobVersion)
        .where(TargetJobVersion.target_job_id == target_id, TargetJobVersion.owner_id == owner)
        .order_by(TargetJobVersion.version.desc())
    )
    return version.id if version else None, target.title


async def freeze(
    session: AsyncSession, interview: InterviewSession, user: User, config: InterviewConfiguration
) -> None:
    versions = await pool(session, user.id, config)
    if not feasible(
        config.interview_type, [v.category or "" for v in versions], config.question_count
    ):
        conflict("interview_pool")
    matrix = await skill_matrix(session, user, config.target_id)
    if len(matrix.rows) > 1000:
        conflict("interview_context_limit")
    target_version, target_title = await validate_target(session, user.id, config.target_id)
    interview.target_job_version_id = target_version
    mappings = (
        await session.execute(
            select(QuestionSkill.question_version_id, QuestionSkill.skill_id)
            .where(QuestionSkill.question_version_id.in_([v.id for v in versions]))
            .limit(10001)
        )
    ).all()
    if len(mappings) > 10000:
        conflict("interview_context_limit")
    by_version: dict[UUID, list[str]] = {}
    for v_id, skill_id in mappings:
        by_version.setdefault(v_id, []).append(str(skill_id))
    identities = dict(
        (
            await session.execute(
                select(Question.id, Question.canonical_concept).where(
                    Question.id.in_([v.question_id for v in versions])
                )
            )
        ).all()
    )
    performance: dict[str, Performance] = {}
    for row in matrix.rows:
        for source in row.sources:
            if (
                source.eligible
                and source.kind in ("assessment", "interview")
                and source.concept
                and source.difficulty
                and source.outcome
                and source.occurred_at
            ):
                performance.setdefault(
                    source.id,
                    Performance(
                        id=source.id,
                        skill=row.key,
                        concept=source.concept,
                        difficulty=source.difficulty,
                        outcome=source.outcome,
                        occurred_at=source.occurred_at,
                        channel=source.kind,
                        eligible=True,
                    ),
                )
    history, history_count = await exposures(session, user.id)
    data = SelectionInput(
        candidates=tuple(
            Candidate(
                question_id=v.question_id,
                version_id=v.id,
                topic=v.category or "Uncategorized",
                concept=identities[v.question_id],
                skills=tuple(by_version.get(v.id, [])),
                difficulty=v.difficulty,
            )
            for v in versions
            if v.difficulty
        ),
        skills=tuple(
            SkillContext(
                key=row.key,
                importance=row.importance,
                need="practice"
                if row.action == "Practice"
                else "maintain"
                if row.action == "Maintain"
                else "unknown",
            )
            for row in matrix.rows
        ),
        performance=tuple(performance.values()),
        history=history,
        history_count=history_count,
        count=1,
        seed=str(interview.id),
    )
    snapshot: dict[str, object] = {
        "input": data.model_dump(mode="json"),
        "target_title": target_title,
    }
    if len(json.dumps(snapshot).encode()) > 2097152:
        conflict("interview_context_limit")
    interview.selection_context = snapshot
    session.add_all(
        [
            InterviewCandidate(
                owner_id=user.id,
                session_id=interview.id,
                question_id=v.question_id,
                question_version_id=v.id,
            )
            for v in versions
        ]
    )


def choose(
    interview: InterviewSession, turns: list[InterviewQuestion]
) -> tuple[UUID, dict[str, object]]:
    if interview.selection_context is None or interview.configuration is None:
        conflict("interview_state")
    context = interview.selection_context or {}
    frozen = SelectionInput.model_validate(context.get("input"))
    config = InterviewConfiguration.model_validate(interview.configuration)
    mains = [t for t in turns if t.parent_question_id is None]
    used = {t.stable_question_id for t in mains}
    remaining = tuple(c for c in frozen.candidates if c.question_id not in used)
    previous = [c.topic for c in frozen.candidates if c.question_id in used]
    slots = config.question_count - len(mains)
    # Select only candidates that leave the requested coverage feasible.
    viable = tuple(
        c
        for c in remaining
        if feasible(
            config.interview_type,
            previous + [c.topic] + [r.topic for r in remaining if r.question_id != c.question_id],
            config.question_count,
        )
        and _coverage_possible(
            config.interview_type,
            previous + [c.topic],
            [r.topic for r in remaining if r.question_id != c.question_id],
            slots - 1,
        )
    )
    if not viable or slots <= 0:
        conflict("interview_pool")
    lookup = {c.question_id: c for c in frozen.candidates}
    history = list(frozen.history)
    for turn in mains:
        c = lookup.get(turn.stable_question_id) if turn.stable_question_id else None
        if c:
            history.append(Exposure(question_id=c.question_id, topic=c.topic, concept=c.concept))
    selection = select_questions(
        frozen.model_copy(
            update={
                "candidates": viable,
                "history": tuple(history[-1000:]),
                "history_count": (frozen.history_count or len(frozen.history)) + len(mains),
                "seed": f"{interview.id}:{len(mains) + 1}",
            }
        )
    )
    if not selection.choices:
        conflict("interview_pool")
    return selection.choices[0].version_id, selection.model_dump(mode="json")


def _coverage_possible(
    type_: InterviewType, presented: list[str], remaining: list[str], slots: int
) -> bool:
    from interview_prep.modules.interviews.policy import family, required

    missing = required(type_) - set(presented)
    if not missing.issubset(remaining) or len(missing) > slots:
        return False
    if (
        type_ == InterviewType.MIXED
        and len(presented) + slots >= 2
        and len({family(c) for c in presented}) < 2
    ):
        return slots > 0 and any(family(c) != family(presented[0]) for c in remaining)
    return True
