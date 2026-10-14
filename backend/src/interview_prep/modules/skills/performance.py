"""Translate stored results conservatively; this module never grades an answer."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    AssessmentAttempt,
    AssessmentQuestion,
    AttemptStatus,
    QuestionAttempt,
)
from interview_prep.modules.interviews.models import (
    AnswerEvaluation,
    EvaluationDimension,
    EvaluationKind,
    EvaluationStatus,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    SessionStatus,
    TurnStatus,
)
from interview_prep.modules.questions.models import (
    PublicationStatus,
    Question,
    QuestionRubricCriterion,
    QuestionSkill,
    QuestionVersion,
)
from interview_prep.modules.skills.context import INPUT_LIMIT, bounded
from interview_prep.modules.skills.matching import SkillLabel
from interview_prep.modules.skills.schemas import EvidenceSource, SkillFact


async def performance_facts(
    session: AsyncSession,
    owner: UUID,
    labels: list[SkillLabel],
    notices: list[str],
) -> list[SkillFact]:
    facts: list[SkillFact] = []
    labels_by_key = {label.key: label for label in labels}
    assessment_versions = select(AssessmentQuestion.question_version_id).where(
        AssessmentQuestion.owner_id == owner
    )
    interview_versions = select(InterviewQuestion.question_version_id).where(
        InterviewQuestion.owner_id == owner
    )
    # Only global or owned question content is readable, even for malformed legacy links.
    content = list(
        (
            await session.execute(
                select(QuestionVersion, Question.canonical_concept, QuestionSkill.skill_id)
                .join(Question, Question.id == QuestionVersion.question_id)
                .join(QuestionSkill, QuestionSkill.question_version_id == QuestionVersion.id)
                .where(
                    (Question.owner_id == owner) | (Question.owner_id.is_(None)),
                    QuestionVersion.id.in_(assessment_versions.union(interview_versions)),
                )
                .order_by(QuestionVersion.id, QuestionSkill.skill_id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    versions: dict[UUID, tuple[QuestionVersion, str, list[UUID]]] = {}
    for version, concept, skill_id in bounded(content, notices, "Question mappings"):
        if version.id not in versions:
            versions[version.id] = (version, concept, [])
        versions[version.id][2].append(skill_id)

    def append(version_id: UUID, source: EvidenceSource) -> None:
        mapping = versions.get(version_id)
        if mapping is None:
            return
        version, concept, skill_ids = mapping
        eligible = (
            source.eligible
            and len(skill_ids) == 1
            and bool(concept.strip())
            and version.provenance_reviewed
            and version.status != PublicationStatus.DRAFT
        )
        reason = source.review
        if len(skill_ids) != 1:
            reason += "; multi-skill question cannot attribute this result to one skill"
        if not version.provenance_reviewed or version.status == PublicationStatus.DRAFT:
            reason += "; question content is not reviewed/published"
        for skill_id in skill_ids:
            label = labels_by_key.get(str(skill_id))
            if label:
                facts.append(
                    SkillFact(
                        key=label.key,
                        name=label.name,
                        source=source.model_copy(
                            update={
                                "eligible": eligible,
                                "concept": concept,
                                "review": reason,
                            }
                        ),
                    )
                )

    attempts = list(
        (
            await session.execute(
                select(QuestionAttempt, AssessmentQuestion.question_version_id, AssessmentAttempt)
                .join(
                    AssessmentQuestion,
                    AssessmentQuestion.id == QuestionAttempt.assessment_question_id,
                )
                .join(
                    AssessmentAttempt, AssessmentAttempt.id == QuestionAttempt.assessment_attempt_id
                )
                .where(
                    QuestionAttempt.owner_id == owner,
                    AssessmentQuestion.owner_id == owner,
                    AssessmentAttempt.owner_id == owner,
                )
                .order_by(AssessmentAttempt.started_at.desc(), QuestionAttempt.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    for answer, version_id, attempt in bounded(attempts, notices, "Assessment answers"):
        eligible = (
            attempt.status == AttemptStatus.COMPLETED
            and attempt.completed_at is not None
            and answer.status == AnswerStatus.SUBMITTED
            and answer.submitted_at is not None
            and answer.result_kind == "deterministic"
            and bool(answer.grading_version)
            and answer.is_correct is not None
        )
        append(
            version_id,
            EvidenceSource(
                id=f"assessment:{answer.id}",
                kind="assessment",
                detail=f"Attempt {attempt.id}; question version {version_id}; "
                f"grading {answer.grading_version or 'unavailable'}",
                review=(
                    f"{attempt.status.value}; {answer.result_kind or 'ungraded'}; "
                    f"{'eligible' if eligible else 'not eligible for validation'}"
                ),
                eligible=eligible,
                outcome=("met" if answer.is_correct else "practice")
                if answer.is_correct is not None
                else None,
                occurred_at=attempt.completed_at,
            ),
        )

    # Choose newest evaluation BEFORE checking eligibility: a failed re-evaluation
    # must not resurrect an older positive result for the same answer.
    evaluations = list(
        (
            await session.execute(
                select(AnswerEvaluation, InterviewAnswer, InterviewQuestion, InterviewSession)
                .join(InterviewAnswer, InterviewAnswer.id == AnswerEvaluation.interview_answer_id)
                .join(
                    InterviewQuestion, InterviewQuestion.id == InterviewAnswer.interview_question_id
                )
                .join(InterviewSession, InterviewSession.id == InterviewQuestion.session_id)
                .where(
                    AnswerEvaluation.owner_id == owner,
                    InterviewAnswer.owner_id == owner,
                    InterviewQuestion.owner_id == owner,
                    InterviewSession.owner_id == owner,
                )
                .order_by(AnswerEvaluation.version.desc(), AnswerEvaluation.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    criteria_by_version: dict[UUID, list[QuestionRubricCriterion]] = defaultdict(list)
    criteria_rows = list(
        (
            await session.scalars(
                select(QuestionRubricCriterion)
                .where(QuestionRubricCriterion.question_version_id.in_(versions))
                .order_by(QuestionRubricCriterion.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    for criterion in bounded(criteria_rows, notices, "Rubric criteria"):
        criteria_by_version[criterion.question_version_id].append(criterion)
    dimensions_by_evaluation: dict[UUID, list[EvaluationDimension]] = defaultdict(list)
    dimension_rows = list(
        (
            await session.scalars(
                select(EvaluationDimension)
                .where(
                    EvaluationDimension.owner_id == owner,
                    EvaluationDimension.evaluation_id.in_([row[0].id for row in evaluations]),
                )
                .order_by(EvaluationDimension.id)
                .limit(INPUT_LIMIT + 1)
            )
        ).all()
    )
    for dimension in bounded(dimension_rows, notices, "Rubric dimensions"):
        dimensions_by_evaluation[dimension.evaluation_id].append(dimension)
    seen: set[UUID] = set()
    for evaluation, interview_answer, question, interview in bounded(
        evaluations, notices, "Interview evaluations"
    ):
        if interview_answer.id in seen:
            continue
        seen.add(interview_answer.id)
        mapping = versions.get(question.question_version_id)
        if mapping is None:
            continue
        version = mapping[0]
        criteria = criteria_by_version[version.id]
        dimensions = dimensions_by_evaluation[evaluation.id]
        complete = (
            bool(criteria)
            and {c.id for c in criteria} == {d.criterion_id for d in dimensions}
            and all(not d.not_evaluable and d.score is not None for d in dimensions)
            and version.rubric_version == evaluation.rubric_version
        )
        eligible = (
            interview.status == SessionStatus.COMPLETED
            and interview.completed_at is not None
            and question.status == TurnStatus.EVALUATED
            and interview_answer.status == AnswerStatus.SUBMITTED
            and interview_answer.submitted_at is not None
            and evaluation.kind == EvaluationKind.DETERMINISTIC
            and evaluation.status == EvaluationStatus.COMPLETED
            and bool(evaluation.evaluator_version)
            and complete
        )
        passed = complete and all(d.score is not None and d.score >= 3 for d in dimensions)
        append(
            version.id,
            EvidenceSource(
                id=f"interview:{evaluation.id}",
                kind="interview",
                detail=f"Session {interview.id}; question version {version.id}; "
                f"evaluation version {evaluation.version}; rubric {evaluation.rubric_version}. "
                "Every rubric dimension must reach anchor 3 of 4.",
                review=(
                    f"{interview.status.value}; {evaluation.kind.value}; "
                    f"{'eligible' if eligible else 'not eligible for validation'}"
                ),
                eligible=eligible,
                outcome=("met" if passed else "practice") if complete else None,
                occurred_at=interview.completed_at,
            ),
        )
    return facts
