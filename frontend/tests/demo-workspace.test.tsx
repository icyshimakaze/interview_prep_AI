import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DemoWorkspace } from "@/components/demo-workspace";
import { WorkspaceScreen } from "@/components/workspace/workspace-context";
import { workspaceFixture } from "./workspace-fixture";

const navigation = vi.hoisted(() => ({ replace: vi.fn(), refresh: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => navigation,
  usePathname: () => "/demo",
}));

beforeEach(() => {
  navigation.replace.mockReset();
  navigation.refresh.mockReset();
  document.cookie = "interview_prep_csrf=demo-test-csrf; path=/";
});

function renderDemo() {
  return render(
    <DemoWorkspace>
      <WorkspaceScreen section="dashboard" />
    </DemoWorkspace>,
  );
}

describe("demo lifecycle and recoverable states", () => {
  it("shows pending bootstrap, then retries a failed dashboard without losing the route", async () => {
    const user = userEvent.setup();
    let first = true;
    const fetchMock = vi.fn(async (path: string, init: RequestInit) => {
      expect(init.credentials).toBe("same-origin");
      expect(new Headers(init.headers).get("Authorization")).toBeNull();
      if (path.endsWith("/sessions")) return Response.json({});
      if (path.endsWith("/dashboard")) {
        if (first) {
          first = false;
          return Response.json({}, { status: 503 });
        }
        return Response.json(workspaceFixture);
      }
      throw new Error(`Unexpected test request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    renderDemo();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Preparing your isolated",
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "temporarily unavailable",
    );
    await user.click(screen.getByRole("button", { name: /^Try again$/ }));
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Aarav Rao",
    );
    expect(screen.getByLabelText("Demo disclosure")).toHaveTextContent(
      "fictional",
    );
    expect(navigation.replace).not.toHaveBeenCalled();
  });

  it("retains the workspace when deletion fails and navigates only after confirmed erasure", async () => {
    const user = userEvent.setup();
    let deletes = 0;
    const fetchMock = vi.fn(async (path: string, init: RequestInit) => {
      if (path.endsWith("/sessions")) return Response.json({});
      if (path.endsWith("/dashboard")) return Response.json(workspaceFixture);
      if (path.endsWith("/session") && init.method === "DELETE") {
        expect(new Headers(init.headers).get("X-CSRF-Token")).toBe(
          "demo-test-csrf",
        );
        deletes += 1;
        return deletes === 1
          ? Response.json({}, { status: 503 })
          : new Response(null, { status: 204 });
      }
      throw new Error(`Unexpected test request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    renderDemo();
    await screen.findByRole("heading", { level: 1 });
    await user.click(
      screen.getByRole("button", { name: "Exit and delete demo" }),
    );
    const dialog = screen.getByRole("dialog", {
      name: "Delete this demo workspace?",
    });
    await user.click(
      within(dialog).getByRole("button", { name: "Delete demo and exit" }),
    );
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "temporarily unavailable",
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Aarav Rao",
    );
    expect(navigation.replace).not.toHaveBeenCalled();
    await user.click(
      within(dialog).getByRole("button", { name: "Delete demo and exit" }),
    );
    await waitFor(() =>
      expect(navigation.replace).toHaveBeenCalledExactlyOnceWith("/"),
    );
    expect(navigation.refresh).toHaveBeenCalledOnce();
  });

  it("resets an expired credential with CSRF before starting a fresh fictional workspace", async () => {
    const user = userEvent.setup();
    let expired = true;
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (path: string, init: RequestInit) => {
        calls.push(path);
        if (path.endsWith("/reset")) {
          expect(init.method).toBe("POST");
          expect(new Headers(init.headers).get("X-CSRF-Token")).toBe(
            "demo-test-csrf",
          );
          expired = false;
          return new Response(null, { status: 204 });
        }
        if (path.endsWith("/sessions"))
          return Response.json({}, { status: expired ? 401 : 200 });
        if (path.endsWith("/dashboard")) return Response.json(workspaceFixture);
        throw new Error(`Unexpected test request: ${path}`);
      }),
    );
    renderDemo();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "session expired",
    );
    await user.click(
      screen.getByRole("button", { name: "Start a fresh demo" }),
    );
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Aarav Rao",
    );
    expect(calls).toEqual([
      "/api/v1/demo/sessions",
      "/api/v1/demo/reset",
      "/api/v1/demo/sessions",
      "/api/v1/demo/dashboard",
    ]);
  });
});
