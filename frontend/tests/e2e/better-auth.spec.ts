import { test, expect, restrictToLocal } from "./fixtures";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { Pool } from "pg";

test("Better Auth local cookie, profile, upload, persistence and isolation journey", async ({
  page,
  browser,
  baseURL,
}) => {
  test.skip(
    process.env.AUTH_BROWSER_TEST !== "true",
    "Requires the isolated auth database runner.",
  );
  test.setTimeout(240000);
  if (
    !baseURL ||
    !["localhost", "127.0.0.1"].includes(new URL(baseURL).hostname)
  )
    throw new Error("This auth journey requires the disposable local stack.");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/app/dashboard");
  await expect(page).toHaveURL(/\/sign-in$/);
  await page.goto("/sign-up");
  await page.setViewportSize({ width: 375, height: 900 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByLabel("Email address").fill("browser-one@example.test");
  await page.getByLabel("Password").fill("Synthetic-password-0001");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page).toHaveURL(/\/app\/dashboard$/);
  await page.goto("/app/settings");
  await page
    .getByLabel("Target role", { exact: true })
    .fill("Synthetic Backend Engineer");
  await page.getByRole("button", { name: "Save profile", exact: true }).click();
  await expect(
    page.getByText("Profile saved. Your preparation direction is up to date."),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Target role", { exact: true })).toHaveValue(
    "Synthetic Backend Engineer",
  );
  const nextTab = await page.context().newPage();
  await nextTab.goto("/app/settings");
  await expect(nextTab.getByLabel("Target role", { exact: true })).toHaveValue(
    "Synthetic Backend Engineer",
  );
  await nextTab.close();
  await page.goto("/app/resume");
  await page.getByLabel("PDF resume", { exact: true }).setInputFiles({
    name: "synthetic-private.pdf",
    mimeType: "application/pdf",
    buffer: await readFile(
      new URL("./fixtures/synthetic-resume.pdf", import.meta.url),
    ),
  });
  const uploaded = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/account/resumes") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Upload PDF", exact: true }).click();
  const response = await uploaded;
  expect(response.status()).toBe(201);
  const resume: unknown = await response.json();
  if (
    !resume ||
    typeof resume !== "object" ||
    !("id" in resume) ||
    typeof resume.id !== "string"
  )
    throw new Error("Invalid upload response");
  await expect(
    page.getByRole("heading", { name: "synthetic-private.pdf", exact: true }),
  ).toBeVisible();
  const cookies = await page.context().cookies();
  const session = cookies.find(
    (c) => c.name === "interview-auth.session_token",
  );
  expect(session?.httpOnly).toBe(true);
  expect(session?.sameSite).toBe("Lax");
  expect((await page.request.get("/api/v1/account/dashboard")).status()).toBe(
    401,
  );
  const secondContext = await browser.newContext();
  const blocked = await restrictToLocal(secondContext, baseURL);
  const second = await secondContext.newPage();
  try {
    await second.goto("/sign-up");
    await second.getByLabel("Email address").fill("browser-two@example.test");
    await second.getByLabel("Password").fill("Synthetic-password-0002");
    await second
      .getByRole("button", { name: "Create account", exact: true })
      .click();
    await expect(second).toHaveURL(/\/app\/dashboard$/);
    // A signed-in cookie precedes the account bootstrap POST. Wait for the
    // owned workspace to load before testing authorization of a foreign ID.
    await second.goto("/app/settings");
    await expect(second.getByLabel("Target role", { exact: true })).toHaveValue(
      "",
    );
    const tokenResponse = await second.request.get("/api/auth/token");
    const tokenData: unknown = await tokenResponse.json();
    if (
      !tokenData ||
      typeof tokenData !== "object" ||
      !("token" in tokenData) ||
      typeof tokenData.token !== "string"
    )
      throw new Error("No API token for second synthetic user");
    const foreign = await second.request.get(
      "/api/v1/account/resumes/" + resume.id,
      {
        headers: { Authorization: "Bearer " + tokenData.token },
      },
    );
    expect(foreign.status()).toBe(404);
    expect(blocked()).toEqual([]);
  } finally {
    await secondContext.close();
  }
  if (process.env.AUTH_SCREENSHOT_DIR)
    await page.screenshot({
      path: join(process.env.AUTH_SCREENSHOT_DIR, "account-mobile.png"),
      fullPage: true,
    });
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/app/dashboard");
  await expect(page).toHaveURL(/\/sign-in$/);
  await page.getByLabel("Email address").fill("browser-one@example.test");
  await page.getByLabel("Password").fill("incorrect-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByLabel("Password").fill("Synthetic-password-0001");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/app\/dashboard$/);
  // Switch identities in the same browser context: cached owner data must clear.
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  // Sign-out redirects to the public home; finish that navigation before a new one.
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/sign-in");
  await page.getByLabel("Email address").fill("browser-two@example.test");
  await page.getByLabel("Password").fill("Synthetic-password-0002");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/app\/dashboard$/);
  await page.goto("/app/settings");
  await expect(page.getByLabel("Target role", { exact: true })).toHaveValue("");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/sign-in");
  await page.getByLabel("Email address").fill("browser-one@example.test");
  await page.getByLabel("Password").fill("Synthetic-password-0001");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/app\/dashboard$/);
  await page.goto("/app/settings");
  await expect(page.getByLabel("Target role", { exact: true })).toHaveValue(
    "Synthetic Backend Engineer",
  );
  // Operator-side expiry on this runner's disposable DB, never an app endpoint.
  const database = new URL(
    process.env.TEST_AUTH_DATABASE_URL ?? "http://invalid",
  );
  if (
    !["localhost", "127.0.0.1"].includes(database.hostname) ||
    !database.pathname.endsWith("_test")
  )
    throw new Error("Expiry fixture requires the disposable local database");
  const pool = new Pool({ connectionString: database.toString(), max: 1 });
  try {
    await pool.query(
      'UPDATE auth.session SET "expiresAt"=CURRENT_TIMESTAMP WHERE "userId" IN (SELECT id FROM auth."user" WHERE email=$1)',
      ["browser-one@example.test"],
    );
  } finally {
    await pool.end();
  }
  expect((await page.request.get("/api/auth/token")).status()).toBe(401);
  await page.reload();
  await expect(page).toHaveURL(/\/sign-in$/);
  expect(errors).toEqual([]);
});
