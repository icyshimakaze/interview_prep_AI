import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { workspaceFixture } from "../workspace-fixture";
import {
  sectionHref,
  workspaceSections,
} from "../../src/components/workspace/navigation";

// These fixtures exercise frontend states only; the real service/ownership
// regression remains in demo.spec.ts against an isolated PostgreSQL database.
async function mockDemo(page: Page) {
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
    "Walk in witha clearer head.",
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
    if (
      section.slug === "dashboard" ||
      section.slug === "assessments" ||
      section.slug === "settings"
    )
      await page.screenshot({
        path: test.info().outputPath(`${section.slug}-desktop.png`),
        fullPage: true,
      });
    await page.setViewportSize({ width: 375, height: 812 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await checkAccessibility(page);
    if (section.slug === "dashboard" || section.slug === "assessments")
      await page.screenshot({
        path: test.info().outputPath(`${section.slug}-mobile.png`),
        fullPage: true,
      });
  });
}

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
    page.getByRole("heading", { name: "Progress", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("table", { name: "Preparation activity" }),
  ).toBeVisible();
});
