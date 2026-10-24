import { expect, test, type Page } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";
import { workspaceFixture } from "../workspace-fixture";
import { resumeFixture } from "../resume-fixture";
import { roadmap, progress } from "../planning-fixture";
import {
  sectionHref,
  workspaceSections,
} from "../../src/components/workspace/navigation";

// These fixtures exercise frontend states only; the real service/ownership
// regression remains in demo.spec.ts against an isolated PostgreSQL database.
async function mockDemo(page: Page) {
  await page.route("**/api/v1/demo/resume-library", (route) =>
    route.fulfill({ json: { items: [{ ...resumeFixture, is_sample: true }] } }),
  );
  await page.route("**/api/v1/demo/roadmap", (route) =>
    route.fulfill({ json: { ...roadmap(), mode: "demo" } }),
  );
  await page.route("**/api/v1/demo/progress", (route) =>
    route.fulfill({ json: { ...progress(), mode: "demo" } }),
  );
  await page.route("**/api/v1/demo/projects", (route) =>
    route.fulfill({ json: { items: [] } }),
  );
  await page.route("**/api/v1/demo/sessions", (route) =>
    route.fulfill({ json: {} }),
  );
  await page.route("**/api/v1/demo/dashboard", (route) =>
    route.fulfill({ json: workspaceFixture }),
  );
  await page.route("**/api/v1/demo/questions/facets", (route) =>
    route.fulfill({ json: { categories: [], subtopics: [], roles: [] } }),
  );
  await page.route("**/api/v1/demo/questions?*", (route) =>
    route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 12 } }),
  );
  await page.route("**/api/v1/demo/assessments/options", (route) =>
    route.fulfill({
      json: {
        inventory: [],
        max_questions: 12,
        duration_hours: 24,
        conceptual_provider: "MockAIProvider",
        conceptual_kind: "simulation",
      },
    }),
  );
  await page.route("**/api/v1/demo/assessments?*", (route) =>
    route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 10 } }),
  );
  await page.route("**/api/v1/demo/interviews/options", (route) =>
    route.fulfill({
      json: {
        inventory: [],
        provider: {
          name: "MockAIProvider",
          version: "mock-lexical-v1",
          kind: "simulation",
          model: null,
          disclosure: "Demo/simulated practice; not verified competence.",
        },
        targets: [],
        max_followups: 3,
        answer_limit: 10000,
        notices: ["Frontend fixture; no live interview data."],
      },
    }),
  );
  await page.route("**/api/v1/demo/interviews?*", (route) =>
    route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 10 } }),
  );
  await page.route("**/api/v1/demo/skill-evidence", (route) =>
    route.fulfill({
      json: {
        policy_version: "skill-evidence-v1",
        mode: "demo",
        target_id: null,
        targets: [],
        rows: [],
        notices: ["Fictional demo sources never validate real competence."],
      },
    }),
  );
}
async function checkAccessibility(page: Page) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(result.violations).toEqual([]);
}

test("public product sections, privacy and footer are usable and accessible", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Prepare for your next interview.",
  );
  for (const id of ["product", "how-it-works", "features", "privacy"])
    await expect(page.locator(`#${id}`)).toBeVisible();
  await checkAccessibility(page);
  await page.screenshot({
    path: test.info().outputPath("landing-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("link", { name: "Read about privacy & data" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Know what you’re sharing.",
  );
  await checkAccessibility(page);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await checkAccessibility(page);
  await page.screenshot({
    path: test.info().outputPath("landing-mobile.png"),
    fullPage: true,
  });
});

for (const section of workspaceSections) {
  test(`${section.label} supports deep links, accessible content and narrow screens`, async ({
    page,
  }) => {
    await mockDemo(page);
    await page.goto(sectionHref("demo", section.slug));
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByLabel("Demo disclosure")).toBeVisible();
    await expect(
      page
        .getByRole("navigation", { name: "Workspace navigation" })
        .getByRole("link", { name: section.label, exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await checkAccessibility(page);
    await page.screenshot({
      path: test.info().outputPath(`${section.slug}-desktop.png`),
      fullPage: true,
    });
    for (const width of [375, 320]) {
      await page.setViewportSize({ width, height: 812 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await checkAccessibility(page);
      await page.screenshot({
        path: test.info().outputPath(`${section.slug}-${width}.png`),
        fullPage: true,
      });
    }
  });
}

test("mobile question filters preserve selections when collapsed and remain keyboard operable", async ({
  page,
}) => {
  await mockDemo(page);
  await page.setViewportSize({ width: 320, height: 812 });
  await page.goto("/demo/questions");
  const toggle = page.getByRole("button", { name: "Filters", exact: true });
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  const difficulty = page.getByRole("combobox", {
    name: "Difficulty",
    exact: true,
  });
  await expect(difficulty).not.toBeVisible();
  await toggle.focus();
  await page.keyboard.press("Enter");
  await expect(difficulty).toBeVisible();
  await difficulty.selectOption("hard");
  const activeToggle = page.getByRole("button", {
    name: "Filters (1 active)",
    exact: true,
  });
  await activeToggle.click();
  await expect(difficulty).not.toBeVisible();
  await activeToggle.focus();
  await page.keyboard.press("Space");
  await expect(difficulty).toHaveValue("hard");
  await expect(activeToggle).toHaveAttribute("aria-expanded", "true");
  await checkAccessibility(page);
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(difficulty).toHaveValue("");
  expect(
    await page
      .getByLabel("Search questions")
      .evaluate((element) => element.getBoundingClientRect().width),
  ).toBeGreaterThanOrEqual(240);
});

test("keyboard skip link and reduced motion remain available", async ({
  page,
}) => {
  await mockDemo(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/demo");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
  expect(
    await page
      .getByRole("link", { name: "Dashboard", exact: true })
      .evaluate((element) =>
        parseFloat(getComputedStyle(element).transitionDuration),
      ),
  ).toBeLessThanOrEqual(0.01);
});

test("mobile menu and deletion dialog contain focus, close on Escape, and recover from failure", async ({
  page,
}) => {
  await mockDemo(page);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/demo");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const menu = page.getByRole("button", { name: "Open navigation" });
  await menu.click();
  const navigation = page.getByRole("dialog", { name: "Navigation" });
  await expect(navigation).toBeVisible();
  await checkAccessibility(page);
  await page.keyboard.press("Escape");
  await expect(menu).toBeFocused();
  await menu.click();
  await navigation.getByRole("link", { name: "Resume", exact: true }).click();
  await expect(page).toHaveURL(/\/demo\/resume$/);
  await expect(navigation).not.toBeVisible();
  await expect(page.locator("#main-content")).toBeFocused();
  const exit = page.getByRole("button", { name: "Exit and delete demo" });
  await exit.click();
  const dialog = page.getByRole("dialog", {
    name: "Delete this demo workspace?",
  });
  await expect(
    dialog.getByRole("button", { name: "Close dialog" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(
    dialog.getByRole("button", { name: "Delete demo and exit" }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    dialog.getByRole("button", { name: "Close dialog" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(exit).toBeFocused();
  await exit.click();
  await page.route("**/api/v1/demo/session", (route) =>
    route.fulfill({ status: 503, json: {} }),
  );
  await dialog.getByRole("button", { name: "Delete demo and exit" }).click();
  await expect(dialog.getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(
    dialog.getByRole("button", { name: "Keep exploring" }),
  ).toBeEnabled();
  await checkAccessibility(page);
  await dialog.getByRole("button", { name: "Keep exploring" }).click();
  await expect(
    page.getByRole("heading", { name: "Resume", exact: true }),
  ).toBeVisible();
});

test("failed workspace load exposes a retry and recovers to the requested section", async ({
  page,
}) => {
  await mockDemo(page);
  let requests = 0;
  await page.route("**/api/v1/demo/dashboard", (route) => {
    requests += 1;
    return requests === 1
      ? route.fulfill({ status: 503, json: {} })
      : route.fulfill({ json: workspaceFixture });
  });
  await page.goto("/demo/progress");
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(
    page.getByRole("heading", { name: "Progress analytics", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "No completed assessments with reviewed objective grades yet.",
    ),
  ).toBeVisible();
});
