// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  oauthCallbackReason,
  recordOAuthCallback,
} from "@/lib/better-auth/oauth-diagnostics";

const origin = "https://auth.example.test";
afterEach(() => vi.restoreAllMocks());

describe("bounded OAuth callback diagnostics", () => {
  it.each([
    "access_denied",
    "account_not_linked",
    "social_admission_closed",
    "signup_disabled",
    "state_mismatch",
    "unable_to_create_user",
    "unable_to_get_user_info",
    "email_not_verified",
  ])("retains only the fixed failure code %s", (code) => {
    expect(
      oauthCallbackReason(
        302,
        origin + "/sign-in?social_error=1&error=" + code,
        origin,
      ),
    ).toBe(code);
  });

  it("does not log any raw provider/request data or accept injected reasons", () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const sensitive = "private-code-state-email-token-secret";
    const id = recordOAuthCallback(
      "google",
      true,
      302,
      origin +
        "/sign-in?social_error=1&error=account_not_linked&code=" +
        sensitive +
        "&error_description=" +
        sensitive,
      origin,
    );
    expect(id).toMatch(/^[0-9a-f-]{36}$/);
    expect(log).toHaveBeenCalledOnce();
    expect(log.mock.calls[0]?.[0]).not.toContain(sensitive);
    expect(JSON.parse(String(log.mock.calls[0]?.[0]))).toEqual({
      event: "oauth_callback_result",
      requestId: id,
      provider: "google",
      admission: "public",
      status: 302,
      reason: "account_not_linked",
    });
    for (const location of [
      origin + "/sign-in?social_error=1&error=" + sensitive,
      origin + "/sign-in?social_error=1&error=access_denied&error=" + sensitive,
      "https://untrusted.invalid/sign-in?social_error=1&error=access_denied",
      "not a URL " + sensitive,
    ])
      expect(oauthCallbackReason(302, location, origin)).toBe(
        "unclassified_callback_failure",
      );
  });

  it("distinguishes app redirects, server failure and rejected callback requests", () => {
    for (const path of ["/app/dashboard", "/app/account-access"])
      expect(oauthCallbackReason(302, origin + path, origin)).toBe("completed");
    expect(oauthCallbackReason(503, null, origin)).toBe("auth_unavailable");
    expect(oauthCallbackReason(400, null, origin)).toBe(
      "callback_request_rejected",
    );
    expect(
      oauthCallbackReason(302, origin + "/app/dashboard?error=x", origin),
    ).toBe("unclassified_callback_failure");
  });

  it("generates a fresh reference for each account's callback", () => {
    vi.spyOn(console, "info").mockImplementation(() => undefined);
    expect(recordOAuthCallback("google", true, 302, null, origin)).not.toBe(
      recordOAuthCallback("github", false, 302, null, origin),
    );
  });

  it("does not change authentication when the log sink is unavailable", () => {
    vi.spyOn(console, "info").mockImplementation(() => {
      throw new Error("synthetic log sink failure");
    });
    expect(recordOAuthCallback("google", true, 302, null, origin)).toMatch(
      /^[0-9a-f-]{36}$/,
    );
  });
});
