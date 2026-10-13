import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccountWorkspace } from "@/components/account-workspace";
import { WorkspaceScreen } from "@/components/workspace/workspace-context";
import { emptyAccount, workspaceFixture } from "./workspace-fixture";

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
