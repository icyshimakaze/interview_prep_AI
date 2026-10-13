import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("frontend reaches the real backend and PostgreSQL", async ({ page }) => {
  await page.goto("/status");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Verify connection" }).click();
  await expect(page.getByRole("status")).toContainText(
    "API connected · PostgreSQL connected",
  );
  await expect(page.getByRole("status")).toContainText("0004_resume_evidence");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("foundation-desktop.png"),
    fullPage: true,
  });
});

test("database/API failure remains recoverable", async ({ page }) => {
  await page.route("**/api/v1/health/ready", (route) =>
    route.fulfill({ status: 503, json: { code: "unavailable" } }),
  );
  await page.goto("/status");
  await page.getByRole("button", { name: "Verify connection" }).click();
  await expect(page.getByRole("status")).toContainText(
    "API or database is not ready",
  );
  await expect(page.getByRole("button", { name: "Try again" })).toBeEnabled();
});

test("mobile layout and keyboard navigation", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Try Interactive Demo" }),
  ).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: test.info().outputPath("foundation-mobile.png"),
    fullPage: true,
  });
});
