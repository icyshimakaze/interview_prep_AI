from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.projects import service
from interview_prep.modules.projects.defense_models import DefenseAnswer, DefenseRun
from interview_prep.modules.projects.models import ProjectAnalysis
from interview_prep.modules.projects.schemas import (
    DefenseCommand,
    DefenseHistory,
    DefenseResponse,
    DefenseView,
    StartDefense,
)


async def owned_run(
    session: AsyncSession, owner: UUID, identifier: UUID, lock: bool = False
) -> DefenseRun:
    query = select(DefenseRun).where(DefenseRun.owner_id == owner, DefenseRun.id == identifier)
    run = await session.scalar(
        query.with_for_update().execution_options(populate_existing=True) if lock else query
    )
    if run is None:
        raise HTTPException(404)
    return run


async def view(session: AsyncSession, owner: UUID, identifier: UUID) -> DefenseView:
    run = await owned_run(session, owner, identifier)
    analysis = await session.scalar(
        select(ProjectAnalysis).where(
            ProjectAnalysis.id == run.analysis_id, ProjectAnalysis.owner_id == owner
        )
    )
    if analysis is None:
        raise HTTPException(404)
    prompts = {q.id: q for q in await service.prompts(session, owner, run.analysis_id)}
    answers = (
        await session.scalars(
            select(DefenseAnswer)
            .where(DefenseAnswer.owner_id == owner, DefenseAnswer.run_id == run.id)
            .order_by(DefenseAnswer.position)
        )
    ).all()
    return DefenseView(
        id=run.id,
        project_id=analysis.repository_id,
        revision=run.revision,
        status=run.status,
        current_position=run.current_position,
        created_at=run.created_at,
        completed_at=run.completed_at,
        responses=[
            DefenseResponse(
                question=prompts[a.question_id],
                position=a.position,
                answer_text=a.answer_text,
                status=a.status,
                submitted_at=a.submitted_at,
            )
            for a in answers
        ],
    )


async def history(session: AsyncSession, owner: UUID, project: UUID) -> DefenseHistory:
    _, analysis = await service.owned(session, owner, project)
    ids = (
        await session.scalars(
            select(DefenseRun.id)
            .where(DefenseRun.owner_id == owner, DefenseRun.analysis_id == analysis.id)
            .order_by(DefenseRun.created_at.desc(), DefenseRun.id)
            .limit(20)
        )
    ).all()
    return DefenseHistory(items=[await view(session, owner, identifier) for identifier in ids])


async def start(
    session: AsyncSession, owner: UUID, project: UUID, body: StartDefense
) -> DefenseView:
    await service.lock_owner(session, owner)
    _, analysis = await service.owned(session, owner, project)
    existing = await session.scalar(
        select(DefenseRun).where(
            DefenseRun.owner_id == owner, DefenseRun.command_key == body.command_key
        )
    )
    if existing:
        if existing.analysis_id != analysis.id or existing.question_count != body.question_count:
            raise HTTPException(409, detail="defense_state")
        return await view(session, owner, existing.id)
    count = await session.scalar(
        select(func.count())
        .select_from(DefenseRun)
        .where(DefenseRun.owner_id == owner, DefenseRun.analysis_id == analysis.id)
    )
    if count and count >= 20:
        raise HTTPException(409, detail="defense_limit")
    prompts = await service.prompts(session, owner, analysis.id)
    if len(prompts) < body.question_count:
        raise HTTPException(409, detail="defense_state")
    run = DefenseRun(
        owner_id=owner,
        analysis_id=analysis.id,
        command_key=body.command_key,
        status="active",
        question_count=body.question_count,
        current_position=1,
        revision=1,
    )
    session.add(run)
    await session.flush()
    session.add_all(
        [
            DefenseAnswer(
                owner_id=owner,
                run_id=run.id,
                analysis_id=analysis.id,
                question_id=q.id,
                position=i,
                status="draft",
            )
            for i, q in enumerate(prompts[: body.question_count], 1)
        ]
    )
    await session.commit()
    return await view(session, owner, run.id)


async def command(
    session: AsyncSession, owner: UUID, identifier: UUID, body: DefenseCommand
) -> DefenseView:
    await service.lock_owner(session, owner)
    run = await owned_run(session, owner, identifier, lock=True)
    if run.revision != body.revision or run.status == "completed":
        raise HTTPException(409, detail="defense_state")
    if body.answer_text is not None and (
        "\x00" in body.answer_text or any(0xD800 <= ord(c) <= 0xDFFF for c in body.answer_text)
    ):
        raise HTTPException(422)
    if body.action == "resume":
        if run.status != "paused" or body.answer_text is not None:
            raise HTTPException(409, detail="defense_state")
        run.status = "active"
    else:
        if run.status != "active" and not (body.action == "end" and body.answer_text is None):
            raise HTTPException(409, detail="defense_state")
        answer = await session.scalar(
            select(DefenseAnswer).where(
                DefenseAnswer.owner_id == owner,
                DefenseAnswer.run_id == identifier,
                DefenseAnswer.position == run.current_position,
            )
        )
        if answer is None or answer.status != "draft":
            raise HTTPException(409, detail="defense_state")
        if body.answer_text is not None:
            answer.answer_text = body.answer_text
        if body.action in {"submit", "skip"}:
            if body.action == "submit" and not (answer.answer_text or "").strip():
                raise HTTPException(422)
            answer.status = "submitted" if body.action == "submit" else "skipped"
            answer.submitted_at = datetime.now(UTC)
        await session.flush()  # Answer guard observes the current pre-transition run.
        if body.action in {"submit", "skip"}:
            run.current_position += 1
        if body.action == "pause":
            run.status = "paused"
        if body.action == "end" or run.current_position > run.question_count:
            run.status, run.completed_at = "completed", datetime.now(UTC)
    run.revision += 1
    await session.commit()
    return await view(session, owner, identifier)
