import type { components } from "./generated";
import { csrfToken } from "./workspace";

export type Question = components["schemas"]["BankQuestion"];
export type QuestionDetail = components["schemas"]["BankDetail"];
export type QuestionPage = components["schemas"]["BankPage"];
export type QuestionFacets = components["schemas"]["BankFacets"];
export type QuestionHistory = components["schemas"]["AttemptHistory"];
export type PracticeInput = components["schemas"]["PracticeInput"];
export type Practice = components["schemas"]["PracticeView"];
export type QuestionFilters = {
  search: string;
  category: string;
  subtopic: string;
  difficulty: "" | Question["difficulty"];
  question_type: "" | Question["question_type"];
  role: string;
  bookmarked: "all" | "yes" | "no";
  attempted: "all" | "yes" | "no";
  active: boolean;
  offset: number;
};
export const initialQuestionFilters: QuestionFilters = {
  search: "",
  category: "",
  subtopic: "",
  difficulty: "",
  question_type: "",
  role: "",
  bookmarked: "all",
  attempted: "all",
  active: true,
  offset: 0,
};
export type QuestionApi = {
  list: (
    filters: QuestionFilters,
    signal?: AbortSignal,
  ) => Promise<QuestionPage>;
  facets: (signal?: AbortSignal) => Promise<QuestionFacets>;
  read: (id: string, signal?: AbortSignal) => Promise<QuestionDetail>;
  bookmark: (id: string, saved: boolean) => Promise<boolean>;
  submit: (id: string, input: PracticeInput) => Promise<Practice>;
  history: (
    id: string,
    offset: number,
    signal?: AbortSignal,
  ) => Promise<QuestionHistory>;
  removeAttempt: (id: string, attemptId: string) => Promise<void>;
};

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid question response.");
  return value as Record<string, unknown>;
}
function string(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid question text.");
  return value;
}
function nullable(value: unknown): string | null {
  return value === null ? null : string(value);
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid question list.");
  return value;
}
function strings(value: unknown): string[] {
  return list(value).map(string);
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid question state.");
  return value;
}
function integer(value: unknown): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0)
    throw new Error("Invalid question count.");
  return value;
}
function choice<const T extends readonly string[]>(
  value: unknown,
  choices: T,
): T[number] {
  const result = choices.find((item) => item === value);
  if (result === undefined) throw new Error("Invalid question classification.");
  return result;
}
function date(value: unknown): string {
  const result = string(value);
  if (!Number.isFinite(Date.parse(result)))
    throw new Error("Invalid practice date.");
  return result;
}
export function parseQuestion(value: unknown): Question {
  const row = record(value);
  const version = integer(row.version);
  if (version < 1) throw new Error("Invalid question version.");
  return {
    id: string(row.id),
    version_id: string(row.version_id),
    version,
    title: string(row.title),
    category: string(row.category),
    subtopic: string(row.subtopic),
    difficulty: choice(row.difficulty, ["easy", "medium", "hard"]),
    question_type: choice(row.question_type, [
      "multiple_choice",
      "multiple_select",
      "short_answer",
      "written",
      "design",
      "behavioral",
    ]),
    tags: strings(row.tags),
    roles: strings(row.roles),
    source_classification: choice(row.source_classification, [
      "authored",
      "legacy_adapted",
      "external_reviewed",
      "fictional_demo",
    ]),
    active: flag(row.active),
    bookmarked: flag(row.bookmarked),
    attempted: flag(row.attempted),
  };
}
function pagination(row: Record<string, unknown>, count: number) {
  const total = integer(row.total),
    offset = integer(row.offset),
    limit = integer(row.limit);
  if (limit < 1 || limit > 50 || count > limit || total < count)
    throw new Error("Invalid question pagination.");
  return { total, offset, limit };
}
export function parseQuestionPage(value: unknown): QuestionPage {
  const row = record(value),
    items = list(row.items).map(parseQuestion);
  return { items, ...pagination(row, items.length) };
}
export function parseQuestionDetail(value: unknown): QuestionDetail {
  const row = record(value),
    concepts_unlocked = flag(row.concepts_unlocked);
  const expected_concepts =
    row.expected_concepts === null ? null : strings(row.expected_concepts);
  if (
    (!concepts_unlocked && expected_concepts !== null) ||
    (concepts_unlocked && expected_concepts === null)
  )
    throw new Error("Invalid concept disclosure.");
  return {
    ...parseQuestion(row),
    prompt: string(row.prompt),
    concepts_unlocked,
    expected_concepts,
    source_file: nullable(row.source_file),
    original_topic: nullable(row.original_topic),
    options: list(row.options).map((item) => {
      const option = record(item);
      return { id: string(option.id), text: string(option.text) };
    }),
  };
}
export function parseQuestionHistory(value: unknown): QuestionHistory {
  const row = record(value);
  const items = list(row.items).map((value) => {
    const item = record(value);
    return {
      id: string(item.id),
      question_version_id: string(item.question_version_id),
      channel: choice(item.channel, [
        "question_bank",
        "assessment",
        "interview",
      ]),
      submitted_at: date(item.submitted_at),
      result_kind: nullable(item.result_kind),
      response: nullable(item.response),
    };
  });
  return { items, ...pagination(row, items.length) };
}
function parsePractice(value: unknown): Practice {
  const row = record(value);
  return {
    id: string(row.id),
    question_version_id: string(row.question_version_id),
    answer_text: string(row.answer_text),
    submitted_at: date(row.submitted_at),
    result_kind: choice(row.result_kind, ["self_review", "simulation"]),
  };
}
export function createQuestionApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
): QuestionApi {
  const base = `/api/v1/${mode}/questions`;
  const path = (id: string) => `${base}/${encodeURIComponent(id)}`;
  const headers = () => ({
    "Content-Type": "application/json",
    ...(mode === "demo" ? { "X-CSRF-Token": csrfToken() } : {}),
  });
  return {
    list: async (filters, signal) => {
      const params = new URLSearchParams({
        limit: "12",
        offset: String(filters.offset),
        active: String(filters.active),
      });
      for (const key of [
        "search",
        "category",
        "subtopic",
        "difficulty",
        "question_type",
        "role",
      ] as const)
        if (filters[key]) params.set(key, filters[key]);
      for (const key of ["bookmarked", "attempted"] as const)
        if (filters[key] !== "all")
          params.set(key, String(filters[key] === "yes"));
      return parseQuestionPage(
        await (await request(`${base}?${params}`, { signal })).json(),
      );
    },
    facets: async (signal) => {
      const row = record(
        await (await request(`${base}/facets`, { signal })).json(),
      );
      return {
        categories: strings(row.categories),
        subtopics: strings(row.subtopics),
        roles: strings(row.roles),
      };
    },
    read: async (id, signal) =>
      parseQuestionDetail(await (await request(path(id), { signal })).json()),
    bookmark: async (id, saved) =>
      flag(
        record(
          await (
            await request(`${path(id)}/bookmark`, {
              method: saved ? "PUT" : "DELETE",
              headers: headers(),
              ...(saved ? { body: "{}" } : {}),
            })
          ).json(),
        ).bookmarked,
      ),
    submit: async (id, input) =>
      parsePractice(
        await (
          await request(`${path(id)}/attempts`, {
            method: "POST",
            headers: headers(),
            body: JSON.stringify(input),
          })
        ).json(),
      ),
    history: async (id, offset, signal) =>
      parseQuestionHistory(
        await (
          await request(`${path(id)}/attempts?limit=10&offset=${offset}`, {
            signal,
          })
        ).json(),
      ),
    removeAttempt: async (id, attemptId) => {
      await request(`${path(id)}/attempts/${encodeURIComponent(attemptId)}`, {
        method: "DELETE",
        headers: headers(),
      });
    },
  };
}
