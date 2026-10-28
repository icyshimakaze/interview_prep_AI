// Physical-device test utilities. No browser-wide settings, tab inventory or tracing.
import { chromium } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";
import { join } from "node:path";

export function requireCondition(condition, label) {
  if (!condition) throw new Error(label);
}

export async function deviceHarness(origin, folder, secrets = []) {
  const adb = process.env.ANDROID_ADB_PATH;
  const serial = process.env.ANDROID_SERIAL;
  const endpoint = process.env.ANDROID_CDP_URL;
  requireCondition(
    adb && serial && endpoint?.startsWith("http://127.0.0.1:"),
    "device_transport",
  );
  let browser, page, session;
  const results = [],
    screenshots = [];
  const responses = [];
  const restarts = [];
  const ownedCookieHashes = new Set();
  const cookieHash = (value) =>
    createHash("sha256").update(value).digest("hex");
  let errors = 0;
  async function attach() {
    if (!browser?.isConnected())
      browser = await chromium.connectOverCDP(endpoint, { timeout: 15000 });
    page = browser
      .contexts()[0]
      ?.pages()
      .findLast((candidate) => candidate.url().startsWith(origin + "/"));
    requireCondition(page, "owned_android_tab_not_found");
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(30000);
    page.on("pageerror", () => errors++);
    page.on("response", (response) => {
      const url = new URL(response.url());
      if (url.origin === origin && url.pathname.startsWith("/api/")) {
        responses.push({ path: url.pathname, status: response.status() });
        if (responses.length > 20) responses.shift();
      }
    });
    session = await page.context().newCDPSession(page);
    await session.send("Network.enable");
  }
  await attach();
  const api = async (path, token, method = "GET", body) =>
    page.evaluate(
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
    const response = await api("/api/auth/token");
    requireCondition(
      response.status === 200 && typeof response.body?.token === "string",
      "api_token",
    );
    return response.body.token;
  };
  const touch = async (locator) => {
    await locator.waitFor({ state: "visible" });
    // Move focus out of text inputs so Android's software keyboard cannot cover
    // the target. A trial click checks stable bounds without activating it.
    await locator.focus();
    await locator.scrollIntoViewIfNeeded();
    await locator.click({ trial: true });
    requireCondition(await locator.isEnabled(), "touch_target_disabled");
    const box = await locator.boundingBox();
    requireCondition(
      box && box.width > 0 && box.height > 0,
      "touch_target_bounds",
    );
    await session.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [
        {
          x: box.x + box.width / 2,
          y: box.y + box.height / 2,
          radiusX: 2,
          radiusY: 2,
          force: 1,
        },
      ],
    });
    await session.send("Input.dispatchTouchEvent", {
      type: "touchEnd",
      touchPoints: [],
    });
  };
  async function step(name, action) {
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
      let reason = error instanceof Error ? error.message : "unknown_failure";
      // Playwright's multiline navigation log contains OAuth URLs/state/client IDs.
      // Retain only the first safe diagnostic line, never the navigation transcript.
      reason = reason
        .split("\n")[0]
        .replace(/https?:\/\/\S+/g, "[REDACTED-URL]");
      for (const secret of secrets.filter(Boolean))
        reason = reason.replaceAll(secret, "[REDACTED]");
      reason = reason.replace(/eyJ[A-Za-z0-9_.-]{30,}/g, "[REDACTED-TOKEN]");
      results.push({
        name,
        status: "failed",
        ms: Date.now() - start,
        reason: reason.slice(0, 2000),
        alert_count: await page
          .getByRole("alert")
          .count()
          .catch(() => -1),
        form_count: await page
          .locator("form")
          .count()
          .catch(() => -1),
        owned_cookie: await cookieState().catch(() => null),
        path: new URL(page.url()).pathname,
        recent_responses: responses.slice(-10),
      });
      if (new URL(page.url()).origin === origin)
        await screenshot("android-failed-" + results.length).catch(
          () => undefined,
        );
      throw new Error(name);
    } finally {
      save();
    }
  }
  function save() {
    writeFileSync(
      join(folder, "android-results.json"),
      JSON.stringify(
        {
          physical: true,
          origin,
          status: results.some((result) => result.status === "failed")
            ? "failed"
            : "in_progress",
          results,
          restarts,
          screenshots,
          page_errors: errors,
          hosted_https_auth: "pending",
          ios: "pending",
        },
        null,
        2,
      ),
    );
  }
  async function screenshot(name) {
    await page.screenshot({
      path: join(folder, name + ".png"),
      // Android CDP full-page capture can repeat viewport tiles; keep evidence
      // to the real page viewport rather than treating stitching as layout.
      fullPage: false,
      style:
        'input[type="password"], input[type="email"] { visibility: hidden !important; }',
    });
    screenshots.push(name + ".png");
    save();
  }
  async function reopen() {
    const observation = { before: await cookieState(), started: Date.now() };
    restarts.push(observation);
    try {
      // Explicit browser restart required by the physical persistence test; never clears app data.
      execFileSync(
        adb,
        ["-s", serial, "shell", "am", "force-stop", "com.android.chrome"],
        { stdio: "pipe", timeout: 20000 },
      );
      // The old CDP connection belongs to the terminated browser. Discard it
      // without sending Browser.close to a user's subsequently reopened Chrome.
      browser = undefined;
      execFileSync(
        adb,
        [
          "-s",
          serial,
          "shell",
          "am",
          "start",
          "-a",
          "android.intent.action.VIEW",
          "-d",
          origin + "/app/settings",
          "-p",
          "com.android.chrome",
          "--ez",
          "create_new_tab",
          "true",
        ],
        { stdio: "pipe", timeout: 20000 },
      );
      const reconnectDeadline = Date.now() + 30000;
      while (Date.now() < reconnectDeadline) {
        try {
          await attach();
          await page.waitForLoadState("domcontentloaded");
          return;
        } catch (error) {
          const label =
            error instanceof Error ? error.message : "unknown_failure";
          observation.attachment_error = /^[a-z_]{1,80}$/.test(label)
            ? label
            : "cdp_transport_unavailable";
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }
      throw new Error("chrome_restart_attachment");
    } finally {
      observation.after = await cookieState().catch(() => ({
        present: false,
        unavailable: true,
      }));
      observation.elapsed_ms = Date.now() - observation.started;
      delete observation.started;
      save();
    }
  }
  async function cookieState() {
    if (!browser?.isConnected() || !page || page.isClosed())
      return { present: false, unavailable: true };
    const cookie = (await page.context().cookies(origin)).find(
      (item) => item.name === "interview-auth.session_token",
    );
    return cookie
      ? {
          present: true,
          persistent: cookie.expires > Date.now() / 1000,
          httpOnly: cookie.httpOnly,
          sameSite: cookie.sameSite,
          secure: cookie.secure,
          remaining_seconds: Math.floor(cookie.expires - Date.now() / 1000),
        }
      : { present: false };
  }
  async function waitForOwnedReturn(path, timeout = 180000) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      if (!browser?.isConnected() || !page || page.isClosed()) {
        // Provider selection can replace the initiating Android Chrome tab.
        // Keep forwarding alive while waiting for an origin-owned return tab.
        try {
          await attach();
        } catch {
          /* Provider UI can still be open. */
        }
      }
      if (page && !page.isClosed()) {
        const url = new URL(page.url());
        if (url.origin === origin && url.pathname === path) {
          await page.waitForLoadState("domcontentloaded");
          return;
        }
        if (url.origin === origin && url.searchParams.has("social_error"))
          throw new Error("live_provider_callback_rejected");
        const returned = browser
          .contexts()[0]
          ?.pages()
          .find((candidate) => candidate.url().startsWith(origin + path));
        if (returned && returned !== page) await attach();
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    throw new Error("live_provider_return_timed_out");
  }
  return {
    get page() {
      return page;
    },
    get session() {
      return session;
    },
    step,
    api,
    token,
    touch,
    screenshot,
    reopen,
    cookieState,
    waitForOwnedReturn,
    results,
    async rememberOwnedCookie() {
      for (const cookie of await page.context().cookies(origin))
        if (cookie.name === "interview-auth.session_token")
          ownedCookieHashes.add(cookieHash(cookie.value));
    },
    async finish(status) {
      save();
      const payload = JSON.parse(
        await import("node:fs").then(({ readFileSync }) =>
          readFileSync(join(folder, "android-results.json"), "utf8"),
        ),
      );
      payload.status = status;
      writeFileSync(
        join(folder, "android-results.json"),
        JSON.stringify(payload, null, 2),
      );
      for (const cookie of await page.context().cookies(origin)) {
        if (
          cookie.name === "interview-auth.session_token" &&
          ownedCookieHashes.has(cookieHash(cookie.value))
        )
          await page.context().clearCookies({
            name: cookie.name,
            domain: cookie.domain,
            path: cookie.path,
          });
      }
      // Close only this run's origin-scoped tabs, never the user's other tabs/browser.
      for (const owned of browser
        .contexts()[0]
        ?.pages()
        .filter((candidate) => candidate.url().startsWith(origin + "/")) ?? [])
        await owned.close().catch(() => undefined);
    },
  };
}
