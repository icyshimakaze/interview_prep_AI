import type { components } from "./generated";
import { csrfToken } from "./workspace";
import { createAIReviewApi, type AIReviewApi } from "./ai-review";

export type Project = components["schemas"]["ProjectDetail"];
export type ProjectSummary = components["schemas"]["ProjectSummary"];
export type Defense = components["schemas"]["DefenseView"];
export type DefenseAction = components["schemas"]["DefenseCommand"]["action"];
export type ProjectApi = ReturnType<typeof createProjectApi>;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid project response.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new Error("Invalid project text.");
  return value;
}
const nullable = (value: unknown) => (value === null ? null : text(value));
function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
    throw new Error("Invalid project number.");
  return value;
}
function flag(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error("Invalid project flag.");
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("Invalid project list.");
  return value;
}
function choice<const T extends readonly string[]>(
  value: unknown,
  values: T,
): T[number] {
  const result = values.find((v) => v === value);
  if (result === undefined) throw new Error("Invalid project classification.");
  return result;
}
function summary(value: unknown): ProjectSummary {
  const r = object(value);
  return {
    id: text(r.id),
    analysis_id: text(r.analysis_id),
    name: text(r.name),
    origin: text(r.origin),
    github_url: nullable(r.github_url),
    commit_sha: nullable(r.commit_sha),
    created_at: text(r.created_at),
    analysis_version: text(r.analysis_version),
    example: flag(r.example),
  };
}
function prompt(value: unknown): Project["questions"][number] {
  const r = object(value);
  return {
    id: text(r.id),
    focus: text(r.focus),
    prompt: text(r.prompt),
    path: text(r.path),
    line: number(r.line),
    evidence: text(r.evidence),
    inferred: flag(r.inferred),
  };
}
export function parseProject(value: unknown): Project {
  const r = object(value),
    s = object(r.summary);
  return {
    ...summary(r),
    summary: {
      version: choice(s.version, ["project-static-v1"]),
      languages: Object.fromEntries(
        Object.entries(object(s.languages)).map(([k, v]) => [k, number(v)]),
      ),
      skipped_files: number(s.skipped_files),
      truncated: flag(s.truncated),
      notes: list(s.notes).map(text),
    },
    files: list(r.files).map((v) => {
      const f = object(v);
      return {
        path: text(f.path),
        sha256: text(f.sha256),
        byte_count: number(f.byte_count),
        line_count: number(f.line_count),
        language: nullable(f.language),
      };
    }),
    facts: list(r.facts).map((v) => {
      const f = object(v);
      return {
        path: text(f.path),
        line: number(f.line),
        description: text(f.description),
        inferred: flag(f.inferred),
        kind: choice(f.kind, [
          "manifest",
          "dependency",
          "framework",
          "database",
          "route",
          "schema",
          "tests",
          "ci",
          "docker",
          "documentation",
          "component",
          "authentication",
        ]),
      };
    }),
    questions: list(r.questions).map(prompt),
  };
}
export function parseDefense(value: unknown): Defense {
  const r = object(value);
  return {
    id: text(r.id),
    project_id: text(r.project_id),
    revision: number(r.revision),
    status: choice(r.status, ["active", "paused", "completed"]),
    current_position: number(r.current_position),
    created_at: text(r.created_at),
    completed_at: nullable(r.completed_at),
    responses: list(r.responses).map((v) => {
      const a = object(v);
      return {
        question: prompt(a.question),
        position: number(a.position),
        answer_text: nullable(a.answer_text),
        status: choice(a.status, ["draft", "submitted", "skipped"]),
        submitted_at: nullable(a.submitted_at),
      };
    }),
  };
}
export function createProjectApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
  mode: "account" | "demo",
) {
  const base = `/api/v1/${mode}/projects`;
  async function call(
    path = "",
    method = "GET",
    body?: unknown,
  ): Promise<unknown> {
    const response = await request(`${base}${path}`, {
      method,
      signal: AbortSignal.timeout(75000),
      headers: {
        ...(method !== "GET" && mode === "demo"
          ? { "X-CSRF-Token": csrfToken() }
          : {}),
        ...(body instanceof Blob
          ? { "Content-Type": "application/zip" }
          : body !== undefined
            ? { "Content-Type": "application/json" }
            : {}),
      },
      body:
        body instanceof Blob
          ? body
          : body === undefined
            ? undefined
            : JSON.stringify(body),
    });
    return response.status === 204 ? null : response.json();
  }
  const path = (id: string) => `/${encodeURIComponent(id)}`;
  const ai: { ai?: AIReviewApi } =
    mode === "account" ? { ai: createAIReviewApi(request) } : {};
  return {
    ...ai,
    list: async () => list(object(await call()).items).map(summary),
    read: async (id: string) => parseProject(await call(path(id))),
    github: async (url: string) =>
      parseProject(await call("/github", "POST", { url })),
    upload: async (file: File) =>
      parseProject(await call("/zip", "POST", file)),
    example: async () => parseProject(await call("/example", "POST")),
    remove: async (id: string) => {
      await call(path(id), "DELETE");
    },
    history: async (id: string) =>
      list(object(await call(`${path(id)}/defense`)).items).map(parseDefense),
    start: async (id: string, key: string) =>
      parseDefense(
        await call(`${path(id)}/defense`, "POST", {
          command_key: key,
          question_count: 10,
        }),
      ),
    readRun: async (id: string) =>
      parseDefense(await call(`/defense${path(id)}`)),
    command: async (
      id: string,
      revision: number,
      action: DefenseAction,
      answer_text?: string,
    ) =>
      parseDefense(
        await call(`/defense${path(id)}`, "POST", {
          revision,
          action,
          answer_text,
        }),
      ),
  };
}
