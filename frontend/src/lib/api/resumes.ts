import type { components } from "./generated";
import { WorkspaceError } from "./workspace";
import { createAIReviewApi, type AIReviewApi } from "./ai-review";

export type Resume = components["schemas"]["ResumeDetail"];
export type Evidence = components["schemas"]["EvidenceView"];
export type EvidenceInput = Omit<
  components["schemas"]["EvidenceInput"],
  "expected_revision"
>;
export type EvidenceCategory = Evidence["category"];
export const evidenceCategories: EvidenceCategory[] = [
  "language",
  "framework",
  "database",
  "tool",
  "project",
  "education",
  "experience",
  "other",
];
export const categoryLabels: Record<EvidenceCategory, string> = {
  language: "Language",
  framework: "Framework",
  database: "Database",
  tool: "Tool",
  project: "Project",
  education: "Education",
  experience: "Experience",
  other: "Other",
};

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("The resume response is invalid.");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string" || !value.trim())
    throw new Error("The resume response is invalid.");
  return value;
}
function integer(value: unknown, minimum: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < minimum)
    throw new Error("The resume response is invalid.");
  return value;
}
export function isEvidenceCategory(value: unknown): value is EvidenceCategory {
  return evidenceCategories.some((category) => category === value);
}
function parseEvidence(value: unknown): Evidence {
  const row = object(value);
  if (
    !isEvidenceCategory(row.category) ||
    (row.origin !== "resume" && row.origin !== "user") ||
    (row.review_status !== "proposed" &&
      row.review_status !== "confirmed" &&
      row.review_status !== "rejected")
  )
    throw new Error("The evidence response is invalid.");
  const source_excerpt =
    row.source_excerpt === null ? null : text(row.source_excerpt);
  const source_page =
    row.source_page === null ? null : integer(row.source_page, 1);
  const source_start =
    row.source_start === null ? null : integer(row.source_start, 0);
  const source_end =
    row.source_end === null ? null : integer(row.source_end, 1);
  if (
    (source_page !== null && source_page > 20) ||
    (row.origin === "resume" &&
      (!source_excerpt ||
        source_start === null ||
        source_end === null ||
        source_end <= source_start)) ||
    (row.origin === "user" &&
      [source_excerpt, source_page, source_start, source_end].some(
        (item) => item !== null,
      ))
  )
    throw new Error("The evidence provenance is invalid.");
  return {
    id: text(row.id),
    category: row.category,
    origin: row.origin,
    claim: text(row.claim),
    user_correction:
      row.user_correction === null ? null : text(row.user_correction),
    source_excerpt,
    source_page,
    source_start,
    source_end,
    review_status: row.review_status,
  };
}
export function parseResume(value: unknown): Resume {
  const row = object(value);
  if (
    !Array.isArray(row.evidence) ||
    row.evidence.length > 100 ||
    (row.extraction_note !== null &&
      row.extraction_note !== "no_text" &&
      row.extraction_note !== "evidence_limit")
  )
    throw new Error("The resume response is invalid.");
  const page_count =
    row.page_count === null ? null : integer(row.page_count, 1);
  if (page_count !== null && page_count > 20)
    throw new Error("The resume response is invalid.");
  return {
    id: text(row.id),
    label: text(row.label),
    revision: integer(row.revision, 1),
    page_count,
    extraction_note: row.extraction_note,
    evidence: row.evidence.map(parseEvidence),
  };
}

export function validateResumeFile(file: File): string | null {
  if (
    !file.name.toLowerCase().endsWith(".pdf") ||
    file.name.toLowerCase() === ".pdf" ||
    /[/\\:\x00-\x1f\x7f]/.test(file.name)
  )
    return "Choose a PDF with a filename without paths.";
  if (file.type !== "application/pdf")
    return "Choose a PDF file (application/pdf).";
  if (!file.size || file.size > 5 * 1024 * 1024)
    return "Choose a PDF no larger than 5 MiB.";
  return null;
}

export type ResumeApi = {
  ai?: AIReviewApi;
  list: (signal?: AbortSignal) => Promise<Resume[]>;
  read: (id: string) => Promise<Resume>;
  upload: (file: File) => Promise<Resume>;
  saveEvidence: (
    resume: Resume,
    input: EvidenceInput,
    evidence?: Evidence,
  ) => Promise<Resume>;
  removeEvidence: (resume: Resume, evidence: Evidence) => Promise<Resume>;
  remove: (resume: Resume) => Promise<void>;
};
export function createResumeApi(
  request: (path: string, init?: RequestInit) => Promise<Response>,
): ResumeApi {
  const root = "/api/v1/account/resumes";
  const path = (id: string) => `${root}/${encodeURIComponent(id)}`;
  const result = async (url: string, init?: RequestInit) =>
    parseResume(await (await request(url, init)).json());
  return {
    ai: createAIReviewApi(request),
    list: async (signal) => {
      const row = object(await (await request(root, { signal })).json());
      if (!Array.isArray(row.items) || row.items.length > 5)
        throw new Error("The resume list is invalid.");
      return row.items.map(parseResume);
    },
    read: (id) => result(path(id)),
    upload: async (file) => {
      const error = validateResumeFile(file);
      if (error) throw new WorkspaceError(error, "pdf_validation");
      return result(root, {
        method: "POST",
        headers: {
          "Content-Type": "application/pdf",
          "X-Resume-Filename": encodeURIComponent(file.name),
        },
        body: file,
        signal: AbortSignal.timeout(35000),
      });
    },
    saveEvidence: (resume, input, evidence) =>
      result(
        `${path(resume.id)}/evidence${evidence ? `/${encodeURIComponent(evidence.id)}` : ""}`,
        {
          method: evidence ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...input,
            expected_revision: resume.revision,
          }),
        },
      ),
    removeEvidence: (resume, evidence) =>
      result(
        `${path(resume.id)}/evidence/${encodeURIComponent(evidence.id)}?expected_revision=${resume.revision}`,
        { method: "DELETE" },
      ),
    remove: async (resume) => {
      await request(`${path(resume.id)}?expected_revision=${resume.revision}`, {
        method: "DELETE",
      });
    },
  };
}
