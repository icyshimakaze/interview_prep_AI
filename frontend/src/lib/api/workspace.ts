import type { components } from "./generated";

export type Dashboard = components["schemas"]["DashboardView"];
export type ProfileInput = components["schemas"]["ProfileInput"];

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("The workspace response is invalid.");
  return value as Record<string, unknown>;
}
function string(row: Record<string, unknown>, key: string): string {
  const value = row[key];
  if (typeof value !== "string")
    throw new Error("The workspace response is invalid.");
  return value;
}
function nullableString(
  row: Record<string, unknown>,
  key: string,
): string | null {
  return row[key] === null ? null : string(row, key);
}
function number(row: Record<string, unknown>, key: string): number {
  const value = row[key];
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0)
    throw new Error("The workspace response is invalid.");
  return value;
}
function list(
  row: Record<string, unknown>,
  key: string,
): Record<string, unknown>[] {
  const value = row[key];
  if (!Array.isArray(value))
    throw new Error("The workspace response is invalid.");
  return value.map(record);
}
function strings(row: Record<string, unknown>, key: string): string[] {
  const value = row[key];
  if (
    !Array.isArray(value) ||
    !value.every((item: unknown) => typeof item === "string")
  )
    throw new Error("The workspace response is invalid.");
  return value;
}

export function parseDashboard(value: unknown): Dashboard {
  const data = record(value);
  const mode = string(data, "mode");
  if (mode !== "demo" && mode !== "account")
    throw new Error("The workspace mode is invalid.");
  let profile: Dashboard["profile"] = null;
  if (data.profile !== null) {
    const candidate = record(data.profile);
    const experience = string(candidate, "experience_band");
    if (
      experience !== "student" &&
      experience !== "entry" &&
      experience !== "mid" &&
      experience !== "senior"
    )
      throw new Error("The profile response is invalid.");
    profile = {
      display_name: nullableString(candidate, "display_name"),
      target_role: string(candidate, "target_role"),
      experience_band: experience,
      timezone: string(candidate, "timezone"),
      weekly_minutes: number(candidate, "weekly_minutes"),
      revision: number(candidate, "revision"),
    };
  }
  return {
    mode,
    data_label: string(data, "data_label"),
    expires_at: nullableString(data, "expires_at"),
    profile,
    targets: list(data, "targets").map((row) => ({
      id: string(row, "id"),
      title: string(row, "title"),
      organization: nullableString(row, "organization"),
      description: nullableString(row, "description"),
    })),
    resumes: list(data, "resumes").map((row) => ({
      id: string(row, "id"),
      label: string(row, "label"),
      evidence: strings(row, "evidence"),
    })),
    assessments: list(data, "assessments").map((row) => ({
      id: string(row, "id"),
      title: string(row, "title"),
      completed_at: nullableString(row, "completed_at"),
      answered: number(row, "answered"),
      correct: number(row, "correct"),
      result_kind: string(row, "result_kind"),
    })),
    interviews: list(data, "interviews").map((row) => ({
      id: string(row, "id"),
      status: string(row, "status"),
      completed_at: nullableString(row, "completed_at"),
      feedback: strings(row, "feedback"),
      result_kind: string(row, "result_kind"),
    })),
    roadmap_items: list(data, "roadmap_items").map((row) => ({
      id: string(row, "id"),
      title: string(row, "title"),
      status: string(row, "status"),
      estimated_minutes: number(row, "estimated_minutes"),
    })),
    progress: list(data, "progress").map((row) => ({
      event_type: string(row, "event_type"),
      occurred_at: string(row, "occurred_at"),
      result_kind: nullableString(row, "result_kind"),
    })),
  };
}

export function csrfToken(): string {
  return (
    document.cookie
      .split("; ")
      .find((cookie) => cookie.startsWith("interview_prep_csrf="))
      ?.split("=")[1] ?? ""
  );
}

export async function workspaceRequest(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const response = await fetch(path, {
    ...init,
    cache: "no-store",
    credentials: "same-origin",
    signal: init.signal ?? AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    const messages: Record<number, string> = {
      401: "Your session expired. Sign in again or start a new demo.",
      403: "This workspace request is not permitted.",
      409: "Your profile changed in another tab. Reload and try again.",
      429: "Demo creation limit reached. Please try again in an hour.",
      503: "The workspace is temporarily unavailable. Please try again.",
    };
    throw new Error(
      messages[response.status] ??
        "The workspace request failed. Please try again.",
    );
  }
  return response;
}

let bootstrapping: Promise<Dashboard> | undefined;
export function enterDemo(): Promise<Dashboard> {
  bootstrapping ??= (async () => {
    await workspaceRequest("/api/v1/demo/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken(),
      },
      body: "{}",
    });
    const response = await workspaceRequest("/api/v1/demo/dashboard");
    const data = parseDashboard(await response.json());
    if (data.mode !== "demo")
      throw new Error("The demo workspace response is invalid.");
    return data;
  })().finally(() => {
    bootstrapping = undefined;
  });
  return bootstrapping;
}
