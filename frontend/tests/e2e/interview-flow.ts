import { expect, test, type Page } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

export async function checkInterviews(page: Page): Promise<void> {
  await page.goto("/demo/interviews");
  await expect(
    page.getByRole("heading", { name: "Mock interviews", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Main questions", { exact: true }).fill("2");
  await page
    .getByRole("button", { name: "Start interview", exact: true })
    .click();
  await page
    .getByLabel("Your answer", { exact: true })
    .fill(
      "I would compare normal and invalid input before choosing a tradeoff.",
    );
  await page
    .getByRole("button", { name: "Save, pause and return", exact: true })
    .click();
  await page.reload();
  const saved = page.getByText("paused · 0 / 2 main questions · simulation", {
    exact: true,
  });
  await expect(saved).toBeVisible();
  await saved
    .locator("../..")
    .getByRole("button", { name: "Open saved interview", exact: true })
    .click();
  await expect(page.getByLabel("Your answer", { exact: true })).toHaveValue(
    "I would compare normal and invalid input before choosing a tradeoff.",
  );
  await page
    .getByRole("button", { name: "Resume interview", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Submit answer", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Ask a follow-up", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Answer follow-up", exact: true })
    .click();
  await expect(page.getByText(/Your earlier response:/)).toContainText(
    "normal and invalid input",
  );
  await page
    .getByLabel("Your answer", { exact: true })
    .fill("I would test one assumption at a time.");
  await page
    .getByRole("button", { name: "Submit answer", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Next main question", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Skip question", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Complete interview", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Interview review", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/1 of 1 submitted main answers evaluated/),
  ).toBeVisible();
  await expect(page.getByText("Not scored", { exact: true })).toBeVisible();
  await expect(page.getByText(/^Lexical coverage: [0-4] \/ 4\./)).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("interview-review.png"),
    fullPage: true,
  });
}
