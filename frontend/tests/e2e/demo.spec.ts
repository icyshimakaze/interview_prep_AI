import { expect, test, restrictToLocal } from "./fixtures";
import { checkCandidateContext } from "./candidate-flow";
import { checkProjectDefense } from "./project-defense-flow";
import { checkRoadmap, checkProgress } from "./planning-flow";
import { parseRoadmap } from "../../src/lib/api/planning";
import AxeBuilder from "@axe-core/playwright";
import { parseDashboard } from "../../src/lib/api/workspace";
import { checkQuestionBank } from "./question-bank-flow";
import { checkAssessments } from "./assessment-flow";
import { checkInterviews } from "./interview-flow";
import { checkResumeUpload } from "./resume-flow";

// Two real demo creations consume the production hourly budget. Retrying this
// journey would test quota exhaustion instead of the original failure.
test.describe.configure({ retries: 0 });

test("isolated fictional demo persists edits, rejects foreign IDs, and erases on exit", async ({
  page,
  browser,
  baseURL,
}) => {
  // One candidate journey uses two visitors without bypassing the production demo quota.
  test.setTimeout(180000);
  if (!baseURL) throw new Error("A local frontend baseURL is required.");
  const secondContext = await browser.newContext();
  const blocked = await restrictToLocal(secondContext, baseURL);
  const second = await secondContext.newPage();
  try {
    await page.goto("/");
    const dashboardResponse = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/demo/dashboard") &&
        response.request().method() === "GET",
    );
    await page
      .getByRole("link", { name: "Try Interactive Demo", exact: true })
      .click();
    expect((await dashboardResponse).status()).toBe(200);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      "Aarav Rao (fictional)",
    );
    await expect(page.getByLabel("Demo disclosure")).toContainText(
      "no real platform usage",
    );
    const firstResponse = await page.request.get("/api/v1/demo/dashboard");
    expect(firstResponse.status()).toBe(200);
    const first = parseDashboard(await firstResponse.json());
    const firstResume = first.resumes[0];
    if (!firstResume)
      throw new Error("The demo must include its sample resume.");
    await checkCandidateContext(page, first);
    await test.step("question filtering, bookmarks and self-review", () =>
      checkQuestionBank(page));
    const firstAssessment =
      await test.step("saved assessments and objective scoring", () =>
        checkAssessments(page));
    await test.step("mock interview pause, follow-up and completion", () =>
      checkInterviews(page));
    await page.getByRole("link", { name: "Skill Matrix", exact: true }).click();
    await expect(page.getByRole("table")).toContainText("Python");
    const target = first.targets[0];
    if (!target) throw new Error("The demo must include a target.");
    await page.getByLabel("Target job").selectOption(target.id);
    await expect(page.getByRole("table")).toContainText("Mentioned");
    await expect(page.getByRole("table")).toContainText(
      "Needs assessment validation",
    );
    await page.getByText("Why this priority? Sources for Python").click();
    await expect(
      page.getByText(/Original excerpt: Fictional project/).first(),
    ).toBeVisible();
    const matrixAccessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(matrixAccessibility.violations).toEqual([]);
    await page.screenshot({
      path: test.info().outputPath("skill-matrix-live.png"),
      fullPage: true,
    });
    await page.getByRole("link", { name: "Assessments", exact: true }).click();
    await expect(
      page.getByText("4 saved attempts", { exact: true }),
    ).toBeVisible();
    const firstProject = await checkProjectDefense(page);
    const firstRoadmap = await checkRoadmap(page);
    await checkProgress(page);
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await page.screenshot({
      path: test.info().outputPath("persisted-progress.png"),
      fullPage: true,
    });
    const uploadedResume =
      await test.step("personal PDF upload, review and reload", () =>
        checkResumeUpload(page));
    await second.goto(`${baseURL}/demo`);
    await expect(second.getByRole("heading", { level: 1 })).toContainText(
      "Aarav",
    );
    await second.getByRole("link", { name: "Roadmap", exact: true }).click();
    await expect(
      second.getByRole("heading", {
        name: "Personal preparation roadmap",
        exact: true,
      }),
    ).toBeVisible();
    const isolatedPlan = parseRoadmap(
      await (await second.request.get(`${baseURL}/api/v1/demo/roadmap`)).json(),
    );
    expect(isolatedPlan.current?.id).not.toBe(firstRoadmap);
    expect(isolatedPlan.history).toHaveLength(0);
    expect(
      (
        await second.request.get(
          `${baseURL}/api/v1/demo/projects/${firstProject}`,
        )
      ).status(),
    ).toBe(404);
    const foreign = await second.request.get(
      `${baseURL}/api/v1/demo/resumes/${firstResume.id}`,
    );
    expect(foreign.status()).toBe(404);
    expect(
      (
        await second.request.get(
          `${baseURL}/api/v1/demo/resume-library/${uploadedResume}`,
        )
      ).status(),
    ).toBe(404);
    expect(
      (
        await second.request.get(
          `${baseURL}/api/v1/demo/assessments/${firstAssessment}`,
        )
      ).status(),
    ).toBe(404);
    await page.getByRole("button", { name: "Exit and delete demo" }).click();
    await page.getByRole("button", { name: "Delete demo and exit" }).click();
    await expect(page).toHaveURL(`${baseURL}/`);
    expect((await page.request.get("/api/v1/demo/dashboard")).status()).toBe(
      401,
    );
    await second.getByRole("button", { name: "Exit and delete demo" }).click();
    await second.getByRole("button", { name: "Delete demo and exit" }).click();
    await expect(second).toHaveURL(`${baseURL}/`);
  } finally {
    // Each browser can erase only its own capability, including on failed checks.
    for (const context of [page.context(), secondContext]) {
      const cookies = await context.cookies().catch(() => []);
      const csrf = cookies.find(
        (cookie) => cookie.name === "interview_prep_csrf",
      )?.value;
      if (csrf && baseURL)
        await context.request.delete(`${baseURL}/api/v1/demo/session`, {
          headers: { Origin: new URL(baseURL).origin, "X-CSRF-Token": csrf },
        });
    }
    await secondContext.close();
    expect(blocked(), "Second visitor must also remain local").toEqual([]);
  }
});

test("account routes clearly explain missing Clerk setup", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(
    page.getByRole("heading", { name: "Account sign-in is unavailable" }),
  ).toBeVisible();
  await page.goto("/sign-up");
  await expect(
    page.getByRole("link", { name: "Try Interactive Demo" }),
  ).toBeVisible();
  await page.goto("/app/dashboard");
  await expect(
    page.getByRole("heading", { name: "Account sign-in is unavailable" }),
  ).toBeVisible();
});
