import type { Page } from "@playwright/test";
import { parseDefense, parseProject } from "../../src/lib/api/projects";
import { expect, test } from "./fixtures";

export async function checkProjectDefense(page: Page): Promise<string> {
  return test.step("real repository analyzer and saved Project Defense", async () => {
    await page
      .getByRole("link", { name: "Project Defense", exact: true })
      .click();
    await expect(
      page.getByText("No saved project snapshots yet."),
    ).toBeVisible();
    const analyzed = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/demo/projects/example") &&
        r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Load illustrative demo project" })
      .click();
    const response = await analyzed;
    expect(response.status()).toBe(200);
    const project = parseProject(await response.json());
    expect(project.example).toBe(true);
    expect(project.files.length).toBeGreaterThan(0);
    expect(project.questions).toHaveLength(10);
    await expect(
      page.getByRole("heading", { name: "Repository analysis", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Illustrative demo fixture", { exact: false }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Start project defense" }).click();
    await expect(
      page.getByRole("heading", {
        name: "Project Defense interview",
        exact: true,
      }),
    ).toBeVisible();
    const draft =
      "Fictional practice: I reviewed the route boundary and tested invalid inputs.";
    await page
      .getByRole("textbox", { name: "Your answer", exact: true })
      .fill(draft);
    await page
      .getByRole("button", { name: "Save and pause", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Resume", exact: true }),
    ).toBeVisible();
    await page.reload();
    await page.getByRole("button", { name: project.name, exact: true }).click();
    await page.getByRole("button", { name: /^Open practice/ }).click();
    await expect(
      page.getByRole("textbox", { name: "Your answer", exact: true }),
    ).toHaveValue(draft);
    await page.getByRole("button", { name: "Resume", exact: true }).click();
    await expect(
      page.getByRole("textbox", { name: "Your answer", exact: true }),
    ).toBeEnabled();
    const submitted = page.waitForResponse((r) => {
      if (
        !/\/api\/v1\/demo\/projects\/defense\/[^/]+$/.test(r.url()) ||
        r.request().method() !== "POST"
      )
        return false;
      const body: unknown = r.request().postDataJSON();
      return (
        !!body &&
        typeof body === "object" &&
        "action" in body &&
        body.action === "submit"
      );
    });
    await page
      .getByRole("button", { name: "Submit answer", exact: true })
      .click();
    const run = parseDefense(await (await submitted).json());
    expect(run.responses[0]?.answer_text).toBe(draft);
    expect(run.responses[0]?.status).toBe("submitted");
    await page
      .getByRole("button", { name: "End practice", exact: true })
      .click();
    await expect(
      page.getByText(/Deterministic practice · completed/),
    ).toBeVisible();
    await expect(page.getByText(draft, { exact: true })).toBeVisible();
    expect(
      (
        await page.request.get(`/api/v1/demo/projects/${project.id}/defense`)
      ).status(),
    ).toBe(200);
    return project.id;
  });
}
