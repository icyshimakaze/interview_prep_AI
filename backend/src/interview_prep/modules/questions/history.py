"""Owned submitted work from each channel, without keys or grading rubrics."""

from uuid import UUID

from sqlalchemy import Select, literal, select
from sqlalchemy.sql.selectable import Subquery

from interview_prep.modules.assessments.models import (
    AnswerStatus,
    AssessmentQuestion,
    QuestionAttempt,
)
from interview_prep.modules.interviews.models import InterviewAnswer, InterviewQuestion
from interview_prep.modules.questions.models import PracticeAttempt, QuestionVersion


def submitted_history(owner: UUID) -> Subquery:
    bank = select(
        PracticeAttempt.id,
        PracticeAttempt.question_version_id,
        literal("question_bank").label("channel"),
        PracticeAttempt.submitted_at,
        PracticeAttempt.result_kind,
        PracticeAttempt.answer_text.label("response"),
    ).where(PracticeAttempt.owner_id == owner)
    assessments = (
        select(
            QuestionAttempt.id,
            AssessmentQuestion.question_version_id,
            literal("assessment"),
            QuestionAttempt.submitted_at,
            QuestionAttempt.result_kind,
            QuestionAttempt.answer_text,
        )
        .join(AssessmentQuestion, AssessmentQuestion.id == QuestionAttempt.assessment_question_id)
        .where(
            QuestionAttempt.owner_id == owner,
            AssessmentQuestion.owner_id == owner,
            QuestionAttempt.status == AnswerStatus.SUBMITTED,
            QuestionAttempt.submitted_at.is_not(None),
        )
    )
    interviews = (
        select(
            InterviewAnswer.id,
            InterviewQuestion.question_version_id,
            literal("interview"),
            InterviewAnswer.submitted_at,
            literal(None),
            InterviewAnswer.answer_text,
        )
        .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.interview_question_id)
        .where(
            InterviewAnswer.owner_id == owner,
            InterviewQuestion.owner_id == owner,
            InterviewQuestion.question_version_id.is_not(None),
            InterviewAnswer.status == AnswerStatus.SUBMITTED,
            InterviewAnswer.submitted_at.is_not(None),
        )
    )
    return bank.union_all(assessments, interviews).subquery()


def attempted_ids(owner: UUID) -> Select[UUID]:
    history = submitted_history(owner)
    return (
        select(QuestionVersion.question_id)
        .join(
            history,
            history.c.question_version_id == QuestionVersion.id,
        )
        .distinct()
    )
