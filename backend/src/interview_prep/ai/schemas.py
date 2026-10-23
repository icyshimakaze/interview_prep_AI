"""Bounded contracts shared by all providers; provider identity is never model output."""

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from interview_prep.ai.rubric import Dimension, Profile, dimensions

Text = Annotated[str, StringConstraints(min_length=1, max_length=4000, pattern=r"\S")]
Label = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"\S")]
Concept = Annotated[str, StringConstraints(min_length=1, max_length=1000, pattern=r"\S")]
Document = Annotated[str, StringConstraints(min_length=1, max_length=50000, pattern=r"\S")]
QuestionText = Annotated[str, StringConstraints(min_length=1, max_length=30000, pattern=r"\S")]
AnswerText = Annotated[str, StringConstraints(min_length=1, max_length=10000, pattern=r"\S")]
Operation = Literal[
    "analyze_resume",
    "analyze_job_description",
    "evaluate_answer",
    "generate_followup",
    "recommend_roadmap",
    "generate_project_questions",
]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
    )


class ResumeInput(Contract):
    text: Document


class JobInput(Contract):
    text: Document


class AnswerInput(Contract):
    question: QuestionText
    answer: AnswerText
    expected_concepts: list[Concept] = Field(default_factory=list, max_length=12)
    rubric: list[Concept] = Field(default_factory=list, max_length=12)
    profile: Profile = "general"

    @model_validator(mode="after")
    def unique_concepts(self) -> "AnswerInput":
        if len(set(self.expected_concepts)) != len(self.expected_concepts):
            raise ValueError("Expected concepts must be unique")
        return self


class FollowupInput(AnswerInput):
    recent_questions: list[QuestionText] = Field(default_factory=list, max_length=20)


class RoadmapInput(Contract):
    topics: list[Label] = Field(min_length=1, max_length=6)
    weekly_minutes: int = Field(ge=15, le=600)
    context: Document | None = None

    @model_validator(mode="after")
    def unique_topics(self) -> "RoadmapInput":
        if len({t.casefold() for t in self.topics}) != len(self.topics):
            raise ValueError("Topics must be unique")
        return self


class ProjectInput(Contract):
    text: Document
    question_count: int = Field(default=3, ge=1, le=6)


class SkillMention(Contract):
    name: Label
    evidence: Concept
    start: int = Field(ge=0, le=50000)
    end: int = Field(ge=1, le=50000)


class JobRequirement(SkillMention):
    importance: Literal["required", "preferred", "mentioned"]


class ResumeAnalysis(Contract):
    summary: Text
    skills: list[SkillMention] = Field(max_length=30)
    suggestions: list[Text] = Field(min_length=1, max_length=6)


class JobAnalysis(Contract):
    summary: Text
    requirements: list[JobRequirement] = Field(max_length=30)
    review_notes: list[Text] = Field(min_length=1, max_length=6)


CoachingText = Annotated[str, StringConstraints(min_length=1, max_length=600, pattern=r"\S")]


class RubricResult(Contract):
    dimension: Dimension
    score: int | None = Field(ge=0, le=4)
    explanation: CoachingText


class AnswerEvaluation(Contract):
    rubric_version: Literal["answer-rubric-v1"]
    profile: Profile
    score_basis: Literal["lexical_coverage", "rubric_mean"]
    score: int = Field(ge=0, le=4)
    feedback: Text
    matched_concepts: list[Concept] = Field(max_length=12)
    overall_feedback: CoachingText
    strengths: list[CoachingText] = Field(max_length=6)
    improvements: list[CoachingText] = Field(min_length=1, max_length=6)
    missing_concepts: list[Concept] = Field(max_length=12)
    recommended_answer_structure: list[CoachingText] = Field(min_length=1, max_length=6)
    potential_followup: CoachingText
    rubric_results: list[RubricResult] = Field(min_length=5, max_length=10)

    @model_validator(mode="after")
    def consistent_rubric(self) -> "AnswerEvaluation":
        if [row.dimension for row in self.rubric_results] != list(dimensions(self.profile)):
            raise ValueError("Rubric dimensions must match the ordered profile")
        if self.feedback != self.overall_feedback:
            raise ValueError("Legacy feedback must preserve the overall explanation")
        scores = [row.score for row in self.rubric_results if row.score is not None]
        if self.score_basis == "rubric_mean" and (
            not scores or self.score != sum(scores) // len(scores)
        ):
            raise ValueError("Aggregate must be the rounded-down mean of assessed criteria")
        # Conservative ASCII serialization also bounds PostgreSQL JSONB's spaced text.
        if len(json.dumps(self.model_dump(mode="json")).encode("utf-8")) > 15000:
            raise ValueError("Evaluation exceeds storage budget")
        return self


class Followup(Contract):
    question: Text
    rationale: Text


class RoadmapStep(Contract):
    topic: Label
    activity: Text
    minutes: int = Field(ge=1, le=600)
    success_check: Text


class Roadmap(Contract):
    summary: Text
    steps: list[RoadmapStep] = Field(min_length=1, max_length=6)


class ProjectQuestion(Contract):
    question: Text
    focus: Label
    evidence: Concept


class ProjectQuestions(Contract):
    questions: list[ProjectQuestion] = Field(min_length=1, max_length=6)


class Provenance(Contract):
    provider: str
    provider_version: str
    model: str | None
    kind: Literal["simulation", "model_assisted"]
    prompt_version: Literal["ai-prompts-v1", "answer-evaluation-v2"] = "ai-prompts-v1"
    disclosure: str


class ProviderResult[T: Contract](Contract):
    data: T
    provenance: Provenance


Input = ResumeInput | JobInput | AnswerInput | FollowupInput | RoadmapInput | ProjectInput
Output = ResumeAnalysis | JobAnalysis | AnswerEvaluation | Followup | Roadmap | ProjectQuestions
