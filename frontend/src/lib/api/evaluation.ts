import type { components } from "./generated";

export type AnswerEvaluation = components["schemas"]["AnswerEvaluation"];
type Dimension = components["schemas"]["RubricResult"]["dimension"];
export const scoreMeanings = [
  "Absent or incorrect: no usable evidence for this criterion, or a central error.",
  "Limited: some relevant evidence, with major gaps or errors.",
  "Partial: the central idea is present, with significant gaps or weak support.",
  "Sound: accurate and supported for the question, with only minor gaps.",
  "Thorough: accurate, well supported and complete for the requested scope.",
] as const;
export const dimensionLabels: Record<Dimension, string> = {
  correctness: "Correctness",
  relevance: "Relevance",
  completeness: "Completeness",
  depth: "Depth",
  communication_structure: "Communication / structure",
  technical_accuracy: "Technical accuracy",
  important_concepts: "Important concepts",
  trade_offs: "Trade-offs",
  complexity: "Complexity",
  star_structure: "STAR structure",
  specificity: "Specificity",
  ownership: "Ownership",
  impact: "Impact",
  reflection: "Reflection",
};
const general: Dimension[] = [
  "correctness",
  "relevance",
  "completeness",
  "depth",
  "communication_structure",
];
const technical: Dimension[] = [
  "technical_accuracy",
  "important_concepts",
  "trade_offs",
  "complexity",
];
const behavioral: Dimension[] = [
  "star_structure",
  "specificity",
  "ownership",
  "impact",
  "reflection",
];

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid evaluation.");
  return value as Record<string, unknown>;
}
function text(value: unknown, max = 600): string {
  if (typeof value !== "string" || !value.trim() || value.length > max)
    throw new Error("Invalid evaluation text.");
  return value;
}
function list(value: unknown, min: number, max: number): unknown[] {
  if (!Array.isArray(value) || value.length < min || value.length > max)
    throw new Error("Invalid evaluation list.");
  return value;
}
function score(value: unknown): number {
  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 0 ||
    value > 4
  )
    throw new Error("Invalid rubric score.");
  return value;
}
export function parseEvaluation(value: unknown): AnswerEvaluation | null {
  if (value == null) return null; // Historical rows have no structured evaluation.
  const r = object(value);
  if (
    r.rubric_version !== "answer-rubric-v1" ||
    (r.profile !== "general" &&
      r.profile !== "technical" &&
      r.profile !== "behavioral") ||
    (r.score_basis !== "lexical_coverage" && r.score_basis !== "rubric_mean")
  )
    throw new Error("Unsupported evaluation version.");
  const expected = [
    ...general,
    ...(r.profile === "technical"
      ? technical
      : r.profile === "behavioral"
        ? behavioral
        : []),
  ];
  const rubric_results = list(
    r.rubric_results,
    expected.length,
    expected.length,
  ).map((value, i) => {
    const row = object(value),
      dimension = expected[i];
    if (!dimension || row.dimension !== dimension)
      throw new Error("Invalid rubric dimensions.");
    return {
      dimension,
      score: row.score === null ? null : score(row.score),
      explanation: text(row.explanation),
    };
  });
  const result: AnswerEvaluation = {
    rubric_version: r.rubric_version,
    profile: r.profile,
    score_basis: r.score_basis,
    score: score(r.score),
    feedback: text(r.feedback),
    overall_feedback: text(r.overall_feedback),
    matched_concepts: list(r.matched_concepts, 0, 12).map((v) => text(v, 1000)),
    missing_concepts: list(r.missing_concepts, 0, 12).map((v) => text(v, 1000)),
    strengths: list(r.strengths, 0, 6).map((v) => text(v)),
    improvements: list(r.improvements, 1, 6).map((v) => text(v)),
    recommended_answer_structure: list(
      r.recommended_answer_structure,
      1,
      6,
    ).map((v) => text(v)),
    potential_followup: text(r.potential_followup),
    rubric_results,
  };
  const scores = rubric_results.flatMap((r) =>
    r.score === null ? [] : [r.score],
  );
  const concepts = [...result.matched_concepts, ...result.missing_concepts];
  const lexicalScore = Math.floor(
    (4 * result.matched_concepts.length) / Math.max(1, concepts.length),
  );
  if (
    new Set(concepts).size !== concepts.length ||
    (result.score_basis === "lexical_coverage" &&
      (result.score !== lexicalScore ||
        rubric_results.some(
          (row) =>
            row.score !==
            (row.dimension === "completeness" && concepts.length
              ? lexicalScore
              : null),
        )))
  ) {
    throw new Error("Inconsistent concept coverage.");
  }
  if (
    result.feedback !== result.overall_feedback ||
    (result.score_basis === "rubric_mean" &&
      (!scores.length ||
        result.score !==
          Math.floor(scores.reduce((a, b) => a + b, 0) / scores.length)))
  )
    throw new Error("Inconsistent evaluation.");
  return result;
}
