"""Authored practice templates grounded in cited static clues, never competence claims."""

from dataclasses import dataclass

from interview_prep.modules.projects.schemas import StaticAnalysis, StaticFact


@dataclass(frozen=True)
class Prompt:
    focus: str
    text: str
    fact: StaticFact


def questions(analysis: StaticAnalysis) -> list[Prompt]:
    first = analysis.files[0]
    fallback = StaticFact(
        path=first.path,
        kind="component",
        description="Source file present; role has not been established.",
        line=1,
        inferred=False,
    )
    templates = [
        (
            "Framework choice",
            ("framework", "manifest"),
            "Why did you choose this framework or toolchain? Explain one alternative and the "
            "constraints that influenced you.",
        ),
        (
            "Architecture",
            ("component", "route"),
            "Explain the project's architecture and trace one request or user action through "
            "it. Which static assumptions below would you correct?",
        ),
        (
            "Authentication",
            ("authentication", "route"),
            "How does authentication work, if applicable? Distinguish identity, authorization "
            "and session handling. If this project has none, explain that boundary and when "
            "you would add it.",
        ),
        (
            "Persistence",
            ("database", "schema"),
            "How is data persisted, if at all? Explain the data model, validation, migrations "
            "and recovery. Distinguish configured technology from what actually runs.",
        ),
        (
            "Scale and failure",
            ("route", "component"),
            "What would fail first under increased scale? Explain a likely bottleneck, the "
            "evidence you would collect and one bounded improvement.",
        ),
        (
            "Security boundaries",
            ("authentication", "docker", "route"),
            "Where are this project's security boundaries? Trace untrusted input to "
            "authorization, validation and persistence. What would you test to challenge your "
            "assumptions?",
        ),
        (
            "Testing",
            ("tests", "ci", "schema"),
            "How would you test this component? Describe a unit test, an integration boundary "
            "and a failure case. Existing test files are not evidence that tests passed.",
        ),
        (
            "Dependency trade-offs",
            ("dependency", "manifest"),
            "What trade-off does this dependency or tool introduce? Discuss maintenance, "
            "failure modes and what replacing it would cost.",
        ),
        (
            "Ownership and AI assistance",
            ("documentation", "component"),
            "Which parts did you build yourself, with teammates, or with AI assistance? "
            "Explain how you reviewed, tested and corrected generated code. Do not invent "
            "contributions or outcomes.",
        ),
        (
            "Change and reflection",
            ("schema", "docker", "documentation"),
            "Walk through a change you understand in this project. What would you modify, "
            "which components would be affected, and how would you verify and roll it back?",
        ),
    ]
    result = []
    for focus, kinds, text in templates:
        fact = next((f for kind in kinds for f in analysis.facts if f.kind == kind), fallback)
        result.append(Prompt(focus, text, fact))
    return result
