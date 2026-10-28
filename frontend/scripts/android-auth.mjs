// Real Android Chrome; private synthetic account provisioning against the owned local DB only.
import { registerHooks } from "node:module";
import { randomBytes, createPublicKey, verify } from "node:crypto";
import { globSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { Pool } from "pg";
import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {
  deviceHarness,
  requireCondition as check,
} from "./android-support.mjs";

registerHooks({
  resolve(specifier, context, next) {
    return next(
      specifier.startsWith("./") &&
        context.parentURL?.includes("/src/lib/better-auth/") &&
        !specifier.endsWith(".ts")
        ? specifier + ".ts"
        : specifier,
      context,
    );
  },
});
const { createBetterAuth } = await import("../src/lib/better-auth/factory.ts");
const origin = process.env.ANDROID_TEST_ORIGIN;
const folder = process.env.ANDROID_TEST_ARTIFACTS;
const database = new URL(process.env.AUTH_DATABASE_URL ?? "http://invalid");
check(
  origin &&
    new URL(origin).hostname === "localhost" &&
    folder &&
    ["localhost", "127.0.0.1"].includes(database.hostname) &&
    database.pathname.endsWith("_test"),
  "owned_local_target",
);
check(
  process.env.AUTH_LOCAL_REGISTRATION_ENABLED === "false",
  "registration_must_stay_closed",
);
const pool = new Pool({ connectionString: database.toString(), max: 1 });
const accounts = ["one", "two"].map((label) => ({
  name: "Synthetic Android " + label,
  email: "android-" + label + "@example.invalid",
  password: randomBytes(24).toString("base64url"),
}));
let h,
  status = "failed";
try {
  const auth = createBetterAuth(pool, {
    origin,
    secret: process.env.BETTER_AUTH_SECRET,
    rateLimitKey: process.env.AUTH_RATE_LIMIT_KEY,
    production: false,
    registrationEnabled: true,
  });
  for (const body of accounts) await auth.api.signUpEmail({ body });
  await pool.query("DELETE FROM auth.session");
  const unverified = await pool.query(
    'SELECT count(*)::int AS count FROM auth."user" WHERE NOT "emailVerified"',
  );
  check(unverified.rows[0]?.count === 2, "synthetic_users_remain_unverified");
  h = await deviceHarness(origin, folder, [
    ...accounts.map((account) => account.password),
    process.env.BETTER_AUTH_SECRET,
    process.env.AUTH_RATE_LIMIT_KEY,
    database.toString(),
  ]);
  const step = h.step;
  const goto = (path) =>
    h.page.goto(origin + path, { waitUntil: "domcontentloaded" });
  const button = (name) => h.page.getByRole("button", { name, exact: true });
  const login = async (account, password = account.password) => {
    await goto("/sign-in");
    await expect(button("Sign in")).toBeEnabled();
    await h.page.getByLabel("Email address").fill(account.email);
    await h.page.getByLabel("Password", { exact: true }).fill(password);
    const response = h.page.waitForResponse(
      (candidate) =>
        candidate.url().endsWith("/api/auth/sign-in/email") &&
        candidate.request().method() === "POST",
    );
    await h.touch(button("Sign in"));
    const result = await response;
    if (result.status() === 200) {
      await h.rememberOwnedCookie();
      await expect(h.page).toHaveURL(origin + "/app/dashboard");
    }
    return result.status();
  };
  const readyProfile = async () => {
    await goto("/app/settings");
    await expect(
      h.page.getByLabel("Target role", { exact: true }),
    ).toBeVisible();
  };
  await step("physical_device_and_landing", async () => {
    await goto("/");
    const metrics = await h.page.evaluate(() => ({
      userAgent: navigator.userAgent,
      touchPoints: navigator.maxTouchPoints,
      width: innerWidth,
      screenWidth: screen.width,
      dpr: devicePixelRatio,
      coarse: matchMedia("(pointer: coarse)").matches,
      overflow: document.documentElement.scrollWidth > innerWidth,
      secureContext: isSecureContext,
    }));
    check(
      metrics.touchPoints > 0 && metrics.coarse && !metrics.overflow,
      "actual_mobile_metrics",
    );
    await h.screenshot("android-landing");
    return metrics;
  });
  await step("public_registration_closed_private_fixture_only", async () => {
    await goto("/sign-up");
    check(
      /registration.*closed/i.test(await h.page.locator("body").innerText()),
      "signup_closed_ui",
    );
    const response = await h.api(
      "/api/auth/sign-up/email",
      undefined,
      "POST",
      accounts[0],
    );
    check(response.status === 404, "signup_closed_http");
    await h.screenshot("android-signup-closed");
    return {
      public_status: response.status,
      private_synthetic_users: 2,
      email_verified: false,
    };
  });
  await step("incorrect_password_login", async () => {
    check(
      (await login(accounts[0], "Incorrect-synthetic-password")) === 401,
      "incorrect_password_http_401",
    );
    await expect(h.page.locator("form").getByRole("alert")).toBeVisible();
    check(
      new URL(h.page.url()).pathname === "/sign-in",
      "incorrect_login_stays_signed_out",
    );
  });
  await step("correct_password_and_first_party_cookie", async () => {
    check((await login(accounts[0])) === 200, "correct_password_http_200");
    await expect(h.page).toHaveURL(/\/app\/dashboard$/);
    await readyProfile();
    const cookies = await h.page.context().cookies(origin);
    const cookie = cookies.find(
      (candidate) => candidate.name === "interview-auth.session_token",
    );
    check(
      cookie?.httpOnly &&
        cookie.sameSite === "Lax" &&
        cookie.domain === "localhost",
      "host_only_cookie",
    );
    check(
      !(await h.page.evaluate(() => document.cookie)).includes("session_token"),
      "http_only_cookie",
    );
    return {
      httpOnly: cookie.httpOnly,
      sameSite: cookie.sameSite,
      host: cookie.domain,
      secure: cookie.secure,
      persistent: cookie.expires > Date.now() / 1000,
      scope: "local HTTP development; hosted Secure cookie pending",
    };
  });
  await step("profile_save_and_refresh_persistence", async () => {
    await h.page
      .getByLabel("Target role", { exact: true })
      .fill("ANDROID-ALICE");
    await h.touch(button("Save profile"));
    await expect(
      h.page.getByText(
        "Profile saved. Your preparation direction is up to date.",
      ),
    ).toBeVisible();
    await h.page.reload();
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "ANDROID-ALICE",
    );
    await h.screenshot("android-profile");
  });
  try {
    await step("physical_chrome_force_close_reopen_persistence", async () => {
      await h.reopen();
      await expect(
        h.page.getByLabel("Target role", { exact: true }),
      ).toHaveValue("ANDROID-ALICE");
      return { actual_package_restart: true, storage_state_import: false };
    });
  } catch {
    // Preserve the failed result, then recover only our synthetic session so
    // independent expiry/isolation journeys can still produce real evidence.
    await step("recover_synthetic_login_after_restart_failure", async () => {
      check((await login(accounts[0])) === 200, "restart_recovery_login");
      await readyProfile();
      await expect(
        h.page.getByLabel("Target role", { exact: true }),
      ).toHaveValue("ANDROID-ALICE");
    });
  }
  const oldToken = await h.token();
  const claims = JSON.parse(Buffer.from(oldToken.split(".")[1], "base64url"));
  await step("actual_rs256_signature_and_claims", async () => {
    const header = JSON.parse(Buffer.from(oldToken.split(".")[0], "base64url"));
    const keys = await h.api("/api/auth/jwks");
    const jwk = keys.body.keys.find(
      (candidate) => candidate.kid === header.kid,
    );
    check(
      header.alg === "RS256" &&
        jwk &&
        claims.exp - claims.iat === 60 &&
        claims.nbf === claims.iat &&
        claims.iss === origin &&
        claims.azp === origin &&
        claims.aud === "interview-prep-api" &&
        claims.sid,
      "token_claims",
    );
    check(
      verify(
        "RSA-SHA256",
        Buffer.from(oldToken.split(".").slice(0, 2).join(".")),
        createPublicKey({ key: jwk, format: "jwk" }),
        Buffer.from(oldToken.split(".")[2], "base64url"),
      ),
      "independent_signature",
    );
    check(
      (await h.api("/api/v1/account/dashboard", oldToken)).status === 200,
      "backend_accepts_actual_token",
    );
    return {
      algorithm: "RS256",
      lifetime_seconds: 60,
      independent_signature: true,
      backend_status: 200,
    };
  });
  await step("mobile_menu_and_navigation_touch", async () => {
    await h.touch(
      h.page.getByRole("button", { name: "Open navigation", exact: true }),
    );
    const dialog = h.page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await h.touch(
      dialog.getByRole("link", { name: "Question Bank", exact: true }),
    );
    await expect(
      h.page.getByRole("table", { name: "Question bank results" }),
    ).toBeVisible();
  });
  await step("question_practice", async () => {
    await goto("/app/questions");
    await h.page.getByLabel("Search questions").fill("Two Sum");
    await h.touch(button("Search"));
    await h.touch(button("Two Sum Problem"));
    await h.page
      .getByLabel("Your response", { exact: true })
      .fill("Synthetic practice: check the complement among earlier values.");
    await h.touch(
      h.page.getByRole("button", { name: "Submit for self-review" }),
    );
    await expect(
      h.page.getByText(/Synthetic practice: check the complement/),
    ).toBeVisible();
    await h.screenshot("android-question-practice");
  });
  await step("assessment_answer_save_and_submit", async () => {
    await goto("/app/assessments");
    await h.page
      .getByRole("combobox", { name: "Assessment category", exact: true })
      .selectOption("DBMS");
    await h.page
      .getByRole("combobox", { name: "Assessment difficulty", exact: true })
      .selectOption("easy");
    await h.page.getByLabel("Number of questions", { exact: true }).fill("1");
    await h.touch(button("Start assessment"));
    for (const label of [
      "Atomicity prevents a failed transaction from leaving only some of its changes committed.",
      "Durability means committed changes survive a crash and recovery.",
    ])
      await h.page.getByLabel(label, { exact: true }).check();
    await h.touch(button("Save response"));
    await expect(h.page.getByRole("status")).toContainText("Response saved.");
    await h.touch(button("Submit assessment"));
    await expect(
      h.page.getByRole("heading", {
        name: "Category performance",
        exact: true,
      }),
    ).toBeVisible();
    await h.screenshot("android-assessment");
  });
  let interviewId;
  await step("interview_answer_review_and_history", async () => {
    await goto("/app/interviews");
    await h.page.getByLabel("Main questions", { exact: true }).fill("1");
    const created = h.page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/account/interviews") &&
        response.request().method() === "POST",
    );
    await h.touch(button("Start interview"));
    const data = await (await created).json();
    interviewId = data.session.id;
    await h.page
      .getByLabel("Your answer", { exact: true })
      .fill("Synthetic Android answer: validate input and compare tradeoffs.");
    await h.touch(button("Submit answer"));
    await h.touch(button("Complete interview"));
    await expect(
      h.page.getByRole("heading", { name: "Interview review", exact: true }),
    ).toBeVisible();
    await expect(h.page.getByText(/Synthetic Android answer:/)).toBeVisible();
    await h.screenshot("android-interview-review");
    await goto("/app/interviews");
    await expect(button("Review interview").first()).toBeVisible();
  });
  await step("resume_multipart_from_physical_browser", async () => {
    await goto("/app/resume");
    const bytes = [
      ...readFileSync(
        new URL("../tests/e2e/fixtures/synthetic-resume.pdf", import.meta.url),
      ),
    ];
    await h.page
      .getByLabel("PDF resume", { exact: true })
      .evaluate((input, payload) => {
        const data = new DataTransfer();
        data.items.add(
          new File([new Uint8Array(payload)], "android-synthetic.pdf", {
            type: "application/pdf",
          }),
        );
        input.files = data.files;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }, bytes);
    const uploaded = h.page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/account/resumes") &&
        response.request().method() === "POST",
    );
    await h.touch(button("Upload PDF"));
    check((await uploaded).status() === 201, "physical_multipart_upload");
    await expect(
      h.page.getByRole("heading", {
        name: "android-synthetic.pdf",
        exact: true,
      }),
    ).toBeVisible();
    await h.screenshot("android-resume");
    return {
      status: 201,
      native_file_picker: "manual_pending",
      input: "synthetic in-memory File on Android",
    };
  });
  await step("offline_error_and_retry_on_physical_target", async () => {
    await readyProfile();
    await h.session.send("Network.emulateNetworkConditions", {
      offline: true,
      latency: 0,
      downloadThroughput: 0,
      uploadThroughput: 0,
    });
    try {
      let failed = false;
      try {
        await h.api("/api/v1/account/dashboard", await h.token());
      } catch {
        failed = true;
      }
      check(failed, "physical_offline_fetch_fails");
    } finally {
      await h.session.send("Network.emulateNetworkConditions", {
        offline: false,
        latency: 0,
        downloadThroughput: -1,
        uploadThroughput: -1,
      });
    }
    const abortApi = (route) => route.abort("internetdisconnected");
    await h.page.route("**/api/v1/**", abortApi);
    try {
      await goto("/app/settings");
      await expect(
        h.page.getByRole("button", { name: "Try again", exact: true }),
      ).toBeVisible();
      await h.screenshot("android-network-error");
    } finally {
      await h.page.unroute("**/api/v1/**", abortApi);
    }
    await h.touch(
      h.page.getByRole("button", { name: "Try again", exact: true }),
    );
    await expect(h.page.getByLabel("Target role", { exact: true })).toBeVisible(
      { timeout: 15000 },
    );
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "ANDROID-ALICE",
    );
    return { scope: "owned CDP page; phone Wi-Fi/cellular settings unchanged" };
  });
  await step("physical_reopen_after_normal_workspace_use", async () => {
    await h.reopen();
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "ANDROID-ALICE",
    );
    return {
      actual_package_restart: true,
      storage_state_import: false,
      scenario: "after practice, assessment, interview and upload",
    };
  });
  await step("expired_jwt_rejected_and_token_refresh", async () => {
    while (Date.now() / 1000 <= claims.exp + 6)
      await new Promise((resolve) => setTimeout(resolve, 500));
    check(
      (await h.api("/api/v1/account/dashboard", oldToken)).status === 401,
      "expired_jwt_rejected",
    );
    check(
      (await h.api("/api/v1/account/dashboard", await h.token())).status ===
        200,
      "fresh_jwt_accepted",
    );
    return { expired: 401, refreshed: 200 };
  });
  let aliceToken;
  await step("logout_cookie_and_immediate_fastapi_revocation", async () => {
    aliceToken = await h.token();
    await h.touch(button("Sign out"));
    await expect(h.page).toHaveURL(origin + "/");
    check(
      (await h.api("/api/auth/get-session")).body === null,
      "logout_session_null",
    );
    check(
      (await h.api("/api/v1/account/dashboard", aliceToken)).status === 401,
      "logout_revokes_bearer",
    );
    check(
      !(await h.page.context().cookies(origin)).some(
        (cookie) => cookie.name === "interview-auth.session_token",
      ),
      "logout_cookie_deleted",
    );
  });
  await step("browser_back_and_protected_page_after_logout", async () => {
    await h.page.goBack();
    await h.page.reload();
    check(
      !(await h.page.getByLabel("Target role", { exact: true }).isVisible()),
      "no_private_controls_after_back",
    );
    await goto("/app/dashboard");
    await expect(h.page).toHaveURL(/\/sign-in$/);
  });
  await step("login_after_logout_account_switch_and_isolation", async () => {
    await login(accounts[1]);
    await expect(h.page).toHaveURL(/\/app\/dashboard$/);
    await readyProfile();
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "",
    );
    const bob = await h.token();
    check(
      (await h.api("/api/v1/account/interviews/" + interviewId, bob)).status ===
        404,
      "foreign_interview_denied",
    );
    const history = await h.api("/api/v1/account/interviews", bob);
    check(
      history.status === 200 &&
        !JSON.stringify(history.body).includes(interviewId),
      "foreign_history_absent",
    );
    await h.touch(button("Sign out"));
    await login(accounts[0]);
    await expect(h.page).toHaveURL(/\/app\/dashboard$/);
    await readyProfile();
    await expect(h.page.getByLabel("Target role", { exact: true })).toHaveValue(
      "ANDROID-ALICE",
    );
    check(
      (
        await h.api(
          "/api/v1/account/interviews/" + interviewId,
          await h.token(),
        )
      ).status === 200,
      "alice_history_retained",
    );
  });
  await step("accessibility_and_actual_viewport", async () => {
    const findings = await new AxeBuilder({ page: h.page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    check(findings.violations.length === 0, "axe_violations");
    check(
      await h.page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "mobile_horizontal_overflow",
    );
    await h.screenshot("android-final-profile");
    return { axe_violations: 0, manual_touch_ergonomics: "pending" };
  });
  await step("database_session_expiry_and_private_ui_clear", async () => {
    const fresh = await h.token();
    await pool.query(
      'UPDATE auth.session SET "expiresAt"=CURRENT_TIMESTAMP WHERE "userId" IN (SELECT id FROM auth."user" WHERE email=$1)',
      [accounts[0].email],
    );
    check(
      (await h.api("/api/v1/account/dashboard", fresh)).status === 401,
      "session_expiry_backend",
    );
    check(
      (await h.api("/api/auth/token")).status === 401,
      "session_expiry_token",
    );
    await h.page.reload();
    await expect(h.page).toHaveURL(/\/sign-in$/);
  });
  status = h.results.some((result) => result.status === "failed")
    ? "failed"
    : "passed";
} catch {
  console.error(
    "Physical Android journey stopped; see sanitized step statuses (no credentials logged).",
  );
} finally {
  const files = [
    "api.log",
    "frontend.log",
    "android-results.json",
    ...globSync("frontend/.next/{static,dev/static}/**/*.js", { cwd: folder }),
  ];
  let matches = 0;
  for (const file of files) {
    const payload = readFileSync(join(folder, file));
    if (
      accounts.some((account) =>
        payload.includes(Buffer.from(account.password)),
      )
    )
      matches++;
  }
  writeFileSync(
    join(folder, "android-password-scan.json"),
    JSON.stringify({ files: files.length, password_matches: matches }),
  );
  if (matches) status = "failed";
  if (h) await h.finish(status);
  await pool.end();
  writeFileSync(
    join(folder, "android-summary.json"),
    JSON.stringify(
      {
        status,
        physical: true,
        email: "deferred",
        hosted_https_auth: "pending",
        ios: "pending",
      },
      null,
      2,
    ),
  );
  console.log(
    JSON.stringify({ physical_android_status: status, evidence: folder }),
  );
  process.exit(status === "passed" ? 0 : 1);
}
