import type { components } from "./generated";
import { csrfToken } from "./workspace";

export type Roadmap = components["schemas"]["RoadmapWorkspace"];
export type Plan = components["schemas"]["PlanView"];
export type Progress = components["schemas"]["ProgressAnalytics"];
export type GeneratePlan = components["schemas"]["GenerateRoadmap"];
export type PlanningApi = ReturnType<typeof createPlanningApi>;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid planning response.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid planning text.");
  return value;
}
const nullable = (value: unknown) => (value === null ? null : text(value));
function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0)
    throw new Error("Invalid planning number.");
  return value;
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid planning flag.");
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid planning list.");
  return value;
}
function choice<const T extends readonly string[]>(
  value: unknown,
  values: T,
): T[number] {
  const result = values.find((v) => v === value);
  if (result === undefined) throw new Error("Invalid planning classification.");
  return result;
}
function plan(value: unknown): Plan {
  const r = object(value);
  return {
    id: text(r.id),
    revision: number(r.revision),
    title: text(r.title),
    status: text(r.status),
    policy_version: text(r.policy_version),
    created_at: text(r.created_at),
    weekly_minutes: number(r.weekly_minutes),
    interview_date: nullable(r.interview_date),
    starts_on: text(r.starts_on),
    target_id: nullable(r.target_id),
    target_priority: nullable(r.target_priority),
    notices: list(r.notices).map(text),
    items: list(r.items).map((v) => {
      const i = object(v);
      return {
        id: text(i.id),
        topic: text(i.topic),
        reason: text(i.reason),
        priority:
          i.priority === null
            ? null
            : choice(i.priority, ["high", "medium", "low"]),
        objective: nullable(i.objective),
        activity: nullable(i.activity),
        estimated_minutes: number(i.estimated_minutes),
        scheduled_on: nullable(i.scheduled_on),
        status: text(i.status),
        completed_at: nullable(i.completed_at),
      };
    }),
  };
}
export function parseRoadmap(value: unknown): Roadmap {
  const r = object(value);
  return {
    mode: choice(r.mode, ["account", "demo"]),
    current: r.current === null ? null : plan(r.current),
    history: list(r.history).map(plan),
    weekly_minutes: number(r.weekly_minutes),
    interview_date: nullable(r.interview_date),
    notices: list(r.notices).map(text),
    targets: list(r.targets).map((v) => {
      const t = object(v);
      return {
        id: text(t.id),
        title: text(t.title),
        priority: text(t.priority),
      };
    }),
  };
}
function accuracy(r: Record<string, unknown>) {
  return {
    correct: number(r.correct),
    graded: number(r.graded),
    percent: r.percent === null ? null : number(r.percent),
  };
}
export function parseProgress(value: unknown): Progress {
  const r = object(value),
    c = object(r.roadmap);
  const evidence = (value: unknown) =>
    list(value).map((v) => {
      const e = object(v);
      return {
        topic: text(e.topic),
        description: text(e.description),
        source_count: number(e.source_count),
      };
    });
  return {
    policy_version: choice(r.policy_version, ["progress-analytics-v1"]),
    mode: choice(r.mode, ["account", "demo"]),
    generated_at: text(r.generated_at),
    assessment_chart_available: flag(r.assessment_chart_available),
    assessments: list(r.assessments).map((v) => {
      const a = object(v);
      return {
        ...accuracy(a),
        id: text(a.id),
        at: text(a.at),
        excluded: number(a.excluded),
        grading_versions: list(a.grading_versions).map(text),
      };
    }),
    categories: list(r.categories).map((v) => {
      const a = object(v);
      return { ...accuracy(a), category: text(a.category) };
    }),
    interview_series: list(r.interview_series).map((v) => {
      const s = object(v);
      return {
        key: text(s.key),
        label: text(s.label),
        kind: text(s.kind),
        provider: text(s.provider),
        model: nullable(s.model),
        provider_version: text(s.provider_version),
        rubric_version: text(s.rubric_version),
        profile: text(s.profile),
        assessed_dimensions: list(s.assessed_dimensions).map(text),
        chart_available: flag(s.chart_available),
        points: list(s.points).map((v) => {
          const p = object(v);
          return {
            session_id: text(p.session_id),
            at: text(p.at),
            mean: number(p.mean),
            answers: number(p.answers),
          };
        }),
      };
    }),
    excluded_interview_evaluations: number(r.excluded_interview_evaluations),
    frequently_missed: list(r.frequently_missed).map((v) => {
      const m = object(v);
      return {
        concept: text(m.concept),
        basis: choice(m.basis, ["deterministic", "model_assisted"]),
        occurrences: number(m.occurrences),
        sessions: number(m.sessions),
        last_seen: text(m.last_seen),
      };
    }),
    roadmap: {
      current_total: number(c.current_total),
      current_completed: number(c.current_completed),
      historical_items: number(c.historical_items),
      historical_completed: number(c.historical_completed),
      completion_events: number(c.completion_events),
    },
    recent_sessions: list(r.recent_sessions).map((v) => {
      const s = object(v);
      return {
        id: text(s.id),
        channel: choice(s.channel, [
          "assessment",
          "interview",
          "project_defense",
        ]),
        title: text(s.title),
        status: text(s.status),
        at: text(s.at),
      };
    }),
    validated_strengths: evidence(r.validated_strengths),
    requires_validation: evidence(r.requires_validation),
    notices: list(r.notices).map(text),
  };
}
export function createPlanningApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
) {
  const base = `/api/v1/${mode}`;
  async function call(path: string, body?: unknown): Promise<unknown> {
    const response = await request(`${base}${path}`, {
      method: body === undefined ? "GET" : "POST",
      signal: AbortSignal.timeout(30000),
      headers:
        body === undefined
          ? {}
          : {
              "Content-Type": "application/json",
              ...(mode === "demo" ? { "X-CSRF-Token": csrfToken() } : {}),
            },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return response.json();
  }
  return {
    read: async () => parseRoadmap(await call("/roadmap")),
    generate: async (body: GeneratePlan) =>
      parseRoadmap(await call("/roadmap/generate", body)),
    change: async (
      id: string,
      revision: number,
      action: "complete" | "reopen",
    ) =>
      parseRoadmap(
        await call(`/roadmap/items/${encodeURIComponent(id)}`, {
          revision,
          action,
        }),
      ),
    progress: async () => parseProgress(await call("/progress")),
  };
}
