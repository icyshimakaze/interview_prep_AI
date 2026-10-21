import { expect, test, type Page } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";
import { parseAssessment } from "../../src/lib/api/assessments";

async function accessible(page: Page) {
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
}
export async function checkAssessments(page: Page): Promise<string> {
  await page.goto("/demo/assessments");
  await page
    .getByRole("combobox", { name: "Assessment category", exact: true })
    .selectOption("DBMS");
  await page
    .getByRole("combobox", { name: "Assessment difficulty", exact: true })
    .selectOption("easy");
  await page.getByLabel("Number of questions", { exact: true }).fill("1");
  const startResponse = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/demo/assessments") &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Start assessment", exact: true })
    .click();
  const raw: unknown = await (await startResponse).json(),
    attempt = parseAssessment(raw);
  expect(attempt.questions[0]?.question_type).toBe("multiple_select");
  for (const key of [
    "is_correct",
    "accepted_answers",
    "correct_option_ids",
    "expected_concepts",
  ])
    expect(JSON.stringify(raw)).not.toContain(key);
  await page
    .getByLabel(
      "Atomicity prevents a failed transaction from leaving only some of its changes committed.",
      { exact: true },
    )
    .check();
  await page
    .getByLabel(
      "Durability means committed changes survive a crash and recovery.",
      { exact: true },
    )
    .check();
  await page
    .getByRole("button", { name: "Save response", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Response saved.");
  await accessible(page);
  await page.screenshot({
    path: test.info().outputPath("assessment-answer-desktop.png"),
    fullPage: true,
  });
  await page.reload();
  await page
    .getByRole("button", { name: "Resume DBMS assessment", exact: true })
    .click();
  await expect(
    page.getByLabel(
      "Durability means committed changes survive a crash and recovery.",
      { exact: true },
    ),
  ).toBeChecked();
  await page
    .getByRole("button", { name: "Submit assessment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Category performance", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("1 correct of 1", { exact: true })).toBeVisible();
  await expect(page.getByText(/Expected selections:/)).toBeVisible();
  await accessible(page);
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await accessible(page);
  await page.screenshot({
    path: test.info().outputPath("assessment-review-mobile.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Back to assessments", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Assessment category", exact: true })
    .selectOption("Computer Networks");
  await page
    .getByRole("combobox", { name: "Assessment difficulty", exact: true })
    .selectOption("easy");
  await page.getByLabel("Number of questions", { exact: true }).fill("1");
  await page
    .getByRole("button", { name: "Start assessment", exact: true })
    .click();
  await page
    .getByLabel("Your answer", { exact: true })
    .fill(
      "Hostname resolution returns address records. Caching reduces repeated lookups. TLS establishes encryption separately.",
    );
  await page
    .getByRole("button", { name: "Submit assessment", exact: true })
    .click();
  await expect(
    page.getByText(/Mock simulation: lexical overlap/),
  ).toBeVisible();
  await expect(
    page.getByText("4 of 4 · Mock simulation", { exact: true }),
  ).toBeVisible();
  await accessible(page);
  await page.screenshot({
    path: test.info().outputPath("assessment-conceptual-mobile.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  return attempt.id;
}
