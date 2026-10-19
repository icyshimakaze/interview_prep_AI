"""Server-derived owned inputs. No answer text, prompt or resume enters the selector."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.adaptive.engine import select_questions
from interview_prep.modules.adaptive.schemas import (
    Candidate,
    Exposure,
    Performance,
    Selection,
    SelectionInput,
    SkillContext,
)
from interview_prep.modules.assessments.models import AssessmentQuestion
from interview_prep.modules.assessments.queries import pool
from interview_prep.modules.assessments.schemas import Configuration
from interview_prep.modules.identity.models import User
from interview_prep.modules.interviews.models import InterviewQuestion
from interview_prep.modules.questions.models import (
    PracticeAttempt,
    Question,
    QuestionSkill,
    QuestionVersion,
)
from interview_prep.modules.skills.service import skill_matrix

LIMIT = 1000


async def exposures(session: AsyncSession, owner: UUID) -> tuple[tuple[Exposure, ...], int]:
    # Allocations count even if abandoned/skipped. Bank attempts have no allocation
    # record, so only submitted bank practice can contribute to repetition history.
    queries = [
        select(
            model.question_version_id.label("version_id"),
            model.created_at.label("at"),
            model.id.label("id"),
            literal(channel).label("channel"),
            position.label("position"),
            group_id.label("group_id"),
        ).where(model.owner_id == owner, model.question_version_id.is_not(None))
        for model, channel, position, group_id in (
            (
                AssessmentQuestion,
                "assessment",
                AssessmentQuestion.position,
                AssessmentQuestion.assessment_id,
            ),
            (
                InterviewQuestion,
                "interview",
                InterviewQuestion.sequence,
                InterviewQuestion.session_id,
            ),
            (PracticeAttempt, "bank", literal(1), PracticeAttempt.id),
        )
    ]
    combined = queries[0].union_all(*queries[1:]).subquery()
    count = await session.scalar(select(func.count()).select_from(combined)) or 0
    rows = (
        await session.execute(
            select(
                QuestionVersion.question_id, QuestionVersion.category, Question.canonical_concept
            )
            .join(combined, combined.c.version_id == QuestionVersion.id)
            .join(Question, Question.id == QuestionVersion.question_id)
            .where((Question.owner_id == owner) | Question.owner_id.is_(None))
            .order_by(
                combined.c.at.desc(),
                combined.c.channel,
                combined.c.group_id.desc(),
                combined.c.position.desc(),
                combined.c.id.desc(),
            )
            .limit(LIMIT + 1)
        )
    ).all()
    return tuple(
        Exposure(question_id=q, topic=topic or "Uncategorized", concept=concept)
        for q, topic, concept in reversed(rows[:LIMIT])
    ), count


async def allocate(
    session: AsyncSession,
    owner: UUID,
    config: Configuration,
    seed: str,
) -> tuple[list[QuestionVersion], Selection]:
    user = await session.get(User, owner)
    if user is None:
        raise HTTPException(status_code=404)
    # This also validates selected target ownership before any content is allocated.
    matrix = await skill_matrix(session, user, config.target_id)
    if len(matrix.rows) > LIMIT:
        raise HTTPException(status_code=409, detail="adaptive_context_limit")
    versions = list(
        (
            await session.scalars(pool(owner, config).order_by(QuestionVersion.id).limit(LIMIT + 1))
        ).all()
    )
    if len(versions) > LIMIT:
        raise HTTPException(status_code=409, detail="adaptive_pool_limit")
    ids = [v.id for v in versions]
    mappings = (
        await session.execute(
            select(QuestionSkill.question_version_id, QuestionSkill.skill_id)
            .where(QuestionSkill.question_version_id.in_(ids))
            .order_by(QuestionSkill.question_version_id, QuestionSkill.skill_id)
            .limit(10001)
        )
    ).all()
    if len(mappings) > 10000:
        raise HTTPException(status_code=409, detail="adaptive_pool_limit")
    skills_by_version: dict[UUID, list[str]] = {}
    for version_id, skill_id in mappings:
        skills_by_version.setdefault(version_id, []).append(str(skill_id))
    if any(len(keys) > 100 for keys in skills_by_version.values()):
        raise HTTPException(status_code=409, detail="adaptive_pool_limit")
    concepts = dict(
        (
            await session.execute(
                select(Question.id, Question.canonical_concept)
                .where(Question.id.in_([v.question_id for v in versions]))
                .where((Question.owner_id == owner) | Question.owner_id.is_(None))
            )
        ).all()
    )
    candidates = tuple(
        Candidate(
            question_id=v.question_id,
            version_id=v.id,
            topic=v.category or "Uncategorized",
            concept=concepts[v.question_id],
            skills=tuple(skills_by_version.get(v.id, [])),
            difficulty=v.difficulty,
        )
        for v in versions
        if v.difficulty is not None
    )
    performance = tuple(
        Performance(
            id=source.id,
            skill=row.key,
            concept=source.concept,
            difficulty=source.difficulty,
            outcome=source.outcome,
            occurred_at=source.occurred_at,
            channel=source.kind,
            eligible=True,
        )
        for row in matrix.rows
        for source in row.sources
        if source.eligible
        and source.kind in ("assessment", "interview")
        and source.concept
        and source.difficulty
        and source.outcome
        and source.occurred_at
    )
    history, history_count = await exposures(session, owner)
    selected = select_questions(
        SelectionInput(
            candidates=candidates,
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
            performance=performance,
            history=history,
            history_count=history_count,
            count=config.question_count,
            seed=seed,
        )
    )
    notices = [
        "Selection uses editorial rules, not ML or a competence prediction.",
        "Performance uses eligible deterministic results only; "
        "simulation and self-review are excluded.",
        "History covers at most 1000 allocations/submitted bank responses; "
        "coverage uses the latest 20.",
    ]
    if config.difficulty:
        notices.append(
            "Explicit difficulty is an exact filter and overrides adaptive difficulty preference."
        )
    if history_count > LIMIT:
        notices.append("Older exposure history was omitted at the 1000-record limit.")
    notices.extend(
        note for note in matrix.notices if "partial" in note or "withheld" in note or "demo" in note
    )
    result = Selection(choices=selected.choices, notices=(*notices, *selected.notices))
    by_id = {v.id: v for v in versions}
    return [by_id[c.version_id] for c in result.choices], result
