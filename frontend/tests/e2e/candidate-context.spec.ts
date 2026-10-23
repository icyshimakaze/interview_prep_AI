import { accountFormPreview } from "./form-previews";
import { expect, test } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

for (const name of ["profile", "target", "resume", "skills"] as const) {
  test(`${name} form layout and accessibility on desktop and mobile`, async ({
    page,
  }) => {
    await page.goto("/");
    const styles = await page
      .locator('link[rel="stylesheet"]')
      .evaluateAll((links) => links.map((link) => link.outerHTML).join(""));
    const markup = accountFormPreview(name);
    await page.setContent(
      `<!doctype html><html lang="en"><head><title>${name} static test preview</title>${styles}</head><body class="font-sans antialiased">${markup}</body></html>`,
    );
    for (const viewport of [
      { width: 1280, height: 900 },
      { width: 375, height: 812 },
      { width: 320, height: 812 },
    ]) {
      await page.setViewportSize(viewport);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect(results.violations).toEqual([]);
      await page.screenshot({
        path: test.info().outputPath(`${name}-${viewport.width}.png`),
        fullPage: true,
      });
    }
  });
}
