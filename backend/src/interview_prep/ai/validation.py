from interview_prep.ai.errors import InvalidProviderOutput
from interview_prep.ai.schemas import (
    AnswerEvaluation,
    AnswerInput,
    Contract,
    Followup,
    FollowupInput,
    Input,
    JobAnalysis,
    JobInput,
    ProjectInput,
    ProjectQuestions,
    ResumeAnalysis,
    ResumeInput,
    Roadmap,
    RoadmapInput,
)


def validate_domain(content: Input, output: Contract) -> None:
    valid = True
    if isinstance(content, (ResumeInput, JobInput)) and isinstance(
        output, (ResumeAnalysis, JobAnalysis)
    ):
        mentions = output.skills if isinstance(output, ResumeAnalysis) else output.requirements
        valid = len({m.name.casefold() for m in mentions}) == len(mentions) and all(
            0 <= m.start < m.end <= len(content.text)
            and content.text[m.start : m.end] == m.evidence
            for m in mentions
        )
    elif isinstance(content, AnswerInput) and isinstance(output, AnswerEvaluation):
        valid = (
            output.profile == content.profile
            and len(set(output.matched_concepts)) == len(output.matched_concepts)
            and set(output.matched_concepts).issubset(content.expected_concepts)
            and output.missing_concepts
            == [c for c in content.expected_concepts if c not in output.matched_concepts]
        )
        if output.score_basis == "lexical_coverage":
            expected_score = (
                4 * len(output.matched_concepts) // max(1, len(content.expected_concepts))
            )
            valid = (
                valid
                and output.score == expected_score
                and all(
                    row.score
                    == (
                        expected_score
                        if row.dimension == "completeness" and content.expected_concepts
                        else None
                    )
                    for row in output.rubric_results
                )
            )
    elif isinstance(content, FollowupInput) and isinstance(output, Followup):
        valid = output.question.strip().casefold() not in {
            q.strip().casefold() for q in [content.question, *content.recent_questions]
        }
    elif isinstance(content, RoadmapInput) and isinstance(output, Roadmap):
        valid = (
            len(output.steps) == len(content.topics)
            and {step.topic for step in output.steps} == set(content.topics)
            and sum(step.minutes for step in output.steps) <= content.weekly_minutes
        )
    elif isinstance(content, ProjectInput) and isinstance(output, ProjectQuestions):
        valid = (
            len(output.questions) == content.question_count
            and len({q.question.strip().casefold() for q in output.questions})
            == len(output.questions)
            and all(q.evidence in content.text for q in output.questions)
        )
    else:
        valid = False
    if not valid:
        raise InvalidProviderOutput()
