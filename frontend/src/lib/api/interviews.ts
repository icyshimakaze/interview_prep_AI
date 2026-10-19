import type { components } from "./generated";
import { csrfToken } from "./workspace";

export type Interview = components["schemas"]["InterviewSessionView"];
export type InterviewConfig = Required<
  components["schemas"]["InterviewConfiguration"]
>;
export type InterviewOptions = components["schemas"]["InterviewOptions"];
export type InterviewReview = components["schemas"]["InterviewReview"];
export type InterviewPage = components["schemas"]["InterviewHistory"];
export type InterviewTurn = components["schemas"]["InterviewTurnView"];
export type InterviewPayload = components["schemas"]["InterviewMutation"] &
  Partial<{
    answer_text: string | null;
    draft: { turn_id: string; answer_text: string | null } | null;
    current_answer_action: "keep_draft" | "submit" | "skip" | "none";
    from_turn_id: string;
    next_kind: "main" | "followup";
    evaluation_id: string;
    configuration: InterviewConfig;
  }>;
export type InterviewApi = {
  options: (signal?: AbortSignal) => Promise<InterviewOptions>;
  history: (offset: number, signal?: AbortSignal) => Promise<InterviewPage>;
  create: (configuration: InterviewConfig, key: string) => Promise<Interview>;
  read: (id: string, signal?: AbortSignal) => Promise<Interview>;
  command: (
    id: string,
    action: string,
    body: InterviewPayload,
    method?: "POST" | "PUT",
  ) => Promise<Interview>;
  review: (id: string, signal?: AbortSignal) => Promise<InterviewReview>;
};
export const interviewTypes = [
  "technical_fundamentals",
  "backend",
  "frontend",
  "full_stack",
  "system_design",
  "behavioral",
  "mixed",
] as const;
export const interviewLabel = (value: string) =>
  value
    .split("_")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(" ");

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid interview response.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid interview text.");
  return value;
}
const nullable = (value: unknown) => (value === null ? null : text(value));
function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0)
    throw new Error("Invalid interview number.");
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid interview list.");
  return value;
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid interview flag.");
  return value;
}
function choice<const T extends readonly string[]>(
  value: unknown,
  values: T,
): T[number] {
  const result = values.find((item) => item === value);
  if (result === undefined)
    throw new Error("Invalid interview classification.");
  return result;
}
function provider(value: unknown): Interview["provider"] {
  const row = object(value);
  return {
    name: text(row.name),
    version: text(row.version),
    kind: text(row.kind),
    model: nullable(row.model),
    disclosure: text(row.disclosure),
  };
}
function config(value: unknown): InterviewConfig {
  const row = object(value);
  return {
    target_id: nullable(row.target_id),
    interview_type: choice(row.interview_type, interviewTypes),
    difficulty: choice(row.difficulty, ["auto", "easy", "medium", "hard"]),
    question_count: number(row.question_count),
  };
}
function turn(value: unknown): InterviewTurn {
  const row = object(value);
  for (const key of ["feedback", "rubric", "expected_concepts", "score"])
    if (key in row)
      throw new Error("Unexpected interview hints before review.");
  return {
    id: text(row.id),
    sequence: number(row.sequence),
    main_ordinal: row.main_ordinal === null ? null : number(row.main_ordinal),
    parent_id: nullable(row.parent_id),
    kind: text(row.kind),
    prompt: text(row.prompt),
    category: text(row.category),
    difficulty: nullable(row.difficulty),
    status: text(row.status),
    answer_text: nullable(row.answer_text),
    answer_revision: number(row.answer_revision),
    answering_ms: number(row.answering_ms),
    running_since: nullable(row.running_since),
    context_excerpt: nullable(row.context_excerpt),
    evaluation_status: nullable(row.evaluation_status),
    evaluation_id: row.evaluation_id == null ? null : text(row.evaluation_id),
    evaluation_version:
      row.evaluation_version == null ? null : number(row.evaluation_version),
  };
}
export function parseInterview(value: unknown): Interview {
  const row = object(value),
    p = object(row.progress);
  return {
    id: text(row.id),
    revision: number(row.revision),
    contract_version: text(row.contract_version),
    status: choice(row.status, [
      "draft",
      "active",
      "paused",
      "finalizing",
      "completed",
      "abandoned",
      "failed",
    ]),
    phase: nullable(row.phase),
    configuration:
      row.configuration === null ? null : config(row.configuration),
    provider: provider(row.provider),
    target_title: nullable(row.target_title),
    started_at: nullable(row.started_at),
    deadline_at: nullable(row.deadline_at),
    ended_at: nullable(row.ended_at),
    completed_at: nullable(row.completed_at),
    end_reason: nullable(row.end_reason),
    expired: flag(row.expired),
    server_time: text(row.server_time),
    current_turn: row.current_turn === null ? null : turn(row.current_turn),
    followup_decision: text(row.followup_decision),
    progress: {
      requested: number(p.requested),
      presented: number(p.presented),
      resolved: number(p.resolved),
      answered: number(p.answered),
      skipped: number(p.skipped),
      followups_reserved: number(p.followups_reserved),
      followups_presented: number(p.followups_presented),
      evaluation_pending: number(p.evaluation_pending),
      evaluation_failed: number(p.evaluation_failed),
    },
    allowed_actions: list(row.allowed_actions).map(text),
    notices: list(row.notices).map(text),
  };
}
export function parseInterviewReview(value: unknown): InterviewReview {
  const row = object(value);
  return {
    session: parseInterview(row.session),
    review_status: choice(row.review_status, ["provisional", "final"]),
    evaluation_coverage: choice(row.evaluation_coverage, [
      "complete",
      "partial",
      "none",
    ]),
    submitted_main: number(row.submitted_main),
    evaluated_main: number(row.evaluated_main),
    unasked_main: number(row.unasked_main),
    notices: list(row.notices).map(text),
    turns: list(row.turns).map((value) => {
      const r = object(value),
        e = r.evaluation === null ? null : object(r.evaluation);
      return {
        turn: turn(r.turn),
        expected_concepts: list(r.expected_concepts).map(text),
        rubric: list(r.rubric).map(text),
        rationale: nullable(r.rationale),
        evaluation: e
          ? {
              id: text(e.id),
              version: number(e.version),
              status: text(e.status),
              kind: text(e.kind),
              score: e.score === null ? null : number(e.score),
              score_scale_max:
                e.score_scale_max === null ? null : number(e.score_scale_max),
              feedback: nullable(e.feedback),
              error_code: nullable(e.error_code),
              provider: nullable(e.provider),
              model: nullable(e.model),
              prompt_version: nullable(e.prompt_version),
            }
          : null,
      };
    }),
  };
}
export function createInterviewApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
): InterviewApi {
  const base = `/api/v1/${mode}/interviews`,
    path = (id: string) => `${base}/${encodeURIComponent(id)}`;
  async function get(url: string, signal?: AbortSignal): Promise<unknown> {
    return (
      await request(url, {
        signal: signal
          ? AbortSignal.any([signal, AbortSignal.timeout(15000)])
          : AbortSignal.timeout(15000),
      })
    ).json();
  }
  async function mutate(
    url: string,
    body: unknown,
    method = "POST",
  ): Promise<Interview> {
    const raw = object(
      await (
        await request(url, {
          method,
          signal: AbortSignal.timeout(15000),
          headers: {
            "Content-Type": "application/json",
            ...(mode === "demo" ? { "X-CSRF-Token": csrfToken() } : {}),
          },
          body: JSON.stringify(body),
        })
      ).json(),
    );
    return parseInterview(raw.session);
  }
  return {
    options: async (signal) => {
      const row = object(await get(`${base}/options`, signal));
      return {
        provider: provider(row.provider),
        max_followups: number(row.max_followups),
        answer_limit: number(row.answer_limit),
        notices: list(row.notices).map(text),
        targets: list(row.targets).map((v) => {
          const r = object(v);
          return { id: text(r.id), title: text(r.title) };
        }),
        inventory: list(row.inventory).map((v) => {
          const r = object(v);
          return {
            interview_type: choice(r.interview_type, interviewTypes),
            label: text(r.label),
            difficulty: text(r.difficulty),
            available_count: number(r.available_count),
            max_questions: number(r.max_questions),
            min_questions: number(r.min_questions),
          };
        }),
      };
    },
    history: async (offset, signal) => {
      const row = object(
        await get(`${base}?offset=${offset}&limit=10`, signal),
      );
      return {
        items: list(row.items).map(parseInterview),
        total: number(row.total),
        offset: number(row.offset),
        limit: number(row.limit),
      };
    },
    create: (configuration, key) =>
      mutate(base, { configuration, command_key: key }),
    read: async (id, signal) => parseInterview(await get(path(id), signal)),
    command: (id, action, body, method = "POST") =>
      mutate(`${path(id)}/${action}`, body, method),
    review: async (id, signal) =>
      parseInterviewReview(await get(`${path(id)}/review`, signal)),
  };
}
