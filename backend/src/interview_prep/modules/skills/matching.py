"""Finite lexical lookup only; matching never establishes a positive claim."""

import re
from dataclasses import dataclass

from interview_prep.modules.context.models import Skill, SkillAlias
from interview_prep.modules.resumes.extraction import VOCABULARY


@dataclass(frozen=True)
class SkillLabel:
    key: str
    name: str
    pattern: re.Pattern[str]


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def vocabulary(skills: list[Skill], aliases: list[SkillAlias]) -> list[SkillLabel]:
    labels: dict[str, SkillLabel] = {}
    names = {normalize(s.name): s for s in skills}
    alias_names = {normalize(a.alias): a.skill_id for a in aliases}
    by_id = {s.id: s for s in skills}
    for entries in VOCABULARY.values():
        for name, expression in entries:
            alias_id = alias_names.get(normalize(name))
            skill = names.get(normalize(name)) or (by_id.get(alias_id) if alias_id else None)
            key = str(skill.id) if skill else "label:" + normalize(name)
            labels[key] = SkillLabel(
                key,
                skill.name if skill else name,
                re.compile(r"(?<!\w)(?:" + expression + r")(?!\w)", re.I),
            )
    for skill in skills:
        expressions = [re.escape(skill.name)] + [
            re.escape(a.alias) for a in aliases if a.skill_id == skill.id
        ]
        previous = labels.get(str(skill.id))
        if previous:
            expressions.append(previous.pattern.pattern)
        labels[str(skill.id)] = SkillLabel(
            str(skill.id),
            skill.name,
            re.compile(r"(?<!\w)(?:" + "|".join(expressions) + r")(?!\w)", re.I),
        )
    return sorted(labels.values(), key=lambda label: label.key)


def matches(text: str, labels: list[SkillLabel]) -> list[SkillLabel]:
    return [label for label in labels if label.pattern.search(text)]


def profile_label(text: str, labels: list[SkillLabel]) -> SkillLabel:
    """A profile phrase is not split into inferred skills."""
    return next(
        (label for label in labels if label.pattern.fullmatch(text.strip())),
        SkillLabel("label:" + normalize(text), text, re.compile(re.escape(text), re.I)),
    )
