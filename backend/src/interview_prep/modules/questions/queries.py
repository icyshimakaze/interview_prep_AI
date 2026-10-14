"""Database filters and stable pagination; public fields only before attempts."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.questions.history import attempted_ids, submitted_history
from interview_prep.modules.questions.models import (
    Bookmark,
    ExpectedConcept,
    PublicationStatus,
    Question,
    QuestionOption,
    QuestionRole,
    QuestionTag,
    QuestionVersion,
)
from interview_prep.modules.questions.schemas import (
    AttemptHistory,
    AttemptHistoryItem,
    BankDetail,
    BankFacets,
    BankFilters,
    BankOption,
    BankPage,
    BankQuestion,
)


def visible_versions(owner: UUID) -> Select[QuestionVersion]:
    latest = (
        select(
            QuestionVersion.question_id,
            func.max(QuestionVersion.version).label("version"),
        )
        .where(QuestionVersion.status != PublicationStatus.DRAFT)
        .group_by(QuestionVersion.question_id)
        .subquery()
    )
    return (
        select(QuestionVersion)
        .join(Question, Question.id == QuestionVersion.question_id)
        .join(
            latest,
            (latest.c.question_id == QuestionVersion.question_id)
            & (latest.c.version == QuestionVersion.version),
        )
        .where(
            (Question.owner_id == owner) | Question.owner_id.is_(None),
            QuestionVersion.category.is_not(None),
            QuestionVersion.subtopic.is_not(None),
            QuestionVersion.source_classification.is_not(None),
            QuestionVersion.prompt.is_not(None),
            QuestionVersion.difficulty.is_not(None),
            QuestionVersion.question_type.is_not(None),
            QuestionVersion.provenance_reviewed.is_(True),
            QuestionVersion.id.in_(select(ExpectedConcept.question_version_id)),
            QuestionVersion.id.in_(select(QuestionTag.question_version_id)),
            QuestionVersion.id.in_(select(QuestionRole.question_version_id)),
        )
    )


def bookmarked_ids(owner: UUID) -> Select[UUID]:
    return (
        select(QuestionVersion.question_id)
        .join(
            Bookmark,
            Bookmark.question_version_id == QuestionVersion.id,
        )
        .where(Bookmark.owner_id == owner)
        .distinct()
    )


def filtered(owner: UUID, filters: BankFilters) -> Select[QuestionVersion]:
    query = visible_versions(owner).where(
        QuestionVersion.status
        == (PublicationStatus.PUBLISHED if filters.active else PublicationStatus.RETIRED)
    )
    for column, value in [
        (QuestionVersion.category, filters.category),
        (QuestionVersion.subtopic, filters.subtopic),
        (QuestionVersion.difficulty, filters.difficulty),
        (QuestionVersion.question_type, filters.question_type),
    ]:
        if value is not None:
            query = query.where(column == value)
    if filters.role:
        query = query.where(
            QuestionVersion.id.in_(
                select(QuestionRole.question_version_id).where(
                    QuestionRole.label == filters.role,
                )
            )
        )
    if filters.search:
        phrase = filters.search.casefold()
        query = query.where(
            or_(
                *(
                    func.lower(column).contains(phrase, autoescape=True)
                    for column in (
                        QuestionVersion.title,
                        QuestionVersion.prompt,
                        QuestionVersion.category,
                        QuestionVersion.subtopic,
                    )
                ),
                QuestionVersion.id.in_(
                    select(QuestionTag.question_version_id).where(
                        func.lower(QuestionTag.label).contains(phrase, autoescape=True)
                    )
                ),
            )
        )
    for wanted, ids in [
        (filters.bookmarked, bookmarked_ids(owner)),
        (filters.attempted, attempted_ids(owner)),
    ]:
        if wanted is not None:
            condition = QuestionVersion.question_id.in_(ids)
            query = query.where(condition if wanted else ~condition)
    return query


async def summarize(
    session: AsyncSession, owner: UUID, versions: list[QuestionVersion]
) -> list[BankQuestion]:
    ids = [v.id for v in versions]
    question_ids = [v.question_id for v in versions]
    tags = (
        await session.execute(
            select(QuestionTag.question_version_id, QuestionTag.label)
            .where(
                QuestionTag.question_version_id.in_(ids),
            )
            .order_by(QuestionTag.label)
        )
    ).all()
    roles = (
        await session.execute(
            select(QuestionRole.question_version_id, QuestionRole.label)
            .where(
                QuestionRole.question_version_id.in_(ids),
            )
            .order_by(QuestionRole.label)
        )
    ).all()
    bookmarked = set(
        (
            await session.scalars(
                bookmarked_ids(owner).where(QuestionVersion.question_id.in_(question_ids))
            )
        ).all()
    )
    attempted = set(
        (
            await session.scalars(
                attempted_ids(owner).where(QuestionVersion.question_id.in_(question_ids))
            )
        ).all()
    )
    result: list[BankQuestion] = []
    for version in versions:
        if (
            version.category is None
            or version.subtopic is None
            or version.difficulty is None
            or version.question_type is None
            or version.source_classification is None
        ):
            raise HTTPException(status_code=404)
        result.append(
            BankQuestion(
                id=version.question_id,
                version_id=version.id,
                version=version.version,
                title=version.title,
                category=version.category,
                subtopic=version.subtopic,
                difficulty=version.difficulty,
                question_type=version.question_type,
                tags=[label for id, label in tags if id == version.id],
                roles=[label for id, label in roles if id == version.id],
                source_classification=version.source_classification,
                active=version.status == PublicationStatus.PUBLISHED,
                bookmarked=version.question_id in bookmarked,
                attempted=version.question_id in attempted,
            )
        )
    return result


async def list_questions(session: AsyncSession, owner: UUID, filters: BankFilters) -> BankPage:
    query = filtered(owner, filters)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    versions = list(
        (
            await session.scalars(
                query.order_by(QuestionVersion.title, QuestionVersion.question_id)
                .offset(filters.offset)
                .limit(filters.limit)
            )
        ).all()
    )
    return BankPage(
        items=await summarize(session, owner, versions),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


async def facets(session: AsyncSession, owner: UUID) -> BankFacets:
    active = (
        visible_versions(owner)
        .where(QuestionVersion.status == PublicationStatus.PUBLISHED)
        .subquery()
    )
    categories = list(
        (
            await session.scalars(
                select(active.c.category).distinct().order_by(active.c.category).limit(100)
            )
        ).all()
    )
    subtopics = list(
        (
            await session.scalars(
                select(active.c.subtopic).distinct().order_by(active.c.subtopic).limit(200)
            )
        ).all()
    )
    roles = list(
        (
            await session.scalars(
                select(QuestionRole.label)
                .join(
                    active,
                    active.c.id == QuestionRole.question_version_id,
                )
                .distinct()
                .order_by(QuestionRole.label)
                .limit(100)
            )
        ).all()
    )
    return BankFacets(categories=categories, subtopics=subtopics, roles=roles)


async def current_question(
    session: AsyncSession, owner: UUID, question_id: UUID
) -> QuestionVersion:
    version = await session.scalar(
        visible_versions(owner).where(QuestionVersion.question_id == question_id)
    )
    if version is None:
        raise HTTPException(status_code=404)
    return version


async def detail(session: AsyncSession, owner: UUID, question_id: UUID) -> BankDetail:
    version = await current_question(session, owner, question_id)
    history = submitted_history(owner)
    unlocked = bool(
        await session.scalar(
            select(history.c.id).where(history.c.question_version_id == version.id).limit(1)
        )
    )
    concepts = (
        list(
            (
                await session.scalars(
                    select(ExpectedConcept.text)
                    .where(
                        ExpectedConcept.question_version_id == version.id,
                    )
                    .order_by(ExpectedConcept.position)
                    .limit(12)
                )
            ).all()
        )
        if unlocked
        else None
    )
    options = list(
        (
            await session.scalars(
                select(QuestionOption)
                .where(
                    QuestionOption.question_version_id == version.id,
                )
                .order_by(QuestionOption.position)
                .limit(20)
            )
        ).all()
    )
    summary = (await summarize(session, owner, [version]))[0]
    return BankDetail(
        **summary.model_dump(),
        prompt=version.prompt or "",
        concepts_unlocked=unlocked,
        expected_concepts=concepts,
        options=[BankOption(id=o.id, text=o.text) for o in options],
        source_file=version.source_file,
        original_topic=version.original_topic,
    )


async def history_page(
    session: AsyncSession, owner: UUID, question_id: UUID, offset: int, limit: int
) -> AttemptHistory:
    await current_question(session, owner, question_id)
    history = submitted_history(owner)
    query = (
        select(history)
        .join(QuestionVersion, QuestionVersion.id == history.c.question_version_id)
        .where(
            QuestionVersion.question_id == question_id,
        )
    )
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = (
        (
            await session.execute(
                query.order_by(history.c.submitted_at.desc(), history.c.id)
                .offset(offset)
                .limit(limit)
            )
        )
        .mappings()
        .all()
    )
    return AttemptHistory(
        items=[AttemptHistoryItem.model_validate(row) for row in rows],
        total=total,
        offset=offset,
        limit=limit,
    )
