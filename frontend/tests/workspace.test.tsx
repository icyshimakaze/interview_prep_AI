import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { WorkspaceView } from "@/components/workspace-view";
import { WorkspaceShell } from "@/components/workspace/workspace-shell";
import { workspaceSections } from "@/components/workspace/navigation";
import { parseDashboard } from "@/lib/api/workspace";
import { workspaceFixture, emptyAccount } from "./workspace-fixture";

vi.mock("next/navigation", () => ({ usePathname: () => "/demo/assessments" }));

describe("workspace contracts and truthful UI", () => {
  it("validates server data and rejects malformed nested records", () => {
    expect(parseDashboard(workspaceFixture)).toEqual(workspaceFixture);
    expect(() =>
      parseDashboard({
        ...workspaceFixture,
        profile: { ...workspaceFixture.profile, weekly_minutes: "240" },
      }),
    ).toThrow();
    expect(() =>
      parseDashboard({ ...workspaceFixture, mode: "shared" }),
    ).toThrow();
    expect(() =>
      parseDashboard({
        ...workspaceFixture,
        interviews: [{ feedback: "invented" }],
      }),
    ).toThrow();
  });
  it("keeps disclosure and active semantic navigation around demo records", () => {
    render(
      <WorkspaceShell mode="demo">
        <WorkspaceView
          busy={false}
          data={workspaceFixture}
          section="assessments"
        />
      </WorkspaceShell>,
    );
    expect(screen.getByLabelText("Demo disclosure")).toHaveTextContent(
      "no real platform usage or AI evaluation",
    );
    const nav = screen.getByRole("navigation", {
      name: "Workspace navigation",
    });
    expect(within(nav).getAllByRole("link")).toHaveLength(11);
    expect(
      within(nav).getByRole("link", { name: "Skill Matrix" }),
    ).toHaveAttribute("href", "/demo/skills");
    expect(
      within(nav).getByRole("link", { name: "Assessments" }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("table", { name: "Assessment history" }),
    ).toHaveTextContent("1 correct of 2 answered");
    expect(screen.getByText("Simulated example")).toBeVisible();
  });
  it("passes only a task ID to completion and filters without inventing records", async () => {
    const complete = vi.fn();
    const user = userEvent.setup();
    render(
      <WorkspaceView
        busy={false}
        data={workspaceFixture}
        section="roadmap"
        onComplete={complete}
      />,
    );
    const button = screen.getByRole("button", {
      name: "Mark complete: Practice SQL joins",
    });
    button.focus();
    await user.keyboard("{Enter}");
    expect(complete).toHaveBeenCalledExactlyOnceWith("task-1");
    await user.selectOptions(screen.getByLabelText("Task status"), "completed");
    expect(screen.getByText("No tasks match this view.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Show all tasks" }));
    expect(screen.getByText("Practice SQL joins")).toBeVisible();
  });
  it("leads a new account with onboarding, no numerical performance claims", () => {
    render(<WorkspaceView busy={false} data={emptyAccount} />);
    expect(
      screen.getByRole("link", { name: "Set up your profile" }),
    ).toHaveAttribute("href", "/app/settings");
    expect(screen.queryByText(/fictional/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/\d+\s*(%|correct|attempts|minutes)/),
    ).not.toBeInTheDocument();
  });
  it.each(workspaceSections.map((section) => section.slug))(
    "renders %s for an empty account without sample results",
    (section) => {
      render(
        <WorkspaceView
          busy={false}
          data={emptyAccount}
          section={section}
          onSaveProfile={vi.fn()}
        />,
      );
      expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
      expect(
        screen.queryByText("Simulated diagnostic"),
      ).not.toBeInTheDocument();
    },
  );
  it("renders saved interview feedback as simulation", () => {
    render(
      <WorkspaceView
        busy={false}
        data={workspaceFixture}
        section="interviews"
      />,
    );
    expect(
      screen.getByText("Simulated feedback; no AI evaluation."),
    ).toBeVisible();
  });
  it("disables duplicate task gestures while a save is pending", () => {
    render(
      <WorkspaceView
        busy
        data={workspaceFixture}
        section="roadmap"
        onComplete={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /Mark complete:/ }),
    ).toBeDisabled();
  });
});
