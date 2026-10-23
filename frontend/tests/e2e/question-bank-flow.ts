import { expect, test, type Page } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

export async function checkQuestionBank(page: Page) {
  await page.goto("/demo/questions");
  await expect(
    page.getByRole("table", { name: "Question bank results" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Difficulty", exact: true })
    .selectOption("hard");
  await expect(page.getByRole("status")).toContainText("2 matching questions");
  await expect(
    page.getByRole("button", {
      name: "Design a bounded short-link service",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(page.getByRole("button", { name: "Next page" })).toBeEnabled();
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page.getByRole("status")).toContainText("page 2");
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await page.getByLabel("Search questions").fill("Two Sum");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("1 matching questions");
  await page.getByRole("button", { name: "Bookmark: Two Sum Problem" }).click();
  await expect(
    page.getByRole("button", { name: "Remove bookmark: Two Sum Problem" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Bookmarks", exact: true })
    .selectOption("yes");
  await expect(
    page.getByRole("button", { name: "Two Sum Problem", exact: true }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("question-bank-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("question-bank-mobile.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Two Sum Problem", exact: true })
    .click();
  await expect(
    page.getByText(/Submit a response to this question version/),
  ).toBeVisible();
  await page
    .getByLabel("Your response", { exact: true })
    .fill(
      "Fictional practice: track earlier values and check the complement without reusing an index.",
    );
  await page.getByRole("button", { name: "Submit for self-review" }).click();
  await expect(
    page.getByText(
      "Look up the complement among elements visited before the current index.",
    ),
  ).toBeVisible();
  await expect(
    page.getByText(/Fictional practice: track earlier values/),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("question-review-mobile.png"),
    fullPage: true,
  });
  await page.reload();
  await page.getByLabel("Search questions").fill("Two Sum");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("button", { name: /^Filters/ }).click();
  await page
    .getByRole("combobox", { name: "Attempted state", exact: true })
    .selectOption("yes");
  await expect(page.getByRole("status")).toContainText("1 matching questions");
  await page
    .getByRole("button", { name: "Two Sum Problem", exact: true })
    .click();
  await page.getByText("Delete this saved practice response").click();
  await page
    .getByRole("button", { name: "Delete response", exact: true })
    .click();
  await expect(page.getByText("No submitted attempts yet.")).toBeVisible();
  await expect(
    page.getByText(/Submit a response to this question version/),
  ).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/demo");
}
