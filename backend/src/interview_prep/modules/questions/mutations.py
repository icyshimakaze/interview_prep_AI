from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.identity.models import PrincipalKind, User
from interview_prep.modules.questions.models import (
    Bookmark,
    PracticeAttempt,
    PublicationStatus,
    QuestionVersion,
)
from interview_prep.modules.questions.queries import bookmarked_ids, current_question
from interview_prep.modules.questions.schemas import BookmarkState, PracticeInput, PracticeView

MAX_BOOKMARKS = 500
MAX_PRACTICE_ATTEMPTS = 1000


async def lock_owner(session: AsyncSession, owner: UUID) -> None:
    if await session.scalar(select(User.id).where(User.id == owner).with_for_update()) is None:
        raise HTTPException(status_code=401)


async def set_bookmark(
    session: AsyncSession, owner: UUID, question_id: UUID, saved: bool
) -> BookmarkState:
    await lock_owner(session, owner)
    version = await current_question(session, owner, question_id)
    existing = await session.scalar(
        bookmarked_ids(owner).where(QuestionVersion.question_id == question_id)
    )
    if saved and existing is None:
        if version.status != PublicationStatus.PUBLISHED:
            raise HTTPException(status_code=409, detail="question_changed")
        count = (
            await session.scalar(
                select(func.count()).select_from(Bookmark).where(Bookmark.owner_id == owner)
            )
            or 0
        )
        if count >= MAX_BOOKMARKS:
            raise HTTPException(status_code=409, detail="bookmark_limit")
        session.add(Bookmark(owner_id=owner, question_version_id=version.id))
    elif not saved:
        await session.execute(
            delete(Bookmark).where(
                Bookmark.owner_id == owner,
                Bookmark.question_version_id.in_(
                    select(QuestionVersion.id).where(QuestionVersion.question_id == question_id)
                ),
            )
        )
    await session.commit()
    return BookmarkState(bookmarked=saved)


async def submit_practice(
    session: AsyncSession, user: User, question_id: UUID, body: PracticeInput
) -> PracticeView:
    await lock_owner(session, user.id)
    previous = await session.scalar(
        select(PracticeAttempt).where(
            PracticeAttempt.owner_id == user.id,
            PracticeAttempt.submission_key == body.submission_key,
        )
    )
    if previous:
        previous_question_id = await session.scalar(
            select(QuestionVersion.question_id).where(
                QuestionVersion.id == previous.question_version_id
            )
        )
        if (
            previous.question_version_id != body.question_version_id
            or previous_question_id != question_id
            or previous.answer_text != body.answer_text
        ):
            raise HTTPException(status_code=409, detail="submission_conflict")
        return PracticeView.model_validate(previous)
    version = await current_question(session, user.id, question_id)
    if version.id != body.question_version_id or version.status != PublicationStatus.PUBLISHED:
        raise HTTPException(status_code=409, detail="question_changed")
    count = (
        await session.scalar(
            select(func.count())
            .select_from(PracticeAttempt)
            .where(PracticeAttempt.owner_id == user.id)
        )
        or 0
    )
    if count >= MAX_PRACTICE_ATTEMPTS:
        raise HTTPException(status_code=409, detail="practice_limit")
    attempt = PracticeAttempt(
        owner_id=user.id,
        question_version_id=version.id,
        submission_key=body.submission_key,
        answer_text=body.answer_text,
        submitted_at=datetime.now(UTC),
        result_kind="simulation" if user.kind == PrincipalKind.DEMO else "self_review",
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return PracticeView.model_validate(attempt)


async def remove_practice(
    session: AsyncSession, owner: UUID, question_id: UUID, attempt_id: UUID
) -> None:
    await lock_owner(session, owner)
    await current_question(session, owner, question_id)
    attempt = await session.scalar(
        select(PracticeAttempt)
        .join(
            QuestionVersion,
            QuestionVersion.id == PracticeAttempt.question_version_id,
        )
        .where(
            PracticeAttempt.owner_id == owner,
            PracticeAttempt.id == attempt_id,
            QuestionVersion.question_id == question_id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404)
    await session.delete(attempt)
    await session.commit()
