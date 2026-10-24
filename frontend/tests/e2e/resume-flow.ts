import { readFile } from "node:fs/promises";
import { expect, type Page } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

export async function checkResumeUpload(page: Page): Promise<string> {
  await page.goto("/demo/resume");
  await expect(
    page.getByRole("heading", { name: "Upload a resume", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Access expires within 24 hours/)).toBeVisible();
  await page.getByLabel("PDF resume", { exact: true }).setInputFiles({
    name: "my-resume.pdf",
    mimeType: "application/pdf",
    buffer: await readFile(
      new URL("./fixtures/synthetic-resume.pdf", import.meta.url),
    ),
  });
  const uploaded = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/demo/resume-library") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Upload PDF", exact: true }).click();
  const response = await uploaded;
  expect(response.status()).toBe(201);
  const result: unknown = await response.json();
  if (
    !result ||
    typeof result !== "object" ||
    !("id" in result) ||
    typeof result.id !== "string"
  )
    throw new Error("Uploaded resume did not return an identifier");
  await expect(
    page.getByText("Your uploaded resume", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "my-resume.pdf", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Review Python", exact: true })
    .click();
  const dialog = page.getByRole("dialog", {
    name: "Review candidate evidence",
  });
  await dialog
    .getByLabel("Evidence or correction", { exact: true })
    .fill("Python in my own project");
  await dialog
    .getByRole("button", { name: "Save evidence", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: "my-resume.pdf", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Python in my own project",
      exact: true,
    }),
  ).toBeVisible();
  for (const width of [375, 768, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  return result.id;
}
