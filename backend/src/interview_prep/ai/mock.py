"""Deterministic local simulations. No model, credentials, clock, randomness or HTTP."""

import re
from typing import Literal

from interview_prep.ai.provider import BaseProvider
from interview_prep.ai.rubric import dimensions
from interview_prep.ai.schemas import (
    AnswerEvaluation,
    AnswerInput,
    Contract,
    Followup,
    FollowupInput,
    Input,
    JobAnalysis,
    JobInput,
    JobRequirement,
    Operation,
    ProjectInput,
    ProjectQuestion,
    ProjectQuestions,
    ResumeAnalysis,
    ResumeInput,
    Roadmap,
    RoadmapInput,
    RoadmapStep,
    RubricResult,
    SkillMention,
)

VOCABULARY = (
    "Python",
    "SQL",
    "JavaScript",
    "TypeScript",
    "Java",
    "React",
    "PostgreSQL",
    "Docker",
    "Kubernetes",
    "Git",
    "FastAPI",
    "Testing",
    "CI/CD",
    "REST",
    "AWS",
)


def mentions(text: str) -> list[SkillMention]:
    result: list[SkillMention] = []
    for name in VOCABULARY:
        match = re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.IGNORECASE)
        if match:
            result.append(
                SkillMention(
                    name=name,
                    evidence=match.group(),
                    start=match.start(),
                    end=match.end(),
                )
            )
    return result


def evaluate(content: AnswerInput) -> AnswerEvaluation:
    response_words = set(re.findall(r"[a-z0-9]+", content.answer.casefold()))
    matched: list[str] = []
    for concept in content.expected_concepts:
        words = {w for w in re.findall(r"[a-z0-9]+", concept.casefold()) if len(w) >= 4}
        if words and 2 * len(words & response_words) >= len(words):
            matched.append(concept)
    feedback = (
        f"Mock simulation: lexical overlap with {len(matched)} of "
        f"{len(content.expected_concepts)} expected concepts. "
        "This does not judge correctness, reasoning, or demonstrated competence. "
        "Compare your response with the review concepts and practice explaining them."
    )
    score = 4 * len(matched) // max(1, len(content.expected_concepts))
    missing = [c for c in content.expected_concepts if c not in matched]
    return AnswerEvaluation(
        rubric_version="answer-rubric-v1",
        profile=content.profile,
        score_basis="lexical_coverage",
        score=score,
        matched_concepts=matched,
        feedback=feedback,
        overall_feedback=feedback,
        strengths=[
            f"Literal word overlap found for {len(matched)} review concepts; verify meaning."
        ]
        if matched
        else [],
        improvements=[
            "Explain the missing review concepts in your own words and check factual accuracy."
            if missing
            else "Check each claim and add a concrete example; word overlap is not proof.",
            "Use the suggested structure to review your response with a human reviewer.",
        ],
        missing_concepts=missing,
        recommended_answer_structure=(
            [
                "Situation: give relevant context.",
                "Task: state your responsibility.",
                "Action: describe what you personally did and why.",
                "Result: describe supported outcomes without inventing metrics.",
                "Reflection: explain what you learned and would change.",
            ]
            if content.profile == "behavioral"
            else [
                "Answer the question directly and define key terms.",
                "Explain the reasoning with a concrete example.",
                "Discuss limitations and trade-offs; include complexity only when relevant.",
                "Summarize the conclusion and how you would verify it.",
            ]
        ),
        potential_followup=(
            "What would you do differently next time, and why?"
            if content.profile == "behavioral"
            else "Which assumption in your answer would you test first, and how?"
        ),
        rubric_results=[
            RubricResult(
                dimension=dimension,
                score=score if dimension == "completeness" and content.expected_concepts else None,
                explanation=(
                    f"Simulation proxy only: {len(matched)}/{len(content.expected_concepts)} "
                    "concepts have lexical overlap; floor(4 × matched / expected). "
                    "This does not establish semantic completeness."
                    if dimension == "completeness" and content.expected_concepts
                    else "Not assessed: deterministic mock cannot judge this criterion. "
                    "Review it using the documented rubric."
                ),
            )
            for dimension in dimensions(content.profile)
        ],
    )


class MockAIProvider(BaseProvider):
    name = "MockAIProvider"
    version = "mock-structured-v2"
    kind: Literal["simulation", "model_assisted"] = "simulation"
    timeout_seconds = 5.0

    async def _generate(self, operation: Operation, content: Input, schema: type[Contract]) -> str:
        output: Contract
        if isinstance(content, ResumeInput):
            skills = mentions(content.text)
            output = ResumeAnalysis(
                summary=f"Demo simulation: {len(skills)} vocabulary skill mentions found; "
                "mentions are unverified claims, not evidence of proficiency.",
                skills=skills,
                suggestions=[
                    "Tie each claimed skill to a specific project contribution you can explain.",
                    "Describe decisions, tests and tradeoffs; only cite documented outcomes.",
                    "Review extracted mentions for negation, aspirations and missing skills.",
                ],
            )
        elif isinstance(content, JobInput):
            output = JobAnalysis(
                summary="Demo simulation: literal skill mentions for human requirement review.",
                requirements=[
                    JobRequirement(**m.model_dump(), importance="mentioned")
                    for m in mentions(content.text)
                ],
                review_notes=[
                    "Simulation cannot interpret negation, seniority or requirement priority.",
                    "Confirm each requirement against the job description before prioritizing it.",
                ],
            )
        elif isinstance(content, FollowupInput):
            used = {q.strip().casefold() for q in [content.question, *content.recent_questions]}
            prompts = [
                "Which assumption in your answer would you test first, and how?",
                "What tradeoff would change your proposed solution?",
                "How would your approach behave with missing or malformed input?",
            ] + [
                f"Describe test case {i} that could disprove your approach and its expected result."
                for i in range(1, 22)
            ]
            output = Followup(
                question=next(q for q in prompts if q.casefold() not in used),
                rationale="Demo simulation: probe reasoning with a deterministic practice prompt; "
                "this is not an assessment of your answer.",
            )
        elif isinstance(content, AnswerInput):
            output = evaluate(content)
        elif isinstance(content, RoadmapInput):
            minutes = content.weekly_minutes // len(content.topics)
            output = Roadmap(
                summary="Demo simulation: practice blocks for requested topics within your budget.",
                steps=[
                    RoadmapStep(
                        topic=topic,
                        minutes=minutes,
                        activity=f"Review {topic}, solve an example, and explain your reasoning.",
                        success_check="Record your explanation; test normal and failure cases.",
                    )
                    for topic in content.topics
                ],
            )
        elif isinstance(content, ProjectInput):
            project_prompts = [
                (
                    "Ownership",
                    "Which part of this project did you implement, and how can you demonstrate it?",
                ),
                ("Design", "Which design decision in this project involved the largest tradeoff?"),
                ("Testing", "How would you test a failure path in the described project?"),
                (
                    "Security",
                    "Where does this project validate input and enforce access boundaries?",
                ),
                (
                    "Operations",
                    "How would you diagnose and recover from a failed deployment of this project?",
                ),
                (
                    "Evolution",
                    "What would you change first if this project's usage increased, and why?",
                ),
            ]
            output = ProjectQuestions(
                questions=[
                    ProjectQuestion(
                        question=q,
                        focus=focus,
                        evidence=content.text.strip()[:200],
                    )
                    for focus, q in project_prompts[: content.question_count]
                ]
            )
        else:
            raise ValueError("Unsupported AI input")
        return output.model_dump_json()
