import type { components } from "./generated";

export type SkillMatrix = components["schemas"]["SkillMatrix"];
type Source = components["schemas"]["EvidenceSource"];
export type SkillApi = {
  read: (targetId: string | null, signal?: AbortSignal) => Promise<SkillMatrix>;
};

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("The skill evidence response is invalid.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid evidence text.");
  return value;
}
function nullableText(value: unknown): string | null {
  return value === null ? null : text(value);
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid evidence flag.");
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid evidence list.");
  return value;
}
function choice<T extends string>(value: unknown, allowed: readonly T[]): T {
  const result = allowed.find((item) => item === value);
  if (result === undefined) throw new Error("Invalid evidence state.");
  return result;
}
const importance = [
  "Required",
  "Preferred",
  "Mentioned",
  "Low relevance",
] as const;

function source(value: unknown): Source {
  const data = record(value);
  const occurredAt = nullableText(data.occurred_at);
  if (occurredAt !== null && !Number.isFinite(Date.parse(occurredAt)))
    throw new Error("Invalid evidence date.");
  return {
    id: text(data.id),
    kind: choice(data.kind, [
      "profile",
      "resume",
      "user",
      "job",
      "assessment",
      "interview",
    ]),
    detail: text(data.detail),
    review: text(data.review),
    eligible: flag(data.eligible),
    outcome:
      data.outcome === null
        ? null
        : choice(data.outcome, ["met", "practice"] as const),
    concept: nullableText(data.concept),
    occurred_at: occurredAt,
    importance:
      data.importance === null ? null : choice(data.importance, importance),
  };
}

export function parseSkillMatrix(value: unknown): SkillMatrix {
  const data = record(value);
  return {
    policy_version: choice(data.policy_version, ["skill-evidence-v1"]),
    mode: choice(data.mode, ["account", "demo"]),
    target_id: nullableText(data.target_id),
    targets: list(data.targets).map((value) => {
      const target = record(value);
      return { id: text(target.id), title: text(target.title) };
    }),
    notices: list(data.notices).map(text),
    rows: list(data.rows).map((value) => {
      const row = record(value);
      return {
        key: text(row.key),
        name: text(row.name),
        importance: choice(row.importance, importance),
        resume_state: choice(row.resume_state, [
          "Some evidence",
          "No resume evidence",
        ]),
        competence_state: choice(row.competence_state, [
          "Strong evidence",
          "Some evidence",
          "Needs assessment validation",
          "Validated by assessment",
          "Needs additional practice",
        ]),
        assessment_validated: flag(row.assessment_validated),
        action: choice(row.action, ["Practice", "Validate", "Maintain"]),
        explanation: list(row.explanation).map(text),
        sources: list(row.sources).map(source),
      };
    }),
  };
}

export function createSkillApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
): SkillApi {
  return {
    read: async (targetId, signal) => {
      const result = parseSkillMatrix(
        await (
          await request(
            `/api/v1/${mode}/skill-evidence${targetId ? `?target_id=${encodeURIComponent(targetId)}` : ""}`,
            { signal },
          )
        ).json(),
      );
      if (result.mode !== mode || result.target_id !== targetId)
        throw new Error("The skill evidence context is invalid.");
      return result;
    },
  };
}
