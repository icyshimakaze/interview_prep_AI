import { test as base, expect, type BrowserContext } from "@playwright/test";

export { expect };
export type { Page } from "@playwright/test";

export async function restrictToLocal(
  context: BrowserContext,
  baseURL: string,
): Promise<() => string[]> {
  const origin = new URL(baseURL).origin;
  const blocked: string[] = [];
  await context.route("**/*", async (route) => {
    const destination = new URL(route.request().url()).origin;
    if (destination !== origin) {
      blocked.push(destination);
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  return () => blocked;
}

export const test = base.extend({
  context: async ({ context, baseURL }, provideContext) => {
    if (!baseURL) throw new Error("A local frontend baseURL is required.");
    const blocked = await restrictToLocal(context, baseURL);
    await provideContext(context);
    expect(
      blocked(),
      "Browser tests must not contact external services",
    ).toEqual([]);
  },
});
