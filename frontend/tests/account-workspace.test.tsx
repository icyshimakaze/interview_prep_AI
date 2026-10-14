import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccountWorkspace } from "@/components/account-workspace";
import { WorkspaceScreen } from "@/components/workspace/workspace-context";
import { emptyAccount, workspaceFixture } from "./workspace-fixture";
import type { Target } from "@/lib/api/workspace";
import { resumeFixture } from "./resume-fixture";
import type { Resume } from "@/lib/api/resumes";

const auth = vi.hoisted(() => ({
  subject: "account-one",
  token: vi.fn(),
  signOut: vi.fn(),
  replace: vi.fn(),
  refresh: vi.fn(),
}));
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: auth.subject,
    getToken: auth.token,
  }),
  useClerk: () => ({ signOut: auth.signOut }),
}));
vi.mock("next/navigation", () => ({
  usePathname: () => "/app/settings",
  useRouter: () => ({ replace: auth.replace, refresh: auth.refresh }),
}));

beforeEach(() => {
  auth.subject = "account-one";
  auth.token.mockResolvedValue("test-sdk-token");
  auth.signOut.mockResolvedValue(undefined);
});

describe("account workspace integration", () => {
  it("loads question bank filters through SDK authentication", async () => {
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get("Authorization")).toBe(
        "Bearer test-sdk-token",
      );
      expect(url).not.toContain("owner_id");
      if (url.endsWith("/session")) return Response.json({ mode: "account" });
      if (url.endsWith("/dashboard")) return Response.json(emptyAccount);
      if (url.endsWith("/questions/facets"))
        return Response.json({ categories: [], subtopics: [], roles: [] });
      if (url.includes("/questions?"))
        return Response.json({ items: [], total: 0, offset: 0, limit: 12 });
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="questions" />
      </AccountWorkspace>,
    );
    expect(
      await screen.findByText("No questions match this view"),
    ).toBeVisible();
    expect(auth.token).toHaveBeenCalledWith({ template: "interview-prep-api" });
  });
  it("loads the skill matrix through SDK authentication without a client owner ID", async () => {
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get("Authorization")).toBe(
        "Bearer test-sdk-token",
      );
      expect(url).not.toContain("owner_id");
      if (url.endsWith("/session")) return Response.json({ mode: "account" });
      if (url.endsWith("/dashboard")) return Response.json(emptyAccount);
      if (url.endsWith("/skill-evidence"))
        return Response.json({
          policy_version: "skill-evidence-v1",
          mode: "account",
          target_id: null,
          targets: [],
          rows: [],
          notices: [],
        });
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="skills" />
      </AccountWorkspace>,
    );
    expect(await screen.findByText("No skill evidence yet")).toBeVisible();
    expect(auth.token).toHaveBeenCalledWith({ template: "interview-prep-api" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/account/skill-evidence",
      expect.any(Object),
    );
  });
  it("uploads, corrects and deletes a resume using SDK authentication and owned revisions", async () => {
    let resume: Resume | null = null;
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get("Authorization")).toBe(
        "Bearer test-sdk-token",
      );
      if (url.endsWith("/resumes") && init.method === "POST") {
        expect(init.body).toBeInstanceOf(File);
        expect(new Headers(init.headers).get("Content-Type")).toBe(
          "application/pdf",
        );
        expect(new Headers(init.headers).get("X-Resume-Filename")).toBe(
          "candidate.pdf",
        );
        resume = resumeFixture;
        return Response.json(resume);
      }
      if (url.includes("/evidence/") && init.method === "PUT") {
        const body: Record<string, unknown> = JSON.parse(String(init.body));
        expect(body.expected_revision).toBe(1);
        expect(body).not.toHaveProperty("owner_id");
        expect(body).not.toHaveProperty("source_excerpt");
        resume = {
          ...resumeFixture,
          revision: 2,
          evidence: resumeFixture.evidence.map((item) => ({
            ...item,
            user_correction: String(body.claim),
            review_status: "confirmed",
          })),
        };
        return Response.json(resume);
      }
      if (url.includes("/resumes/owned-resume") && init.method === "DELETE") {
        expect(url).toContain("expected_revision=2");
        resume = null;
        return new Response(null, { status: 204 });
      }
      if (url.endsWith("/resumes"))
        return Response.json({ items: resume ? [resume] : [] });
      return Response.json(url.endsWith("/session") ? {} : emptyAccount);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="resume" />
      </AccountWorkspace>,
    );
    const user = userEvent.setup();
    await screen.findByText("Your experience starts with your evidence.");
    await user.upload(
      screen.getByLabelText("PDF resume"),
      new File(["%PDF-1.7\nfixture"], "candidate.pdf", {
        type: "application/pdf",
      }),
    );
    await user.click(screen.getByRole("button", { name: "Upload PDF" }));
    await user.click(
      await screen.findByRole("button", { name: "Review Python" }),
    );
    await user.type(screen.getByLabelText("Evidence or correction"), " basics");
    await user.selectOptions(
      screen.getByLabelText("Review status"),
      "confirmed",
    );
    await user.click(screen.getByRole("button", { name: "Save evidence" }));
    await screen.findByText("Evidence saved.");
    await user.click(screen.getByRole("button", { name: "Delete resume" }));
    await user.click(
      screen.getByRole("button", { name: "Confirm resume deletion" }),
    );
    expect(
      await screen.findByText("Your experience starts with your evidence."),
    ).toBeVisible();
  });
  it("creates, edits and deletes target jobs through authenticated requests", async () => {
    const sample = workspaceFixture.targets[0];
    if (!sample) throw new Error("Missing target fixture");
    let job: Target | null = null;
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get("Authorization")).toBe(
        "Bearer test-sdk-token",
      );
      if (url.includes("/targets?") && init.method !== "DELETE")
        return Response.json({
          items: job ? [job] : [],
          total: job ? 1 : 0,
          offset: 0,
          limit: 20,
        });
      if (url.endsWith("/targets") && init.method === "POST") {
        const body: Record<string, unknown> = JSON.parse(String(init.body));
        expect(body).toEqual(
          expect.objectContaining({
            title: "Frontend job",
            description: "Supplied context",
          }),
        );
        expect(body).not.toHaveProperty("owner_id");
        job = {
          ...sample,
          title: String(body.title),
          description: String(body.description),
          id: "owned-job",
        };
        return Response.json(job);
      }
      if (url.includes("/targets/owned-job") && init.method === "PUT") {
        const body: Record<string, unknown> = JSON.parse(String(init.body));
        expect(body.expected_revision).toBe(1);
        if (!job) throw new Error("Job was not created");
        job = { ...job, title: String(body.title), revision: 2 };
        return Response.json(job);
      }
      if (url.includes("/targets/owned-job") && init.method === "DELETE") {
        expect(url).toContain("expected_revision=2");
        job = null;
        return new Response(null, { status: 204 });
      }
      return Response.json(url.endsWith("/session") ? {} : emptyAccount);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="targets" />
      </AccountWorkspace>,
    );
    const user = userEvent.setup();
    await screen.findByText("Start with a job you are considering.");
    await user.click(screen.getByRole("button", { name: "Add target job" }));
    await user.type(screen.getByLabelText("Job title"), "Frontend job");
    await user.type(
      screen.getByLabelText("Job description"),
      "Supplied context",
    );
    await user.click(screen.getByRole("button", { name: "Save job" }));
    await user.click(
      await screen.findByRole("button", { name: "Edit Frontend job" }),
    );
    await user.type(screen.getByLabelText("Job title"), " II");
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    await user.click(
      await screen.findByRole("button", { name: "Delete Frontend job II" }),
    );
    await user.click(screen.getByRole("button", { name: "Delete target job" }));
    expect(
      await screen.findByText("Start with a job you are considering."),
    ).toBeVisible();
  });
  it("bootstraps with SDK credentials, retries a failed read, and renders no fake activity", async () => {
    let reads = 0;
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get("Authorization")).toBe(
        "Bearer test-sdk-token",
      );
      expect(init.cache).toBe("no-store");
      if (url.endsWith("/session")) return new Response("{}", { status: 200 });
      reads += 1;
      return reads === 1
        ? new Response("{}", { status: 503 })
        : Response.json(emptyAccount);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="dashboard" />
      </AccountWorkspace>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "temporarily unavailable",
    );
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("link", { name: "Set up your profile" }),
    ).toBeVisible();
    expect(auth.token).toHaveBeenCalledWith({ template: "interview-prep-api" });
  });
  it("clears private profile and draft state immediately on subject change", async () => {
    const first = {
      ...emptyAccount,
      profile: { ...workspaceFixture.profile, display_name: "First owner" },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/session")
          ? Response.json({})
          : Response.json(
              auth.subject === "account-one" ? first : emptyAccount,
            ),
      ),
    );
    const { rerender } = render(
      <AccountWorkspace>
        <WorkspaceScreen section="settings" />
      </AccountWorkspace>,
    );
    expect(await screen.findByLabelText("Display name (optional)")).toHaveValue(
      "First owner",
    );
    auth.subject = "account-two";
    rerender(
      <AccountWorkspace>
        <WorkspaceScreen section="settings" />
      </AccountWorkspace>,
    );
    expect(screen.queryByDisplayValue("First owner")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByLabelText("Display name (optional)")).toHaveValue(""),
    );
  });
  it("fails closed when an account endpoint returns demo data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        Response.json(url.endsWith("/session") ? {} : workspaceFixture),
      ),
    );
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="dashboard" />
      </AccountWorkspace>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "account workspace response is invalid",
    );
    expect(screen.queryByText(/Aarav/)).not.toBeInTheDocument();
  });

  it("does not send an old profile when token retrieval completes after an account switch", async () => {
    const fetchMock = vi.fn(async (url: string) =>
      Response.json(url.endsWith("/session") ? {} : emptyAccount),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { rerender } = render(
      <AccountWorkspace>
        <WorkspaceScreen section="settings" />
      </AccountWorkspace>,
    );
    const user = userEvent.setup();
    await user.type(
      await screen.findByLabelText("Target role"),
      "Old account draft",
    );
    let resolve: (token: string) => void = () => {
      throw new Error("Token retrieval has not started");
    };
    auth.token.mockImplementationOnce(
      () =>
        new Promise<string>((done) => {
          resolve = done;
        }),
    );
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    auth.subject = "account-two";
    rerender(
      <AccountWorkspace>
        <WorkspaceScreen section="settings" />
      </AccountWorkspace>,
    );
    resolve("new-subject-token");
    await waitFor(() =>
      expect(screen.getByLabelText("Target role")).toHaveValue(""),
    );
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith("/profile"))).toBe(
      false,
    );
  });
  it("saves a profile without client ownership IDs and reloads authoritative data", async () => {
    let saved = false;
    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      if (url.endsWith("/profile")) {
        expect(init.method).toBe("PUT");
        expect(JSON.parse(String(init.body))).toEqual({
          display_name: null,
          target_role: "Backend Engineer",
          experience_band: "entry",
          timezone: "Asia/Kolkata",
          weekly_minutes: 240,
          expected_revision: null,
          expected_id: null,
          education: null,
          graduation_year: null,
          interests: [],
          interview_date: null,
        });
        saved = true;
        return Response.json({});
      }
      return Response.json(
        url.endsWith("/session")
          ? {}
          : {
              ...emptyAccount,
              profile: saved
                ? {
                    ...workspaceFixture.profile,
                    display_name: null,
                    target_role: "Backend Engineer",
                  }
                : null,
            },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <AccountWorkspace>
        <WorkspaceScreen section="settings" />
      </AccountWorkspace>,
    );
    const user = userEvent.setup();
    await user.type(
      await screen.findByLabelText("Target role"),
      "Backend Engineer",
    );
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Profile saved"),
    );
    expect(saved).toBe(true);
  });
});
