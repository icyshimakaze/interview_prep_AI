from abc import ABC, abstractmethod
from typing import Literal, Protocol, cast, runtime_checkable

from pydantic import ValidationError

from interview_prep.ai.errors import InvalidProviderOutput
from interview_prep.ai.rubric import EVALUATION_PROMPT_VERSION
from interview_prep.ai.schemas import (
    AnswerEvaluation,
    AnswerInput,
    Contract,
    Followup,
    FollowupInput,
    Input,
    JobAnalysis,
    JobInput,
    Operation,
    ProjectInput,
    ProjectQuestions,
    Provenance,
    ProviderResult,
    ResumeAnalysis,
    ResumeInput,
    Roadmap,
    RoadmapInput,
)
from interview_prep.ai.validation import validate_domain


@runtime_checkable
class AIProvider(Protocol):
    name: str
    version: str
    kind: Literal["simulation", "model_assisted"]
    timeout_seconds: float
    model: str | None

    async def analyze_resume(self, content: ResumeInput) -> ProviderResult[ResumeAnalysis]: ...
    async def analyze_job_description(self, content: JobInput) -> ProviderResult[JobAnalysis]: ...
    async def evaluate_answer(self, content: AnswerInput) -> ProviderResult[AnswerEvaluation]: ...
    async def generate_followup(self, content: FollowupInput) -> ProviderResult[Followup]: ...
    async def recommend_roadmap(self, content: RoadmapInput) -> ProviderResult[Roadmap]: ...
    async def generate_project_questions(
        self, content: ProjectInput
    ) -> ProviderResult[ProjectQuestions]: ...


class BaseProvider(ABC):
    name: str
    version: str
    kind: Literal["simulation", "model_assisted"]
    model: str | None = None
    timeout_seconds: float = 30.0

    @abstractmethod
    async def _generate(self, operation: Operation, content: Input, schema: type[Contract]) -> str:
        """Return untrusted JSON. Validation and provenance are imposed afterward."""

    async def _run[T: Contract](
        self,
        operation: Operation,
        content: Input,
        schema: type[T],
    ) -> ProviderResult[T]:
        raw = await self._generate(operation, content, schema)
        try:
            if len(raw.encode("utf-8")) > 131072:
                raise InvalidProviderOutput()
            data = schema.model_validate_json(raw)
            validate_domain(content, data)
            if isinstance(data, AnswerEvaluation) and data.score_basis != (
                "lexical_coverage" if self.kind == "simulation" else "rubric_mean"
            ):
                raise InvalidProviderOutput()
        except (ValidationError, ValueError):
            raise InvalidProviderOutput() from None
        # Bind Pydantic to the concrete schema at runtime, not the erased TypeVar.
        result_type = cast(type[ProviderResult[T]], ProviderResult.__class_getitem__(schema))
        return result_type(
            data=data,
            provenance=Provenance(
                provider=self.name,
                provider_version=self.version,
                model=self.model,
                kind=self.kind,
                prompt_version=EVALUATION_PROMPT_VERSION
                if operation == "evaluate_answer"
                else "ai-prompts-v1",
                disclosure="Demo/simulated output; not verified competence."
                if self.kind == "simulation"
                else "AI-assisted output; requires human review.",
            ),
        )

    async def analyze_resume(self, content: ResumeInput) -> ProviderResult[ResumeAnalysis]:
        return await self._run(
            "analyze_resume", ResumeInput.model_validate(content), ResumeAnalysis
        )

    async def analyze_job_description(self, content: JobInput) -> ProviderResult[JobAnalysis]:
        return await self._run(
            "analyze_job_description", JobInput.model_validate(content), JobAnalysis
        )

    async def evaluate_answer(self, content: AnswerInput) -> ProviderResult[AnswerEvaluation]:
        return await self._run(
            "evaluate_answer", AnswerInput.model_validate(content), AnswerEvaluation
        )

    async def generate_followup(self, content: FollowupInput) -> ProviderResult[Followup]:
        return await self._run("generate_followup", FollowupInput.model_validate(content), Followup)

    async def recommend_roadmap(self, content: RoadmapInput) -> ProviderResult[Roadmap]:
        return await self._run("recommend_roadmap", RoadmapInput.model_validate(content), Roadmap)

    async def generate_project_questions(
        self, content: ProjectInput
    ) -> ProviderResult[ProjectQuestions]:
        return await self._run(
            "generate_project_questions", ProjectInput.model_validate(content), ProjectQuestions
        )
