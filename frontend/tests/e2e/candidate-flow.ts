import type { Page } from "@playwright/test";
import type { Dashboard } from "../../src/lib/api/workspace";
import { expect, test } from "./fixtures";

export async function checkCandidateContext(page: Page, data: Dashboard) {
  await test.step("candidate dashboard and fictional target job", async () => {
    const target = data.targets[0];
    if (!target) throw new Error("A fictional target must be seeded.");
    await page.getByRole("link", { name: "Target Job", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: target.title, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Fictional target", { exact: true }),
    ).toBeVisible();
    if (target.description)
      await expect(
        page.getByText(target.description, { exact: true }),
      ).toBeVisible();
  });
  await test.step("resume context and demo analysis preserve provenance", async () => {
    const resume = data.resumes[0];
    if (!resume) throw new Error("A fictional resume must be seeded.");
    await page.getByRole("link", { name: "Resume", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: resume.label, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Fictional resume", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Recorded evidence", exact: true }),
    ).toBeVisible();
    expect(resume.evidence.length).toBeGreaterThan(0);
    for (const excerpt of resume.evidence)
      await expect(page.getByText(excerpt, { exact: true })).toBeVisible();
    await expect(
      page.getByText(/Resume claims are preparation context/),
    ).toBeVisible();
    await expect(page.getByLabel(/PDF resume/)).toHaveCount(0);
  });
}
