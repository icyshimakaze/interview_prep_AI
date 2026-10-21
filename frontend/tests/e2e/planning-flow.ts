import type { Page } from "@playwright/test";
import { parseProgress, parseRoadmap } from "../../src/lib/api/planning";
import { expect, test } from "./fixtures";

export async function checkRoadmap(page: Page): Promise<string> {
  return test.step("roadmap generation, persistence, completion and preserved history", async () => {
    await page.getByRole("link", { name: "Roadmap", exact: true }).click();
    await expect(
      page.getByRole("heading", {
        name: "Personal preparation roadmap",
        exact: true,
      }),
    ).toBeVisible();
    await page
      .getByLabel("Available hours per week", { exact: true })
      .fill("2");
    const generated = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/demo/roadmap/generate") &&
        r.request().method() === "POST",
    );
    await page
      .getByRole("button", {
        name: /Generate roadmap|Regenerate recommendations/,
      })
      .click();
    const response = await generated;
    expect(response.status()).toBe(200);
    const roadmap = parseRoadmap(await response.json());
    const current = roadmap.current;
    if (!current || !current.items[0])
      throw new Error("The saved evidence must yield a plan.");
    expect(current.weekly_minutes).toBe(120);
    const task = current.items[0];
    const taskRow = page
      .getByRole("listitem")
      .filter({
        has: page.getByRole("heading", { name: task.topic, exact: true }),
      })
      .first();
    await taskRow.getByText("Why this task?", { exact: true }).click();
    await expect(taskRow.getByText(task.reason, { exact: true })).toBeVisible();
    await taskRow
      .getByRole("button", {
        name: `Mark complete: ${task.topic}`,
        exact: true,
      })
      .click();
    await expect(
      taskRow.getByRole("button", {
        name: `Reopen: ${task.topic}`,
        exact: true,
      }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("button", { name: `Reopen: ${task.topic}`, exact: true }),
    ).toBeVisible();
    const regenerated = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/demo/roadmap/generate") &&
        r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Regenerate recommendations", exact: true })
      .click();
    const regeneratedResponse = await regenerated;
    expect(regeneratedResponse.status()).toBe(200);
    expect(parseRoadmap(await regeneratedResponse.json()).current?.id).not.toBe(
      current.id,
    );
    await expect(
      page.getByRole("heading", { name: "Preserved history", exact: true }),
    ).toBeVisible();
    const historical = page.locator("details").filter({
      has: page.locator("summary").filter({ hasText: current.title }),
    });
    await historical.locator(":scope > summary").click();
    await expect(
      historical.getByRole("button", {
        name: `Reopen: ${task.topic}`,
        exact: true,
      }),
    ).toBeVisible();
    const reread = parseRoadmap(
      await (await page.request.get("/api/v1/demo/roadmap")).json(),
    );
    expect(
      reread.history.some(
        (plan) =>
          plan.id === current.id &&
          plan.items.some((i) => i.id === task.id && i.status === "completed"),
      ),
    ).toBe(true);
    return current.id;
  });
}

export async function checkProgress(page: Page) {
  await test.step("progress reflects persisted practice and keeps simulation unscored", async () => {
    await page.getByRole("link", { name: "Progress", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Progress analytics", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("table", {
        name: "Recorded assessment accuracy",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByText(/More history is needed for a chart/),
    ).toBeVisible();
    const data = parseProgress(
      await (await page.request.get("/api/v1/demo/progress")).json(),
    );
    expect(data.recent_sessions.some((s) => s.channel === "assessment")).toBe(
      true,
    );
    expect(data.recent_sessions.some((s) => s.channel === "interview")).toBe(
      true,
    );
    expect(
      data.recent_sessions.some((s) => s.channel === "project_defense"),
    ).toBe(true);
    expect(data.roadmap.completion_events).toBeGreaterThan(0);
    expect(data.assessment_chart_available).toBe(false);
    expect(data.interview_series).toEqual([]);
    await page
      .getByRole("button", { name: "Refresh progress", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Refresh progress", exact: true }),
    ).toBeEnabled();
  });
}
