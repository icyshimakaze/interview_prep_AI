import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EvaluationFeedback } from "@/components/workspace/evaluation-feedback";
import { AssessmentReview } from "@/components/workspace/assessment-review";
import { parseEvaluation, type AnswerEvaluation } from "@/lib/api/evaluation";
import { parseAssessment } from "@/lib/api/assessments";
import { assessmentFixture } from "./assessment-fixture";

function fixture(): AnswerEvaluation {
  return {
    rubric_version: "answer-rubric-v1",
    profile: "general",
    score_basis: "lexical_coverage",
    score: 2,
    feedback: "Mock simulation: word overlap does not judge correctness.",
    overall_feedback:
      "Mock simulation: word overlap does not judge correctness.",
    matched_concepts: ["Storage"],
    missing_concepts: ["Write cost"],
    strengths: ["Word overlap found for one concept; verify meaning."],
    improvements: ["Explain the cost of maintaining an index."],
    recommended_answer_structure: ["Define the index.", "Explain a trade-off."],
    potential_followup: "When would you avoid this index?",
    rubric_results: [
      "correctness",
      "relevance",
      "completeness",
      "depth",
      "communication_structure",
    ].map((dimension) => {
      // Narrow against the explicit generated contract without accepting arbitrary dimensions.
      if (
        dimension !== "correctness" &&
        dimension !== "relevance" &&
        dimension !== "completeness" &&
        dimension !== "depth" &&
        dimension !== "communication_structure"
      )
        throw new Error("Invalid fixture");
      return {
        dimension,
        score: dimension === "completeness" ? 2 : null,
        explanation:
          dimension === "completeness"
            ? "Simulation proxy: one of two concepts overlaps."
            : "Not assessed: mock cannot judge this criterion.",
      };
    }),
  };
}

describe("structured evaluation", () => {
  it("renders provider HTML and links as inert text", () => {
    const evaluation = fixture();
    const hostile =
      '<img src=x onerror="alert(1)"> [click](javascript:alert(1))';
    evaluation.overall_feedback = hostile;
    evaluation.feedback = hostile;
    evaluation.potential_followup = "<script>alert(document.cookie)</script>";
    const { container } = render(
      <EvaluationFeedback evaluation={evaluation} />,
    );
    expect(screen.getByText(hostile)).toBeVisible();
    expect(container.querySelector("img, script, a, iframe")).toBeNull();
  });
  it("shows every coaching section, rubric explanation and simulation limitation", () => {
    render(<EvaluationFeedback evaluation={fixture()} />);
    for (const name of [
      "Strengths",
      "Improvements",
      "Missing concepts",
      "Recommended answer structure",
      "Potential follow-up",
      "Rubric results",
    ]) {
      expect(screen.getByRole("heading", { name })).toBeVisible();
    }
    expect(screen.getByText(/one of two concepts overlaps/)).toBeVisible();
    expect(screen.getByText(/0 = below 25%/)).toBeVisible();
    expect(screen.getAllByText(/Not assessed: mock cannot judge/)).toHaveLength(
      4,
    );
    expect(screen.getByText(/answer-rubric-v1/)).toBeVisible();
  });

  it("shows a score's exact meaning for model judgments", () => {
    const e = fixture();
    e.score_basis = "rubric_mean";
    render(<EvaluationFeedback evaluation={e} />);
    expect(screen.getByText(/Rounded-down mean/)).toBeVisible();
    expect(screen.getAllByText(/Partial: the central idea/)[0]).toBeVisible();
    expect(screen.getByText(/requires human review/)).toBeVisible();
  });

  it("does not invent strengths or certainty for an empty result list", () => {
    const e = fixture();
    e.strengths = [];
    e.missing_concepts = [];
    render(<EvaluationFeedback evaluation={e} />);
    expect(screen.getByText(/No supported strengths/)).toBeVisible();
    expect(screen.getByText(/does not establish correctness/)).toBeVisible();
  });

  it("preserves structured assessment feedback and provider metadata through parsing", () => {
    const attempt = structuredClone(assessmentFixture);
    attempt.status = "completed";
    const q = attempt.questions[2];
    if (!q) throw new Error("Missing question");
    q.review = {
      score: 2,
      max_score: 4,
      is_correct: null,
      result_kind: "simulation",
      feedback: fixture().feedback,
      expected_concepts: ["Storage", "Write cost"],
      correct_option_ids: [],
      accepted_answers: [],
      metadata: {
        provider: "MockAIProvider",
        provider_version: "mock-structured-v2",
        policy_version: "assessment-scoring-v1",
        rubric_version: "answer-rubric-v1",
        evaluated_at: "2026-10-20T10:00:00Z",
        matched_concepts: ["Storage"],
        evaluation: fixture(),
        model: null,
        prompt_version: "answer-evaluation-v2",
      },
    };
    const parsed = parseAssessment(attempt);
    expect(parsed.questions[2]?.review?.metadata?.evaluation).toEqual(
      fixture(),
    );
    expect(parsed.questions[2]?.review?.metadata?.prompt_version).toBe(
      "answer-evaluation-v2",
    );
    render(<AssessmentReview attempt={parsed} />);
    expect(
      screen.getByRole("region", { name: "Structured answer feedback" }),
    ).toBeVisible();
  });

  it("keeps historical records without fabricated rubric results", () => {
    expect(parseEvaluation(undefined)).toBeNull();
    expect(parseEvaluation(null)).toBeNull();
  });

  it.each([
    { rubric_version: "future-version" },
    { score: 7 },
    { score: true },
    { profile: "invented" },
    { improvements: [] },
    { overall_feedback: " " },
    { rubric_results: [] },
    { score_basis: "rubric_mean", score: 4 },
  ])("rejects malformed structured feedback: %j", (patch) => {
    expect(() => parseEvaluation({ ...fixture(), ...patch })).toThrow();
  });

  it("rejects duplicate rubric criteria", () => {
    const e = fixture();
    const row = e.rubric_results[0];
    if (!row) throw new Error("Missing fixture row");
    row.dimension = "relevance";
    expect(() => parseEvaluation(e)).toThrow();
  });

  it("rejects mock correctness judgments and inconsistent coverage", () => {
    const e = fixture();
    const row = e.rubric_results[0];
    if (!row) throw new Error("Missing fixture row");
    row.score = 4;
    expect(() => parseEvaluation(e)).toThrow();
    expect(() => parseEvaluation({ ...fixture(), score: 4 })).toThrow();
    expect(() =>
      parseEvaluation({ ...fixture(), missing_concepts: ["Storage"] }),
    ).toThrow();
  });
});
