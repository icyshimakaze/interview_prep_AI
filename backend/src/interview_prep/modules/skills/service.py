from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.context.models import Skill, SkillAlias
from interview_prep.modules.identity.models import PrincipalKind, User
from interview_prep.modules.skills.context import INPUT_LIMIT, bounded, context_facts
from interview_prep.modules.skills.engine import build_matrix
from interview_prep.modules.skills.matching import vocabulary
from interview_prep.modules.skills.performance import performance_facts
from interview_prep.modules.skills.schemas import SkillMatrix


async def skill_matrix(
    session: AsyncSession,
    user: User,
    target_id: UUID | None,
) -> SkillMatrix:
    notices: list[str] = []
    skills = list(
        (await session.scalars(select(Skill).order_by(Skill.id).limit(INPUT_LIMIT + 1))).all()
    )
    aliases = list(
        (
            await session.scalars(select(SkillAlias).order_by(SkillAlias.id).limit(INPUT_LIMIT + 1))
        ).all()
    )
    labels = vocabulary(
        bounded(skills, notices, "Vocabulary"), bounded(aliases, notices, "Aliases")
    )
    facts, targets = await context_facts(session, user.id, target_id, labels, notices)
    facts.extend(await performance_facts(session, user.id, labels, notices))
    partial = any("results are partial" in note for note in notices)
    demo = user.kind == PrincipalKind.DEMO
    if partial or demo:
        facts = [
            fact.model_copy(update={"source": fact.source.model_copy(update={"eligible": False})})
            for fact in facts
        ]
    if partial:
        notices.append("Validation is withheld because this matrix has incomplete input.")
    if demo:
        notices.append("Fictional demo sources never validate real competence.")
    notices.extend(
        [
            "Resume mentions can be negative or aspirational. "
            "No resume evidence does not mean no skill.",
            "Required and Preferred use reviewed requirements. Raw job text is only Mentioned; "
            "lexical matching cannot interpret negation or all skill names.",
            "Results describe recorded, tested scope, not overall job readiness. "
            "Job requirement confirmation is not yet available; "
            "simulated/model-assisted interview feedback does not validate competence.",
        ]
    )
    return SkillMatrix(
        mode="demo" if demo else "account",
        target_id=target_id,
        targets=targets,
        rows=build_matrix(facts),
        notices=notices,
    )
