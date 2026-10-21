import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectsWorkspace } from "@/components/workspace/projects-workspace";
import { ProjectDefense } from "@/components/workspace/project-defense";
import { ProjectAnalysis } from "@/components/workspace/project-analysis";
import {
  createProjectApi,
  parseProject,
  parseDefense,
  type Defense,
  type Project,
  type ProjectApi,
} from "@/lib/api/projects";

const timestamp = "2026-10-20T10:00:00Z";
const prompt: Project["questions"][number] = {
  id: "q1",
  focus: "Architecture",
  prompt: "Explain this architecture.",
  path: "src/main.py",
  line: 2,
  evidence: "Route-shaped declaration",
  inferred: true,
};
function response(): Defense["responses"][number] {
  return {
    question: prompt,
    position: 1,
    answer_text: null,
    status: "draft",
    submitted_at: null,
  };
}
const project: Project = {
  id: "project",
  analysis_id: "analysis",
  name: "Illustrative task tracker",
  origin: "zip",
  github_url: null,
  commit_sha: null,
  created_at: timestamp,
  analysis_version: "project-static-v1",
  example: true,
  summary: {
    version: "project-static-v1",
    languages: { Python: 1 },
    skipped_files: 2,
    truncated: false,
    notes: ["Static inspection only."],
  },
  files: [
    {
      path: "src/main.py",
      sha256: "a".repeat(64),
      byte_count: 20,
      line_count: 3,
      language: "Python",
    },
  ],
  facts: [
    {
      path: "requirements.txt",
      line: 1,
      kind: "framework",
      description: "FastAPI dependency",
      inferred: false,
    },
    {
      path: "src/main.py",
      line: 2,
      kind: "route",
      description: "GET /tasks; exposure unverified",
      inferred: true,
    },
  ],
  questions: [prompt],
};
function run(): Defense {
  return {
    id: "run",
    project_id: "project",
    revision: 1,
    status: "active",
    current_position: 1,
    created_at: timestamp,
    completed_at: null,
    responses: [response()],
  };
}
function api(): ProjectApi {
  return {
    list: vi.fn().mockResolvedValue([project]),
    read: vi.fn().mockResolvedValue(project),
    github: vi.fn().mockResolvedValue(project),
    upload: vi.fn().mockResolvedValue(project),
    example: vi.fn().mockResolvedValue(project),
    remove: vi.fn().mockResolvedValue(undefined),
    history: vi.fn().mockResolvedValue([]),
    start: vi.fn().mockResolvedValue(run()),
    readRun: vi.fn().mockResolvedValue(run()),
    command: vi.fn().mockResolvedValue(run()),
  };
}

describe("Project Defense", () => {
  it("waits for the repository list before showing an empty state", async () => {
    const service = api();
    const pending = Promise.withResolvers<Project[]>();
    vi.mocked(service.list).mockReturnValueOnce(pending.promise);
    render(<ProjectsWorkspace api={service} />);
    expect(screen.getByText(/Loading saved repositories/)).toBeInTheDocument();
    expect(
      screen.queryByText("No saved project snapshots yet."),
    ).not.toBeInTheDocument();
    await act(async () => pending.resolve([]));
    expect(
      screen.getByText("No saved project snapshots yet."),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Loading saved repositories/),
    ).not.toBeInTheDocument();
  });
  it("recovers a failed repository list without claiming the account is empty", async () => {
    const user = userEvent.setup();
    const service = api();
    vi.mocked(service.list)
      .mockRejectedValueOnce(new Error("Repository list unavailable"))
      .mockResolvedValueOnce([]);
    render(<ProjectsWorkspace api={service} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Repository list unavailable",
    );
    expect(
      screen.queryByText("No saved project snapshots yet."),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByText("No saved project snapshots yet."),
    ).toBeInTheDocument();
    expect(service.list).toHaveBeenCalledTimes(2);
  });
  it("validates response structure and classifications", () => {
    expect(parseProject(project)).toEqual(project);
    expect(parseDefense(run())).toEqual(run());
    expect(() =>
      parseProject({
        ...project,
        summary: { ...project.summary, languages: { Python: "bad" } },
      }),
    ).toThrow();
    expect(() =>
      parseProject({
        ...project,
        facts: [{ ...project.facts[0], inferred: "true" }],
      }),
    ).toThrow();
    expect(() => parseDefense({ ...run(), status: "published" })).toThrow();
  });
  it("labels inferred architecture, direct declarations and inspected paths", () => {
    render(<ProjectAnalysis project={project} />);
    expect(screen.getByText("Inferred · route")).toBeInTheDocument();
    expect(screen.getByText("Observed · framework")).toBeInTheDocument();
    expect(screen.getByText(/src\/main.py · 3 lines/)).toBeInTheDocument();
    expect(screen.getByText(/Illustrative demo fixture/)).toBeInTheDocument();
  });
  it("imports a demo through the analyzer and starts saved practice", async () => {
    const user = userEvent.setup(),
      service = api();
    render(<ProjectsWorkspace api={service} />);
    await user.click(
      screen.getByRole("button", { name: "Load illustrative demo project" }),
    );
    expect(await screen.findByText("Repository analysis")).toBeInTheDocument();
    expect(service.example).toHaveBeenCalledOnce();
    await user.click(
      screen.getByRole("button", { name: "Start project defense" }),
    );
    expect(await screen.findByLabelText("Your answer")).toBeInTheDocument();
    expect(service.start).toHaveBeenCalledWith("project", expect.any(String));
  });
  it("retains local answers on failure and submits with the current revision", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.command).mockRejectedValueOnce(
      new Error("Service unavailable"),
    );
    render(<ProjectDefense initial={run()} api={service} onBack={vi.fn()} />);
    await user.type(
      screen.getByLabelText("Your answer"),
      "I reviewed generated code.",
    );
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "local answer is retained",
    );
    expect(screen.getByLabelText("Your answer")).toHaveValue(
      "I reviewed generated code.",
    );
    vi.mocked(service.command).mockResolvedValueOnce({
      ...run(),
      revision: 2,
      status: "completed",
      current_position: 2,
      completed_at: timestamp,
      responses: [
        {
          ...response(),
          answer_text: "I reviewed generated code.",
          status: "submitted",
          submitted_at: timestamp,
        },
      ],
    });
    await user.click(screen.getByRole("button", { name: "Submit answer" }));
    expect(service.command).toHaveBeenLastCalledWith(
      "run",
      1,
      "submit",
      "I reviewed generated code.",
    );
    expect(
      await screen.findByText("I reviewed generated code."),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Your answer")).not.toBeInTheDocument();
  });
  it("pauses durably and restores a saved draft", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.command).mockResolvedValueOnce({
      ...run(),
      status: "paused",
      revision: 2,
      responses: [{ ...response(), answer_text: "Paused draft" }],
    });
    render(<ProjectDefense initial={run()} api={service} onBack={vi.fn()} />);
    await user.type(screen.getByLabelText("Your answer"), "Paused draft");
    await user.click(screen.getByRole("button", { name: "Save and pause" }));
    expect(
      await screen.findByRole("button", { name: "Resume" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Your answer")).toBeDisabled();
    expect(screen.getByLabelText("Your answer")).toHaveValue("Paused draft");
  });
  it("keeps a local draft separate when reload finds the question completed elsewhere", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.readRun).mockResolvedValueOnce({
      ...run(),
      status: "completed",
      current_position: 2,
      revision: 2,
      completed_at: timestamp,
      responses: [
        {
          ...response(),
          status: "submitted",
          submitted_at: timestamp,
          answer_text: "Saved in another tab",
        },
      ],
    });
    render(<ProjectDefense initial={run()} api={service} onBack={vi.fn()} />);
    await user.type(screen.getByLabelText("Your answer"), "My local draft");
    await user.click(
      screen.getByRole("button", { name: "Reload saved session" }),
    );
    expect(await screen.findByLabelText(/Recovered local draft/)).toHaveValue(
      "My local draft",
    );
    expect(screen.getByText("Saved in another tab")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back to repository" }),
    ).toBeEnabled();
    expect(service.command).not.toHaveBeenCalled();
  });
  it("uses raw bounded ZIP upload, demo CSRF and private project paths", async () => {
    document.cookie = "interview_prep_csrf=test-token";
    const request = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(project)));
    const service = createProjectApi(request, "demo");
    const file = new File(["source"], "project.zip");
    await service.upload(file);
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/api/v1/demo/projects/zip",
        expect.objectContaining({
          method: "POST",
          body: file,
          headers: {
            "Content-Type": "application/zip",
            "X-CSRF-Token": "test-token",
          },
        }),
      ),
    );
    request.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await service.remove("project/other");
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/demo/projects/project%2Fother",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
