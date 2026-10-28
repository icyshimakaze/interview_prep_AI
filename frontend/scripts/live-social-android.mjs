// Real providers, user-controlled test consent; owned disposable localhost fixture only.
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import {
  deviceHarness,
  requireCondition as check,
} from "./android-support.mjs";

const origin = process.env.ANDROID_TEST_ORIGIN;
const folder = process.env.ANDROID_TEST_ARTIFACTS;
check(
  origin === "http://localhost:3001" &&
    folder &&
    process.env.LOCAL_LIVE_OAUTH === "true",
  "owned_live_fixture_required",
);
let h,
  status = "failed",
  failureReason;
// Chrome termination intentionally removes the CDP socket. Keep this bounded
// operator test alive until reconnection completes or its own deadline fails.
const keepAlive = setInterval(() => {}, 1000);
const callbacks = [];
const metadata = {};
const stage = (name) => {
  writeFileSync(
    join(folder, "live-android-stage.json"),
    JSON.stringify({ stage: name }),
  );
  console.log(JSON.stringify({ live_android_stage: name }));
};
try {
  h = await deviceHarness(origin, folder);
  const observeCallbacks = () =>
    h.page.on("response", (response) => {
      const url = new URL(response.url());
      if (
        url.origin === origin &&
        /^\/api\/auth\/callback\/(google|github)$/.test(url.pathname)
      )
        callbacks.push({
          provider: url.pathname.split("/").at(-1),
          status: response.status(),
        });
    });
  observeCallbacks();
  const api = (path, token, method = "GET", body) =>
    h.api(path, token, method, body);
  const claims = (value) =>
    JSON.parse(Buffer.from(value.split(".")[1], "base64url"));
  const callbackEvents = () => {
    check(process.env.LIVE_CALLBACK_LOG, "owned_callback_observation_required");
    return readFileSync(process.env.LIVE_CALLBACK_LOG, "utf8")
      .split("\n")
      .filter((line) => line.startsWith('{"local_oauth_callback":'))
      .map((line) => JSON.parse(line));
  };
  async function login(provider) {
    await h.page.goto(origin + "/sign-in", { waitUntil: "domcontentloaded" });
    stage("complete_" + provider.toLowerCase() + "_consent_on_phone");
    const name = provider.toLowerCase();
    const previousCallbacks = callbackEvents().filter(
      (event) => event.local_oauth_callback === name,
    ).length;
    const initiation = h.page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.origin === origin &&
        url.pathname === "/api/auth/sign-in/social" &&
        response.request().postDataJSON()?.provider === name
      );
    });
    const expectedHost =
      name === "google" ? "accounts.google.com" : "github.com";
    const navigation = h.page.waitForRequest(
      (request) =>
        request.isNavigationRequest() &&
        new URL(request.url()).hostname === expectedHost,
    );
    // Select the exact DOM control on the physical browser; native touch
    // ergonomics remain a separate manual check, not a provider-proof shortcut.
    await h.page
      .getByRole("button", {
        name: "Continue with " + provider,
        exact: true,
      })
      .click();
    const started = await initiation;
    check(started.status() === 200, "matching_provider_initiation");
    const authorization = new URL((await navigation).url());
    check(
      authorization.protocol === "https:" &&
        authorization.hostname === expectedHost,
      "matching_provider_authorization_host",
    );
    const callbackDeadline = Date.now() + 600000;
    let received = false;
    while (Date.now() < callbackDeadline) {
      const event = callbackEvents().filter(
        (item) => item.local_oauth_callback === name,
      )[previousCallbacks];
      if (event) {
        check(event.result === "success", "live_provider_callback_rejected");
        callbacks.push({
          provider: name,
          status: 302,
          observation: "matching_fixture_callback",
        });
        received = true;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    check(received, "matching_provider_callback_timeout");
    // Human account selection/2FA is provisioning, not an app latency assertion.
    await h.waitForOwnedReturn("/app/dashboard", 600000);
    observeCallbacks();
    await h.page
      .getByRole("button", { name: "Sign out", exact: true })
      .waitFor({ state: "visible", timeout: 15000 });
    const value = await h.token();
    const payload = claims(value);
    check(
      payload.exp - payload.iat === 60 &&
        payload.iss === origin &&
        payload.azp === origin &&
        payload.sid,
      "exact_live_api_claims",
    );
    check(
      (await api("/api/v1/account/session", value, "POST", {})).status === 200,
      "live_principal_bootstrap",
    );
    await h.rememberOwnedCookie();
    const cookie = await h.cookieState();
    check(
      cookie.present &&
        cookie.persistent &&
        cookie.httpOnly &&
        cookie.sameSite === "Lax" &&
        !cookie.secure,
      "development_cookie_attributes",
    );
    return { value, subject: payload.sub, session: payload.sid };
  }
  async function logout(value) {
    const current = await h.token();
    const sameSession = claims(current).sid === claims(value).sid;
    check(sameSession, "logout_test_requires_current_session");
    const before = await api("/api/v1/account/dashboard", current);
    check(before.status === 200, "live_bearer_valid_before_logout");
    check(
      (await api("/api/auth/sign-out", undefined, "POST", {})).status === 200,
      "live_logout_response",
    );
    const after = await api("/api/v1/account/dashboard", current);
    (metadata.logout_checks ??= []).push({
      current_session_matched: sameSession,
      before: before.status,
      after: after.status,
    });
    check(after.status === 401, "live_logout_revocation");
    check(!(await h.cookieState()).present, "live_logout_cookie_removed");
  }
  async function recover(provider, expectedSubject) {
    const response = await api("/api/auth/token");
    if (
      response.status === 200 &&
      claims(response.body.token).sub === expectedSubject
    ) {
      const payload = claims(response.body.token);
      return {
        value: response.body.token,
        subject: payload.sub,
        session: payload.sid,
      };
    }
    return login(provider);
  }
  let google, github, target;
  await h.step("physical_auth_controls_and_responsive_layout", async () => {
    await h.page.goto(origin + "/sign-in", { waitUntil: "domcontentloaded" });
    for (const provider of ["Google", "GitHub"]) {
      const button = h.page.getByRole("button", {
        name: "Continue with " + provider,
        exact: true,
      });
      await button.waitFor({ state: "visible" });
      const bounds = await button.boundingBox();
      check(bounds && bounds.height >= 44, "mobile_auth_target_height");
    }
    const dimensions = await h.page.evaluate(() => ({
      width: innerWidth,
      content: document.documentElement.scrollWidth,
    }));
    check(
      dimensions.content <= dimensions.width,
      "mobile_auth_no_horizontal_overflow",
    );
    await h.screenshot("live-mobile-sign-in");
    return dimensions;
  });
  if (process.env.LIVE_RETURNING_ONLY === "true") {
    const expected = JSON.parse(
      readFileSync(process.env.LIVE_EXPECTED_IDENTITIES, "utf8"),
    );
    for (const provider of ["Google", "GitHub"]) {
      await h.step(
        "real_" + provider.toLowerCase() + "_returning_phone_login",
        async () => {
          const returning = await login(provider);
          const fingerprint = createHash("sha256")
            .update(returning.subject)
            .digest("hex");
          check(
            fingerprint === expected[provider.toLowerCase()],
            "returning_existing_auth_identity",
          );
          const response = await api(
            "/api/v1/account/targets",
            returning.value,
          );
          check(response.status === 200, "returning_targets_read");
          const ownsSavedTarget = response.body.items.some(
            (item) => item.title === "SYNTHETIC-LIVE-ANDROID",
          );
          check(
            ownsSavedTarget === (provider === "Google"),
            "returning_saved_work_ownership",
          );
          await logout(returning.value);
        },
      );
    }
  } else {
    await h.step("real_google_first_phone_login", async () => {
      google = await login("Google");
    });
    await h.step("real_google_api_save_refresh_and_cookie", async () => {
      const saved = await api("/api/v1/account/targets", google.value, "POST", {
        title: "SYNTHETIC-LIVE-ANDROID",
        description:
          "Synthetic test job for Python development and testing. No real personal content.",
      });
      check(saved.status === 201, "live_owned_target_created");
      target = saved.body.id;
      await h.page.reload();
      check(
        claims(await h.token()).sub === google.subject,
        "live_google_refresh_identity",
      );
      metadata.google_cookie_before_restart = await h.cookieState();
    });
    try {
      await h.step("real_google_force_stop_reopen", async () => {
        const start = Date.now();
        await h.reopen();
        observeCallbacks();
        metadata.google_restart_ms = Date.now() - start;
        metadata.google_cookie_after_restart = await h.cookieState();
        const resumed = await h.token();
        check(
          claims(resumed).sub === google.subject,
          "live_google_restart_identity",
        );
        metadata.google_same_session_after_restart =
          claims(resumed).sid === google.session;
        check(
          metadata.google_same_session_after_restart,
          "live_google_restart_session_changed",
        );
        google.value = resumed;
      });
    } catch {
      await h.step("real_google_recovery_if_cookie_lost", async () => {
        const recovered = await recover("Google", google.subject);
        check(
          recovered.subject === google.subject,
          "live_google_recovery_same_identity",
        );
        google = recovered;
        check(
          (await api("/api/v1/account/targets/" + target, google.value))
            .status === 200,
          "live_saved_target_retained",
        );
      });
    }
    await h.step("real_google_logout_revokes_api_session", () =>
      logout(google.value),
    );
    await h.step("real_github_first_phone_login", async () => {
      github = await login("GitHub");
    });
    await h.step("real_github_switch_isolates_google_work", async () => {
      check(github.subject !== google.subject, "distinct_live_test_accounts");
      check(
        (await api("/api/v1/account/targets/" + target, github.value))
          .status === 404,
        "live_foreign_target_denied",
      );
      await h.page.reload();
      check(
        claims(await h.token()).sub === github.subject,
        "live_github_refresh_identity",
      );
      metadata.github_cookie_before_restart = await h.cookieState();
    });
    try {
      await h.step("real_github_force_stop_reopen", async () => {
        const start = Date.now();
        await h.reopen();
        observeCallbacks();
        metadata.github_restart_ms = Date.now() - start;
        metadata.github_cookie_after_restart = await h.cookieState();
        const resumed = await h.token();
        check(
          claims(resumed).sub === github.subject,
          "live_github_restart_identity",
        );
        metadata.github_same_session_after_restart =
          claims(resumed).sid === github.session;
        check(
          metadata.github_same_session_after_restart,
          "live_github_restart_session_changed",
        );
        github.value = resumed;
      });
    } catch {
      await h.step("real_github_recovery_if_cookie_lost", async () => {
        const recovered = await recover("GitHub", github.subject);
        check(
          recovered.subject === github.subject,
          "live_github_recovery_same_identity",
        );
        github = recovered;
      });
    }
    await h.step("real_github_logout_revokes_api_session", () =>
      logout(github.value),
    );
    await h.step("real_google_returning_phone_login", async () => {
      const returning = await login("Google");
      check(
        returning.subject === google.subject,
        "returning_google_same_identity",
      );
      check(
        (await api("/api/v1/account/targets/" + target, returning.value))
          .status === 200,
        "returning_google_retains_work",
      );
      await logout(returning.value);
    });
    await h.step("real_github_returning_phone_login", async () => {
      const returning = await login("GitHub");
      check(
        returning.subject === github.subject,
        "returning_github_same_identity",
      );
      await logout(returning.value);
    });
  }
  // A provider handoff can replace the tab before CDP attaches. Retain the
  // callback assertion using the fixture's enum-only server observation too.
  if (process.env.LIVE_CALLBACK_LOG) {
    for (const line of readFileSync(
      process.env.LIVE_CALLBACK_LOG,
      "utf8",
    ).split("\n")) {
      if (!line.startsWith('{"local_oauth_callback":')) continue;
      const event = JSON.parse(line);
      if (
        ["google", "github"].includes(event.local_oauth_callback) &&
        event.result === "success"
      )
        callbacks.push({
          provider: event.local_oauth_callback,
          status: 302,
          observation: "fixture_server",
        });
    }
  }
  check(
    callbacks.some(
      (item) =>
        item.provider === "google" && item.status >= 300 && item.status < 400,
    ) &&
      callbacks.some(
        (item) =>
          item.provider === "github" && item.status >= 300 && item.status < 400,
      ),
    "both_real_callbacks_observed",
  );
  status = h.results.some((result) => result.status === "failed")
    ? "failed"
    : "passed";
} catch (error) {
  const label = error instanceof Error ? error.message : "unknown_failure";
  failureReason = /^[a-z_]{1,80}$/.test(label)
    ? label
    : "browser_transport_failure";
} finally {
  clearInterval(keepAlive);
  if (h)
    await h.finish(status).catch(() => {
      failureReason ??= "browser_closed_before_cleanup";
    });
  writeFileSync(
    join(folder, "live-android-result.json"),
    JSON.stringify(
      {
        status,
        failure_reason: failureReason,
        synthetic_provider_transport: false,
        callbacks,
        metadata,
        hosted_https: false,
      },
      null,
      2,
    ),
  );
  stage("finished_" + status);
  // End the automation connection after evidence/cleanup; leave Chrome running.
  process.exit(status === "passed" ? 0 : 1);
}
