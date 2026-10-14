"""Owned current context; no text is executed or sent to an external service."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.context.models import (
    EvidenceOrigin,
    JobSkillRequirement,
    RequirementPriority,
    ResumeSkillEvidence,
    ResumeVersion,
    ReviewStatus,
    TargetJob,
    TargetJobVersion,
)
from interview_prep.modules.identity.models import ProfileInterest
from interview_prep.modules.skills.matching import SkillLabel, matches, profile_label
from interview_prep.modules.skills.schemas import EvidenceSource, SkillFact, SkillTarget

INPUT_LIMIT = 1000


def bounded[T](items: list[T], notices: list[str], source: str) -> list[T]:
    if len(items) > INPUT_LIMIT:
        notices.append(f"{source} exceeds the {INPUT_LIMIT}-record limit; results are partial.")
    return items[:INPUT_LIMIT]


async def context_facts(
    session: AsyncSession,
    owner: UUID,
    target_id: UUID | None,
    labels: list[SkillLabel],
    notices: list[str],
) -> tuple[list[SkillFact], list[SkillTarget]]:
    facts: list[SkillFact] = []
    targets = list(
        (
            await session.scalars(
                select(TargetJob)
                .where(TargetJob.owner_id == owner)
                .order_by(TargetJob.title, TargetJob.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    choices = [SkillTarget(id=t.id, title=t.title) for t in bounded(targets, notices, "Targets")]
    if target_id is not None:
        target = await session.scalar(
            select(TargetJob).where(TargetJob.id == target_id, TargetJob.owner_id == owner)
        )
        if target is None:
            raise HTTPException(status_code=404)
        version = await session.scalar(
            select(TargetJobVersion)
            .where(TargetJobVersion.target_job_id == target_id, TargetJobVersion.owner_id == owner)
            .order_by(TargetJobVersion.version.desc())
            .limit(1)
        )
        if version:
            requirements = list(
                (
                    await session.scalars(
                        select(JobSkillRequirement)
                        .where(
                            JobSkillRequirement.owner_id == owner,
                            JobSkillRequirement.target_job_version_id == version.id,
                        )
                        .order_by(JobSkillRequirement.id)
                        .limit(INPUT_LIMIT + 1)
                    )
                ).all()
            )
            reviewed: set[str] = set()
            by_key = {label.key: label for label in labels}
            for requirement in bounded(requirements, notices, "Requirements"):
                label = by_key.get(str(requirement.skill_id))
                if label is None:
                    continue
                if requirement.review_status == ReviewStatus.REJECTED:
                    reviewed.add(label.key)
                    continue
                confirmed = requirement.review_status == ReviewStatus.CONFIRMED
                if confirmed:
                    reviewed.add(label.key)
                facts.append(
                    SkillFact(
                        key=label.key,
                        name=label.name,
                        source=EvidenceSource(
                            id=f"requirement:{requirement.id}",
                            kind="job",
                            detail=requirement.source_excerpt,
                            review=(
                                f"{requirement.review_status.value}; job version {version.version}"
                            ),
                            importance=(
                                "Required"
                                if requirement.priority == RequirementPriority.ESSENTIAL
                                else "Preferred"
                            )
                            if confirmed
                            else "Mentioned",
                        ),
                    )
                )
            for label in matches(version.description, labels):
                if label.key in reviewed:
                    continue
                match = label.pattern.search(version.description)
                if match is None:
                    continue
                start = max(0, match.start() - 100)
                facts.append(
                    SkillFact(
                        key=label.key,
                        name=label.name,
                        source=EvidenceSource(
                            id=f"job:{version.id}:{label.key}",
                            kind="job",
                            detail=version.description[start : match.end() + 100],
                            review=f"Unreviewed lexical mention; job version {version.version}",
                            importance="Mentioned",
                        ),
                    )
                )
    else:
        notices.append("No target selected. Low relevance means no selected job evidence.")

    interests = list(
        (
            await session.scalars(
                select(ProfileInterest)
                .where(ProfileInterest.owner_id == owner)
                .order_by(ProfileInterest.position)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    for interest in bounded(interests, notices, "Profile labels"):
        label = profile_label(interest.label, labels)
        facts.append(
            SkillFact(
                key=label.key,
                name=label.name,
                source=EvidenceSource(
                    id=f"profile:{interest.id}",
                    kind="profile",
                    detail=interest.label,
                    review="Self-reported interest; not competence evidence",
                ),
            )
        )

    latest = (
        select(ResumeVersion.resume_id, func.max(ResumeVersion.version).label("version"))
        .where(ResumeVersion.owner_id == owner)
        .group_by(ResumeVersion.resume_id)
        .subquery()
    )
    evidence = list(
        (
            await session.scalars(
                select(ResumeSkillEvidence)
                .join(ResumeVersion, ResumeVersion.id == ResumeSkillEvidence.resume_version_id)
                .join(
                    latest,
                    (latest.c.resume_id == ResumeVersion.resume_id)
                    & (latest.c.version == ResumeVersion.version),
                )
                .where(
                    ResumeSkillEvidence.owner_id == owner,
                    ResumeVersion.owner_id == owner,
                    ResumeSkillEvidence.review_status != ReviewStatus.REJECTED,
                )
                .order_by(ResumeSkillEvidence.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    by_key = {label.key: label for label in labels}
    for evidence_item in bounded(evidence, notices, "Resume evidence"):
        # Corrections replace matching text; original excerpts remain visible for provenance.
        text = evidence_item.user_correction or evidence_item.claim
        matching_text = evidence_item.user_correction or (
            evidence_item.claim + " " + (evidence_item.source_excerpt or "")
        )
        linked = by_key.get(str(evidence_item.skill_id))
        found = (
            [linked]
            if linked and evidence_item.user_correction is None
            else matches(matching_text, labels)
        )
        for label in found:
            detail = text
            if evidence_item.source_excerpt:
                detail += f" | Original excerpt: {evidence_item.source_excerpt}"
            facts.append(
                SkillFact(
                    key=label.key,
                    name=label.name,
                    source=EvidenceSource(
                        id=f"resume-evidence:{evidence_item.id}",
                        kind="resume" if evidence_item.origin == EvidenceOrigin.RESUME else "user",
                        detail=detail,
                        review=(
                            f"{evidence_item.review_status.value}; resume version "
                            f"{evidence_item.resume_version_id}; "
                            f"page {evidence_item.source_page or 'n/a'}; "
                            "a mention may be negative or aspirational"
                        ),
                    ),
                )
            )
    return facts, choices
