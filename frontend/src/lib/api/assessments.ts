import type { components } from "./generated";
import { csrfToken } from "./workspace";

export type Assessment = components["schemas"]["AttemptView"];
export type AssessmentSummary = components["schemas"]["AttemptSummary"];
export type AssessmentPage = components["schemas"]["AttemptPage"];
export type AssessmentOptions = components["schemas"]["Options"];
export type AssessmentConfig = components["schemas"]["Configuration"];
export type AssessmentStart = components["schemas"]["StartInput"];
export type AssessmentResponse = components["schemas"]["ResponseInput"];
export type AssessmentQuestion = components["schemas"]["PresentedQuestion"];
export type AssessmentApi = {
  options: (signal?: AbortSignal) => Promise<AssessmentOptions>;
  history: (offset: number, signal?: AbortSignal) => Promise<AssessmentPage>;
  start: (input: AssessmentStart) => Promise<Assessment>;
  read: (id: string, signal?: AbortSignal) => Promise<Assessment>;
  save: (
    id: string,
    question: string,
    input: AssessmentResponse,
  ) => Promise<Assessment>;
  submit: (id: string, revision: number) => Promise<Assessment>;
  abandon: (id: string, revision: number) => Promise<Assessment>;
};
export const assessmentTypes = [
  "multiple_choice",
  "multiple_select",
  "short_answer",
  "written",
] as const;
export const assessmentTypeLabel = {
  multiple_choice: "MCQ · choose one",
  multiple_select: "Multiple-select · choose all that apply",
  short_answer: "Short objective answer",
  written: "Short conceptual answer",
};
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid assessment response.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid assessment text.");
  return value;
}
function nullable(value: unknown): string | null {
  return value === null ? null : text(value);
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid assessment list.");
  return value;
}
function integer(value: unknown): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0)
    throw new Error("Invalid assessment count.");
  return value;
}
function optionalNumber(value: unknown): number | null {
  return value === null ? null : integer(value);
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid assessment state.");
  return value;
}
function choice<const T extends readonly string[]>(
  value: unknown,
  choices: T,
): T[number] {
  const found = choices.find((v) => v === value);
  if (found === undefined)
    throw new Error("Invalid assessment classification.");
  return found;
}
function date(value: unknown): string {
  const result = text(value);
  if (!Number.isFinite(Date.parse(result)))
    throw new Error("Invalid assessment date.");
  return result;
}
const difficulties = ["easy", "medium", "hard"] as const;
function config(value: unknown): AssessmentConfig {
  const row = record(value);
  return {
    category: nullable(row.category),
    difficulty:
      row.difficulty === null ? null : choice(row.difficulty, difficulties),
    question_count: integer(row.question_count),
    question_types: list(row.question_types).map((v) =>
      choice(v, assessmentTypes),
    ),
  };
}
export function parseAssessmentSummary(value: unknown): AssessmentSummary {
  const row = record(value);
  return {
    id: text(row.id),
    title: text(row.title),
    status: choice(row.status, [
      "in_progress",
      "completed",
      "abandoned",
      "expired",
    ]),
    revision: integer(row.revision),
    question_count: integer(row.question_count),
    answered: integer(row.answered),
    simulated: flag(row.simulated),
    started_at: date(row.started_at),
    completed_at: row.completed_at === null ? null : date(row.completed_at),
    deadline_at: row.deadline_at === null ? null : date(row.deadline_at),
  };
}
export function parseAssessment(value: unknown): Assessment {
  const row = record(value),
    summary = parseAssessmentSummary(row);
  const questions = list(row.questions).map((value) => {
    const q = record(value);
    // Fail closed if an API regression ever includes review material before completion.
    if (summary.status !== "completed" && q.review !== null)
      throw new Error("Unexpected assessment review before submission.");
    let review: AssessmentQuestion["review"] = null;
    if (q.review !== null) {
      const r = record(q.review),
        m = r.metadata === null ? null : record(r.metadata);
      review = {
        score: optionalNumber(r.score),
        max_score: optionalNumber(r.max_score),
        is_correct: r.is_correct === null ? null : flag(r.is_correct),
        result_kind: nullable(r.result_kind),
        feedback: nullable(r.feedback),
        expected_concepts: list(r.expected_concepts).map(text),
        accepted_answers: list(r.accepted_answers).map(text),
        correct_option_ids: list(r.correct_option_ids).map(text),
        metadata: m
          ? {
              provider: text(m.provider),
              provider_version: text(m.provider_version),
              policy_version: text(m.policy_version),
              rubric_version: nullable(m.rubric_version),
              evaluated_at: date(m.evaluated_at),
              matched_concepts: list(m.matched_concepts).map(text),
            }
          : null,
      };
      if (
        review.score !== null &&
        (review.max_score === null || review.score > review.max_score)
      )
        throw new Error("Invalid assessment score.");
    }
    return {
      id: text(q.id),
      question_version_id: text(q.question_version_id),
      position: integer(q.position),
      title: text(q.title),
      prompt: text(q.prompt),
      category: text(q.category),
      difficulty:
        q.difficulty === null ? null : choice(q.difficulty, difficulties),
      question_type: choice(q.question_type, [
        ...assessmentTypes,
        "design",
        "behavioral",
      ]),
      answer_text: nullable(q.answer_text),
      selected_option_ids: list(q.selected_option_ids).map(text),
      saved_at: q.saved_at === null ? null : date(q.saved_at),
      skipped: flag(q.skipped),
      review,
      options: list(q.options).map((v) => {
        const o = record(v);
        return { id: text(o.id), text: text(o.text) };
      }),
    };
  });
  if (
    questions.length !== summary.question_count ||
    new Set(questions.map((q) => q.id)).size !== questions.length
  )
    throw new Error("Invalid assessment allocation.");
  return {
    ...summary,
    configuration:
      row.configuration === null ? null : config(row.configuration),
    questions,
    categories: list(row.categories).map((v) => {
      const c = record(v);
      return {
        category: text(c.category),
        questions: integer(c.questions),
        answered: integer(c.answered),
        skipped: integer(c.skipped),
        objective_correct: integer(c.objective_correct),
        objective_total: integer(c.objective_total),
        conceptual_score: integer(c.conceptual_score),
        conceptual_max: integer(c.conceptual_max),
        conceptual_kind: nullable(c.conceptual_kind),
      };
    }),
  };
}
export function parseAssessmentPage(value: unknown): AssessmentPage {
  const row = record(value),
    items = list(row.items).map(parseAssessmentSummary),
    limit = integer(row.limit),
    total = integer(row.total);
  if (limit < 1 || limit > 50 || items.length > limit || total < items.length)
    throw new Error("Invalid assessment pagination.");
  return { items, total, limit, offset: integer(row.offset) };
}
export function parseAssessmentOptions(value: unknown): AssessmentOptions {
  const row = record(value);
  return {
    max_questions: integer(row.max_questions),
    duration_hours: integer(row.duration_hours),
    conceptual_provider: text(row.conceptual_provider),
    conceptual_kind: choice(row.conceptual_kind, [
      "simulation",
      "model_assisted",
    ]),
    inventory: list(row.inventory).map((v) => {
      const i = record(v);
      return {
        category: text(i.category),
        difficulty: choice(i.difficulty, difficulties),
        question_type: choice(i.question_type, assessmentTypes),
        count: integer(i.count),
      };
    }),
  };
}
export function createAssessmentApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
): AssessmentApi {
  const base = `/api/v1/${mode}/assessments`,
    path = (id: string) => `${base}/${encodeURIComponent(id)}`;
  const readSignal = (signal?: AbortSignal) =>
    signal
      ? AbortSignal.any([signal, AbortSignal.timeout(10000)])
      : AbortSignal.timeout(10000);
  async function mutate(url: string, body: unknown, method = "POST") {
    return parseAssessment(
      await (
        await request(url, {
          method,
          signal: AbortSignal.timeout(75000),
          headers: {
            "Content-Type": "application/json",
            ...(mode === "demo" ? { "X-CSRF-Token": csrfToken() } : {}),
          },
          body: JSON.stringify(body),
        })
      ).json(),
    );
  }
  return {
    options: async (signal) =>
      parseAssessmentOptions(
        await (
          await request(`${base}/options`, { signal: readSignal(signal) })
        ).json(),
      ),
    history: async (offset, signal) =>
      parseAssessmentPage(
        await (
          await request(`${base}?limit=10&offset=${offset}`, {
            signal: readSignal(signal),
          })
        ).json(),
      ),
    read: async (id, signal) =>
      parseAssessment(
        await (await request(path(id), { signal: readSignal(signal) })).json(),
      ),
    start: (input) => mutate(base, input),
    save: (id, q, input) =>
      mutate(`${path(id)}/questions/${encodeURIComponent(q)}`, input, "PUT"),
    submit: (id, revision) => mutate(`${path(id)}/submit`, { revision }),
    abandon: (id, revision) => mutate(`${path(id)}/abandon`, { revision }),
  };
}
