// Signed SYNTHETIC provider transport; no live provider/account verification.
import { chromium, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { writeFileSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { Pool } from "pg";
import {
  deviceHarness,
  requireCondition as check,
} from "./android-support.mjs";

const origin = process.env.SOCIAL_TEST_ORIGIN;
const folder = process.env.SOCIAL_TEST_ARTIFACTS;
const database = new URL(process.env.AUTH_DATABASE_URL ?? "http://invalid");
check(
  origin &&
    folder &&
    new URL(origin).hostname === "localhost" &&
    ["localhost", "127.0.0.1"].includes(database.hostname) &&
    database.pathname.endsWith("_test") &&
    process.env.GOOGLE_CLIENT_ID ===
      "synthetic-google-client.apps.googleusercontent.com",
  "owned_synthetic_target",
);
const physical = Boolean(process.env.ANDROID_CDP_URL);
const pool = new Pool({ connectionString: database.toString(), max: 1 });
const results = [];
let browser, h;
let status = "failed",
  persona = "alice",
  consent = "allow",
  pageErrors = 0,
  failureReason;
const save = () =>
  writeFileSync(
    join(folder, "social-results.json"),
    JSON.stringify(
      {
        synthetic_provider_transport: true,
        live_provider_verified: false,
        physical,
        status,
        results,
        page_errors: pageErrors,
        hosted_https: "pending",
        ...(failureReason ? { failure_reason: failureReason } : {}),
      },
      null,
      2,
    ),
  );
try {
  if (physical)
    h = await deviceHarness(origin, folder, [
      process.env.BETTER_AUTH_SECRET,
      process.env.GOOGLE_CLIENT_SECRET,
      process.env.GITHUB_CLIENT_SECRET,
      database.toString(),
    ]);
  else {
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const context = await browser.newContext({
      viewport: { width: 1280, height: 900 },
    });
    const page = await context.newPage();
    h = {
      page,
      touch: (locator) => locator.click(),
      screenshot: (name) =>
        page.screenshot({ path: join(folder, name + ".png"), fullPage: false }),
      step: async (name, action) => {
        const start = Date.now();
        try {
          const evidence = await action();
          results.push({
            name,
            status: "passed",
            ms: Date.now() - start,
            ...(evidence ? { evidence } : {}),
          });
        } catch (error) {
          results.push({
            name,
            status: "failed",
            ms: Date.now() - start,
            reason:
              error instanceof Error
                ? error.message.split("\n")[0].slice(0, 160)
                : "unknown_failure",
          });
          throw new Error("synthetic_browser_step");
        } finally {
          save();
        }
      },
    };
  }
  const api = (path, token, method = "GET", body) =>
    h.page.evaluate(
      async (input) => {
        const response = await fetch(input.path, {
          method: input.method,
          headers: {
            ...(input.token ? { Authorization: "Bearer " + input.token } : {}),
            ...(input.body ? { "Content-Type": "application/json" } : {}),
          },
          body: input.body ? JSON.stringify(input.body) : undefined,
        });
        return {
          status: response.status,
          body: await response.json().catch(() => null),
        };
      },
      { path, token, method, body },
    );
  const token = async () => {
    const result = await api("/api/auth/token");
    check(result.status === 200 && result.body.token, "actual_api_token");
    return result.body.token;
  };
  const subject = (value) =>
    JSON.parse(Buffer.from(value.split(".")[1], "base64url")).sub;
  const goto = (path) =>
    h.page.goto(origin + path, { waitUntil: "domcontentloaded" });
  async function routes() {
    h.page.on("pageerror", () => pageErrors++);
    await h.page.route(
      /^https:\/\/(accounts\.google\.com|github\.com)\//,
      async (route) => {
        const url = new URL(route.request().url());
        const provider =
          url.hostname === "accounts.google.com" ? "google" : "github";
        check(
          url.searchParams.get("redirect_uri") ===
            origin + "/api/auth/callback/" + provider &&
            url.searchParams.get("code_challenge_method") === "S256" &&
            url.searchParams.get("state"),
          "authorization_binding",
        );
        const query = new URLSearchParams({
          state: url.searchParams.get("state"),
        });
        if (provider === "google") {
          query.set("scope", "openid profile email");
          query.set("authuser", "0");
        }
        if (consent === "deny") {
          query.set("error", "access_denied");
          query.set("error_description", "synthetic-private-description");
        } else
          query.set(
            "code",
            persona === "bob" ? "synthetic-bob" : "synthetic-code",
          );
        await route.fulfill({
          status: 302,
          headers: {
            location: origin + "/api/auth/callback/" + provider + "?" + query,
          },
        });
      },
    );
  }
  await routes();
  const signIn = async (provider) => {
    await goto("/sign-in");
    await h.touch(
      h.page.getByRole("button", {
        name: "Continue with " + provider,
        exact: true,
      }),
    );
    await expect(h.page).toHaveURL(origin + "/app/dashboard");
    check(
      (await api("/api/v1/account/session", await token(), "POST", {}))
        .status === 200,
      "bootstrap_current_principal",
    );
    if (physical) await h.rememberOwnedCookie();
  };
  const signOut = async () => {
    await h.touch(
      h.page.getByRole("button", { name: "Sign out", exact: true }),
    );
    await expect(h.page).toHaveURL(origin + "/");
  };
  const step = h.step;
  await step("both_opt_in_buttons_and_password_closed_signup", async () => {
    for (const path of ["/sign-in", "/sign-up"]) {
      await goto(path);
      for (const name of ["Google", "GitHub"])
        await expect(
          h.page.getByRole("button", {
            name: "Continue with " + name,
            exact: true,
          }),
        ).toBeEnabled();
      if (path === "/sign-in")
        await expect(
          h.page.getByLabel("Password", { exact: true }),
        ).toBeVisible();
      else
        await expect(
          h.page.getByRole("heading", { name: "Registration is closed" }),
        ).toBeVisible();
      await h.screenshot("social-" + path.slice(1));
    }
    check(
      (await api("/api/auth/sign-up/email", undefined, "POST", {})).status ===
        404,
      "password_signup_closed",
    );
  });
  let aliceSubject, aliceTarget;
  await step("google_callback_session_api_and_saved_profile", async () => {
    await signIn("Google");
    const value = await token();
    aliceSubject = subject(value);
    await goto("/app/settings");
    await h.page
      .getByLabel("Target role", { exact: true })
      .fill("SYNTHETIC-SOCIAL-ALICE");
    await h.touch(
      h.page.getByRole("button", { name: "Save profile", exact: true }),
    );
    await expect(
      h.page.getByText(
        "Profile saved. Your preparation direction is up to date.",
      ),
    ).toBeVisible();
    await h.page.reload();
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "SYNTHETIC-SOCIAL-ALICE",
    );
    const target = await api("/api/v1/account/targets", value, "POST", {
      title: "Synthetic OAuth job",
      description:
        "A harmless synthetic owned job requiring Python and testing.",
    });
    check(target.status === 201, "owned_target_created");
    aliceTarget = target.body.id;
  });
  if (physical) {
    try {
      await step("immediate_social_force_stop_persistence", async () => {
        await h.reopen();
        await routes();
        await expect(
          h.page.getByLabel("Target role", { exact: true }),
        ).toHaveValue("SYNTHETIC-SOCIAL-ALICE");
      });
    } catch {
      await routes();
      await step("recover_social_after_retained_restart_failure", async () => {
        await signIn("Google");
        check(
          subject(await token()) === aliceSubject,
          "stable_returning_subject",
        );
      });
    }
  }
  await step(
    "explicit_github_link_same_owner_then_returning_sign_in",
    async () => {
      await goto("/app/account-access");
      await h.touch(
        h.page.getByRole("button", { name: "Connect GitHub", exact: true }),
      );
      await expect(h.page).toHaveURL(origin + "/app/account-access");
      // The link redirect returns to the same path; wait for persisted account proof.
      await expect
        .poll(
          async () =>
            (
              await pool.query(
                "SELECT count(*)::int AS count FROM auth.account WHERE \"providerId\"='github'",
              )
            ).rows[0].count,
        )
        .toBe(1);
      await signOut();
      await signIn("GitHub");
      check(
        subject(await token()) === aliceSubject,
        "explicit_link_retains_auth_owner",
      );
      await goto("/app/settings");
      await expect(
        h.page.getByLabel("Target role", { exact: true }),
      ).toHaveValue("SYNTHETIC-SOCIAL-ALICE");
      await h.screenshot("social-linked-profile");
    },
  );
  if (physical) {
    try {
      await step("immediate_github_force_stop_persistence", async () => {
        await h.reopen();
        await routes();
        await expect(
          h.page.getByLabel("Target role", { exact: true }),
        ).toHaveValue("SYNTHETIC-SOCIAL-ALICE");
      });
    } catch {
      await routes();
      await step("recover_github_after_retained_restart_failure", async () => {
        await signIn("GitHub");
        check(subject(await token()) === aliceSubject, "github_owner_retained");
      });
    }
  }
  await step("logout_revokes_bearer_and_switch_isolates_data", async () => {
    const previous = await token();
    await signOut();
    check(
      (await api("/api/v1/account/dashboard", previous)).status === 401,
      "immediate_revocation",
    );
    persona = "bob";
    await signIn("Google");
    const bob = await token();
    check(subject(bob) !== aliceSubject, "distinct_subject");
    check(
      (await api("/api/v1/account/targets/" + aliceTarget, bob)).status === 404,
      "foreign_target_denied",
    );
    check(
      (await api("/api/v1/account/profile", bob)).body === null,
      "foreign_profile_absent",
    );
    await signOut();
    persona = "alice";
    check(
      (
        await api("/api/auth/link-social", undefined, "POST", {
          provider: "google",
        })
      ).status === 401,
      "signed_out_link_denied",
    );
  });
  await step(
    "denied_consent_sanitized_retry_and_accessible_layout",
    async () => {
      consent = "deny";
      await goto("/sign-in");
      await h.touch(
        h.page.getByRole("button", {
          name: "Continue with Google",
          exact: true,
        }),
      );
      await expect(h.page).toHaveURL(origin + "/sign-in?social_error=1");
      await expect(h.page.locator("form").getByRole("alert")).toBeVisible();
      check(
        !(await h.page.locator("body").innerText()).includes(
          "synthetic-private-description",
        ),
        "no_raw_provider_error",
      );
      check(
        !h.page.url().includes("error_description"),
        "no_error_description_url",
      );
      for (const width of physical ? [null] : [375, 1280]) {
        if (width) await h.page.setViewportSize({ width, height: 900 });
        check(
          await h.page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          "no_horizontal_overflow",
        );
        const scan = await new AxeBuilder({ page: h.page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        check(scan.violations.length === 0, "axe_violations");
      }
      await h.screenshot("social-consent-error");
    },
  );
  const retainedFailure = physical
    ? h.results.some((item) => item.status === "failed")
    : results.some((item) => item.status === "failed");
  status = retainedFailure ? "failed" : "passed";
} catch (error) {
  const label = error instanceof Error ? error.message : "unknown_failure";
  failureReason = /^[a-z_]{1,80}$/.test(label)
    ? label
    : "browser_transport_failure";
  console.error(
    "Synthetic social browser test stopped; see bounded statuses. No credentials logged.",
  );
} finally {
  await pool.end();
  if (physical && h) {
    await h.finish(status);
    const evidence = JSON.parse(
      readFileSync(join(folder, "android-results.json"), "utf8"),
    );
    results.push(...evidence.results);
  }
  if (browser) await browser.close();
  save();
  console.log(
    JSON.stringify({
      synthetic_social_browser: status,
      physical,
      evidence: folder,
    }),
  );
  process.exit(status === "passed" ? 0 : 1);
}
