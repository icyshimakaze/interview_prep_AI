import { at, plan, roadmap, progress } from "./planning-fixture";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PersonalRoadmap } from "@/components/workspace/personal-roadmap";
import {
  ProgressAnalytics,
  ProgressReport,
} from "@/components/workspace/progress-analytics";
import {
  createPlanningApi,
  parseProgress,
  parseRoadmap,
  type PlanningApi,
  type Roadmap,
} from "@/lib/api/planning";

function api(): PlanningApi {
  return {
    read: vi.fn().mockResolvedValue(roadmap()),
    generate: vi.fn().mockResolvedValue(roadmap()),
    change: vi.fn().mockResolvedValue(roadmap()),
    progress: vi.fn().mockResolvedValue(progress()),
  };
}

describe("personal roadmap and persisted progress", () => {
  it("validates runtime contracts without turning nulls into scores", () => {
    expect(parseRoadmap(roadmap())).toEqual(roadmap());
    expect(parseProgress(progress())).toEqual(progress());
    expect(() =>
      parseRoadmap({ ...roadmap(), weekly_minutes: "120" }),
    ).toThrow();
    expect(() =>
      parseProgress({ ...progress(), assessment_chart_available: "true" }),
    ).toThrow();
  });
  it("shows loading, error and retry states", async () => {
    const service = api();
    vi.mocked(service.read).mockRejectedValueOnce(
      new Error("Service unavailable"),
    );
    render(<PersonalRoadmap api={service} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading your roadmap",
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Service unavailable",
    );
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Current roadmap")).toBeInTheDocument();
  });
  it("shows rationale and persists completion/reopen with the saved revision", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.read).mockResolvedValueOnce({
      ...roadmap(),
      targets: [{ id: "target", title: "A saved job", priority: "high" }],
    });
    const completed: Roadmap = {
      ...roadmap(),
      current: {
        ...plan(),
        revision: 3,
        items: [
          {
            ...plan().items[0],
            id: "task",
            topic: "SQL",
            reason: "Saved rationale",
            priority: "high",
            objective: null,
            activity: null,
            estimated_minutes: 60,
            scheduled_on: null,
            status: "completed",
            completed_at: at,
          },
        ],
      },
    };
    vi.mocked(service.change).mockResolvedValueOnce(completed);
    render(<PersonalRoadmap api={service} />);
    await user.click(await screen.findByText("Why this task?"));
    expect(screen.getByLabelText("Target job")).toHaveValue("");
    expect(
      screen.getByText("A reviewed response needs practice."),
    ).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Mark complete: SQL" }),
    );
    expect(service.change).toHaveBeenCalledWith("task", 2, "complete");
    await user.click(
      await screen.findByRole("button", { name: "Reopen: SQL" }),
    );
    expect(service.change).toHaveBeenLastCalledWith("task", 3, "reopen");
  });
  it("regenerates with explicit time and preserves completed historical tasks", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.generate).mockResolvedValueOnce({
      ...roadmap(),
      current: { ...plan(), id: "new", items: [] },
      history: [
        {
          ...plan(),
          status: "archived",
          items: [
            {
              id: "completed",
              topic: "SQL",
              reason: "Historical rationale",
              priority: "high",
              objective: null,
              activity: null,
              estimated_minutes: 60,
              scheduled_on: null,
              status: "completed",
              completed_at: at,
            },
          ],
        },
      ],
    });
    render(<PersonalRoadmap api={service} />);
    const hours = await screen.findByLabelText("Available hours per week");
    await user.clear(hours);
    await user.type(hours, "3");
    await user.click(
      screen.getByRole("button", { name: "Regenerate recommendations" }),
    );
    expect(service.generate).toHaveBeenCalledWith(
      expect.objectContaining({
        weekly_minutes: 180,
        expected_id: "plan",
        expected_revision: 2,
      }),
    );
    expect(await screen.findByText(/1 completed/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Reopen: SQL", hidden: true }),
    ).toBeInTheDocument();
  });
  it("keeps saved roadmap content visible on a failed regeneration", async () => {
    const user = userEvent.setup(),
      service = api();
    vi.mocked(service.generate).mockRejectedValueOnce(
      new Error("Reload the saved roadmap"),
    );
    render(<PersonalRoadmap api={service} />);
    await user.click(
      await screen.findByRole("button", { name: "Regenerate recommendations" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Reload the saved roadmap",
    );
    expect(
      screen.getByRole("button", { name: "Mark complete: SQL" }),
    ).toBeInTheDocument();
  });
  it("shows useful empty progress without charts or fabricated strengths", () => {
    render(<ProgressReport data={progress()} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(
      screen.getByText(/No strengths meet the validation policy yet/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No completed assessments with reviewed objective grades yet/,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/ready for Google/i)).not.toBeInTheDocument();
  });
  it("withholds charts for sparse history and shows genuine zero accuracy", () => {
    render(
      <ProgressReport
        data={{
          ...progress(),
          assessments: [
            {
              id: "a",
              at,
              correct: 0,
              graded: 2,
              percent: 0,
              excluded: 1,
              grading_versions: ["v1"],
            },
          ],
        }}
      />,
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText(/More history is needed/)).toBeInTheDocument();
  });
  it("renders a trend only for sufficient comparable persisted history", () => {
    render(
      <ProgressReport
        data={{
          ...progress(),
          assessment_chart_available: true,
          assessments: [0, 1, 2].map((i) => ({
            id: String(i),
            at: `2026-10-${18 + i}T10:00:00Z`,
            correct: i,
            graded: 2,
            percent: i * 50,
            excluded: 0,
            grading_versions: ["v1"],
          })),
        }}
      />,
    );
    expect(
      screen.getByRole("img", {
        name: "Recorded objective assessment accuracy (%)",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "Recorded assessment accuracy" }),
    ).toBeInTheDocument();
  });
  it("handles progress failures and retries", async () => {
    const service = api();
    vi.mocked(service.progress).mockRejectedValueOnce(
      new Error("Progress unavailable"),
    );
    render(<ProgressAnalytics api={service} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Progress unavailable",
    );
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Recent sessions")).toBeInTheDocument();
  });
  it("sends CSRF and revision data to the selected private workspace", async () => {
    document.cookie = "interview_prep_csrf=planning-token";
    const request = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(roadmap())));
    await createPlanningApi(request, "demo").change("item/id", 2, "reopen");
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/api/v1/demo/roadmap/items/item%2Fid",
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": "planning-token",
          },
          body: JSON.stringify({ revision: 2, action: "reopen" }),
        }),
      ),
    );
  });
});
