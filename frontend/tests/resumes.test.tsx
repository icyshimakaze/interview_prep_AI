import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ResumeUpload } from "@/components/workspace/resume-upload";
import { ResumeEvidence } from "@/components/workspace/resume-evidence";
import { EvidenceForm } from "@/components/workspace/evidence-form";
import { ResumeView } from "@/components/workspace/resume-view";
import {
  createResumeApi,
  parseResume,
  validateResumeFile,
  type ResumeApi,
} from "@/lib/api/resumes";
import { WorkspaceError, workspaceRequest } from "@/lib/api/workspace";
import { resumeFixture } from "./resume-fixture";

const pdf = () =>
  new File(["%PDF-1.7\nfixture"], "candidate.pdf", { type: "application/pdf" });
function apiFixture(): ResumeApi {
  return {
    list: vi.fn().mockResolvedValue([resumeFixture]),
    read: vi.fn().mockResolvedValue({ ...resumeFixture, revision: 2 }),
    upload: vi.fn().mockResolvedValue(resumeFixture),
    saveEvidence: vi.fn().mockResolvedValue({ ...resumeFixture, revision: 2 }),
    removeEvidence: vi
      .fn()
      .mockResolvedValue({ ...resumeFixture, evidence: [], revision: 2 }),
    remove: vi.fn().mockResolvedValue(undefined),
  };
}

describe("secure resume UI", () => {
  it("checks PDF type, extension, size and malformed server evidence", () => {
    expect(validateResumeFile(pdf())).toBeNull();
    expect(
      validateResumeFile(
        new File(["x"], "resume.exe", { type: "application/pdf" }),
      ),
    ).toMatch(/filename/);
    expect(
      validateResumeFile(new File(["x"], "resume.pdf", { type: "text/plain" })),
    ).toMatch(/application\/pdf/);
    expect(
      validateResumeFile(
        new File([new Uint8Array(5 * 1024 * 1024 + 1)], "resume.pdf", {
          type: "application/pdf",
        }),
      ),
    ).toMatch(/5 MiB/);
    expect(parseResume(resumeFixture)).toEqual(resumeFixture);
    expect(() =>
      parseResume({
        ...resumeFixture,
        evidence: [{ ...resumeFixture.evidence[0], category: "score" }],
      }),
    ).toThrow();
    expect(() =>
      parseResume({
        ...resumeFixture,
        evidence: [{ ...resumeFixture.evidence[0], origin: "user" }],
      }),
    ).toThrow();
    expect(() => parseResume({ ...resumeFixture, revision: 0 })).toThrow();
  });
  it("sends raw PDF with a safe encoded filename and revisions on evidence/delete requests", async () => {
    const request = vi
      .fn()
      .mockImplementation(async () => Response.json(resumeFixture));
    const api = createResumeApi(request);
    const file = pdf();
    await api.upload(file);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/account/resumes",
      expect.objectContaining({
        method: "POST",
        body: file,
        headers: {
          "Content-Type": "application/pdf",
          "X-Resume-Filename": "candidate.pdf",
        },
      }),
    );
    await api.saveEvidence(resumeFixture, {
      category: "tool",
      claim: "Supplied tool",
      review_status: "confirmed",
    });
    const [, init] = request.mock.calls[1] ?? [];
    expect(JSON.parse(String(init.body))).toEqual({
      category: "tool",
      claim: "Supplied tool",
      review_status: "confirmed",
      expected_revision: 1,
    });
    await api.remove(resumeFixture);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/account/resumes/owned-resume?expected_revision=1",
      { method: "DELETE" },
    );
  });
  it("uses allowlisted parsing errors without exposing server text", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            { code: "pdf_encrypted", message: "private leaked text" },
            { status: 422 },
          ),
        ),
    );
    await expect(workspaceRequest("/api/v1/account/resumes")).rejects.toThrow(
      "Encrypted PDFs",
    );
  });
  it("retains the selected file on failure, permits retry and blocks empty submissions", async () => {
    const upload = vi
      .fn()
      .mockRejectedValueOnce(new Error("Encrypted PDFs are unsupported."))
      .mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ResumeUpload busy={false} onUpload={upload} />);
    await user.click(screen.getByRole("button", { name: "Upload PDF" }));
    expect(upload).not.toHaveBeenCalled();
    expect(screen.getByText("Choose a PDF to upload.")).toBeVisible();
    await user.upload(screen.getByLabelText("PDF resume"), pdf());
    await user.click(screen.getByRole("button", { name: "Upload PDF" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Encrypted PDFs are unsupported.",
    );
    await user.click(screen.getByRole("button", { name: "Upload PDF" }));
    await waitFor(() => expect(upload).toHaveBeenCalledTimes(2));
  });
  it("states that missing evidence makes no judgment and explains scans", () => {
    render(
      <ResumeEvidence
        resume={{ ...resumeFixture, evidence: [], extraction_note: "no_text" }}
        busy={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("No evidence detected in resume")).toBeVisible();
    expect(
      screen.getByText(/makes no judgment about your knowledge/),
    ).toBeVisible();
    expect(screen.getByText(/No selectable text was found/)).toBeVisible();
  });
  it("renders supplied text as text, with source and review labels", () => {
    render(
      <ResumeEvidence
        resume={{
          ...resumeFixture,
          evidence: [
            {
              ...resumeFixture.evidence[0],
              id: "unsafe",
              category: "project",
              origin: "user",
              claim: '<script>alert("x")</script>',
              source_excerpt: null,
              source_page: null,
              source_start: null,
              source_end: null,
              user_correction: null,
              review_status: "confirmed",
            },
          ],
        }}
        busy={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText('<script>alert("x")</script>')).toBeVisible();
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getByText(/Added by you/)).toBeVisible();
    expect(screen.getByText("Confirmed by you")).toBeVisible();
  });
  it("lets users correct or reject an extracted mention without inventing source fields", async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <EvidenceForm
        evidence={resumeFixture.evidence[0]}
        busy={false}
        onSave={save}
        onReload={vi.fn()}
      />,
    );
    await user.clear(screen.getByLabelText("Evidence or correction"));
    await user.type(
      screen.getByLabelText("Evidence or correction"),
      " Still learning Python ",
    );
    await user.selectOptions(
      screen.getByLabelText("Review status"),
      "rejected",
    );
    await user.click(screen.getByRole("button", { name: "Save evidence" }));
    expect(save).toHaveBeenCalledExactlyOnceWith({
      category: "language",
      claim: "Still learning Python",
      review_status: "rejected",
    });
    expect(screen.getByText("Interested in learning Python.")).toBeVisible();
  });
  it("retains a failed correction and offers explicit discard/reload", async () => {
    const save = vi
      .fn()
      .mockRejectedValue(new Error("Changed in another tab."));
    const reload = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <EvidenceForm
        evidence={resumeFixture.evidence[0]}
        busy={false}
        onSave={save}
        onReload={reload}
      />,
    );
    await user.type(screen.getByLabelText("Evidence or correction"), " basics");
    await user.click(screen.getByRole("button", { name: "Save evidence" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Changed in another tab.",
    );
    expect(screen.getByLabelText("Evidence or correction")).toHaveValue(
      "Python basics",
    );
    await user.click(
      screen.getByRole("button", { name: "Discard edits and reload" }),
    );
    expect(reload).toHaveBeenCalledOnce();
  });
  it("loads resumes with retry and requires confirmed deletion, keeping failures recoverable", async () => {
    const api = apiFixture();
    vi.mocked(api.list).mockRejectedValueOnce(new Error("Unavailable"));
    vi.mocked(api.remove)
      .mockRejectedValueOnce(
        new WorkspaceError("Record changed. Reload.", "409"),
      )
      .mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ResumeView api={api} />);
    await screen.findByText("Unavailable");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await user.click(
      await screen.findByRole("button", { name: "Delete resume" }),
    );
    expect(api.remove).not.toHaveBeenCalled();
    const dialog = screen.getByRole("dialog", { name: "Delete this resume?" });
    await user.click(
      within(dialog).getByRole("button", { name: "Confirm resume deletion" }),
    );
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "Record changed.",
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Reload latest record" }),
    );
    await waitFor(() =>
      expect(api.read).toHaveBeenCalledWith(resumeFixture.id),
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Confirm resume deletion" }),
    );
    expect(
      await screen.findByText("Your experience starts with your evidence."),
    ).toBeVisible();
    expect(api.remove).toHaveBeenLastCalledWith(
      expect.objectContaining({ revision: 2 }),
    );
  });
  it("deletes an evidence entry and preserves the resume", async () => {
    const api = apiFixture();
    const user = userEvent.setup();
    render(<ResumeView api={api} />);
    await user.click(
      await screen.findByRole("button", { name: "Delete evidence Python" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Delete evidence entry" }),
    );
    expect(
      await screen.findByText("No evidence detected in resume"),
    ).toBeVisible();
    expect(api.removeEvidence).toHaveBeenCalledWith(
      resumeFixture,
      resumeFixture.evidence[0],
    );
    expect(api.remove).not.toHaveBeenCalled();
  });
});
