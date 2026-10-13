import type { components } from "./generated";

export type Dashboard = components["schemas"]["DashboardView"];
export type ProfileInput = components["schemas"]["ProfileInput"];
export type Target = components["schemas"]["TargetView"];
export type TargetInput = components["schemas"]["TargetInput"];
export type TargetList = components["schemas"]["TargetList"];
export type TargetStatus = Target["status"];
export type TargetPriority = Target["priority"];

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
      id: string(candidate, "id"),
      display_name: nullableString(candidate, "display_name"),
      target_role: string(candidate, "target_role"),
      experience_band: experience,
      timezone: string(candidate, "timezone"),
      weekly_minutes: number(candidate, "weekly_minutes"),
      revision: number(candidate, "revision"),
      education: nullableString(candidate, "education"),
      graduation_year:
        candidate.graduation_year === null
          ? null
          : number(candidate, "graduation_year"),
      interests: strings(candidate, "interests"),
      interview_date: nullableString(candidate, "interview_date"),
    };
  }
  return {
    mode,
    data_label: string(data, "data_label"),
    expires_at: nullableString(data, "expires_at"),
    profile,
    targets: list(data, "targets").map(parseTarget),
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

export function validSourceUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return (
      (url.protocol === "https:" || url.protocol === "http:") &&
      Boolean(url.hostname) &&
      !url.username &&
      !url.password &&
      !/[\s\\]/.test(value)
    );
  } catch {
    return false;
  }
}

export function parseTarget(value: unknown): Target {
  const row = record(value);
  const priority = string(row, "priority");
  const status = string(row, "status");
  if (priority !== "low" && priority !== "normal" && priority !== "high")
    throw new Error("The target job response is invalid.");
  if (
    status !== "saved" &&
    status !== "applied" &&
    status !== "interviewing" &&
    status !== "archived"
  )
    throw new Error("The target job response is invalid.");
  const source = nullableString(row, "source_url");
  if (source && !validSourceUrl(source))
    throw new Error("The target job source link is invalid.");
  const revision = number(row, "revision");
  if (!Number.isInteger(revision) || revision < 1)
    throw new Error("The target job response is invalid.");
  return {
    id: string(row, "id"),
    title: string(row, "title"),
    organization: nullableString(row, "organization"),
    description: nullableString(row, "description"),
    source_url: source,
    notes: nullableString(row, "notes"),
    priority,
    status,
    revision,
  };
}

export function parseTargetList(value: unknown): TargetList {
  const row = record(value);
  const items = list(row, "items").map(parseTarget);
  const total = number(row, "total"),
    offset = number(row, "offset"),
    limit = number(row, "limit");
  if (
    ![total, offset, limit].every(Number.isInteger) ||
    limit < 1 ||
    limit > 20 ||
    items.length > limit ||
    total < items.length
  )
    throw new Error("The target job list is invalid.");
  return { items, total, offset, limit };
}

export class WorkspaceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = "WorkspaceError";
  }
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
      409: "This record changed in another tab. Reload and try again.",
      422: "Check the field values and try again. Your changes have not been saved.",
      429: "Demo creation limit reached. Please try again in an hour.",
      503: "The workspace is temporarily unavailable. Please try again.",
    };
    const payload: unknown = await response.json().catch(() => null);
    if (payload && typeof payload === "object" && "code" in payload) {
      const resumeMessages: Record<string, string> = {
        pdf_filename:
          "Choose a .pdf filename without paths or control characters.",
        pdf_mime: "Only PDF uploads are accepted. Choose a PDF file.",
        pdf_size: "Upload a PDF no larger than 5 MiB.",
        pdf_corrupt:
          "This PDF could not be read. Export a new PDF and try again.",
        pdf_encrypted:
          "Encrypted PDFs are unsupported. Upload an unlocked PDF.",
        pdf_page_limit: "Upload a PDF with between 1 and 20 pages.",
        pdf_complex:
          "This PDF exceeds safe parsing limits. Export a simpler PDF.",
        pdf_worker_unavailable:
          "PDF parsing is temporarily unavailable. Try again.",
        pdf_busy: "PDF parsing is busy. Please try again shortly.",
        pdf_upload_timeout: "The upload timed out. Please try again.",
        resume_limit:
          "You can save up to 5 resumes. Delete an unwanted resume first.",
        evidence_limit: "A resume can contain up to 100 evidence entries.",
        resume_no_version:
          "This resume has no parsed version. Upload a new PDF.",
        resume_in_use:
          "Preparation history references this resume. You can delete its evidence; deleting the resume requires removing that history.",
      };
      if (
        typeof payload.code === "string" &&
        Object.hasOwn(resumeMessages, payload.code)
      )
        throw new WorkspaceError(
          resumeMessages[payload.code] ?? "Resume request failed.",
          payload.code,
        );
      if (payload.code === "target_in_use")
        throw new WorkspaceError(
          "This job is used by preparation history. Archive it instead of deleting it.",
          "target_in_use",
        );
      if (payload.code === "target_limit")
        throw new WorkspaceError(
          "You can save up to 100 jobs. Delete an unwanted job before adding another.",
          "target_limit",
        );
    }
    throw new WorkspaceError(
      messages[response.status] ??
        "The workspace request failed. Please try again.",
      String(response.status),
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
