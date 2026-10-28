// @vitest-environment node
import { describe, it, expect } from "vitest";
import {
  admittedSocialIdentity,
  socialAuthSettings,
  socialProviderNames,
  SOCIAL_ERROR_PATH,
} from "@/lib/better-auth/social-settings";
import {
  safeSocialLocation,
  socialRequestBody,
  validSocialCallback,
} from "@/lib/better-auth/social-http";

const env = {
  GOOGLE_AUTH_ENABLED: "true",
  GOOGLE_CLIENT_ID: "synthetic-client.apps.googleusercontent.com",
  GOOGLE_CLIENT_SECRET: "synthetic-secret",
  GOOGLE_ALLOWED_SUBJECTS: '["synthetic-sub"]',
};
const origin = "https://auth.example.test";
describe("restricted social authentication policy", () => {
  it("requires explicit public opt-in and validates provider subjects in public mode", () => {
    const settings = socialAuthSettings({
      ...env,
      SOCIAL_REGISTRATION_MODE: "public",
      GOOGLE_ALLOWED_SUBJECTS: "[]",
      GITHUB_AUTH_ENABLED: "true",
      GITHUB_CLIENT_ID: "synthetic-github-client",
      GITHUB_CLIENT_SECRET: "synthetic-github-secret",
    });
    expect(
      admittedSocialIdentity(settings, "google", { sub: "new-public-sub" }),
    ).toBe(true);
    expect(admittedSocialIdentity(settings, "github", { id: 987654321 })).toBe(
      true,
    );
    for (const sub of [
      undefined,
      "",
      "bad@email.invalid",
      "with space",
      "x".repeat(256),
    ])
      expect(admittedSocialIdentity(settings, "google", { sub })).toBe(false);
    for (const id of [
      undefined,
      "",
      "001",
      "login",
      -1,
      1.5,
      Number.MAX_SAFE_INTEGER + 1,
    ])
      expect(admittedSocialIdentity(settings, "github", { id })).toBe(false);
    expect(admittedSocialIdentity(settings, "microsoft", { sub: "new" })).toBe(
      false,
    );
    expect(admittedSocialIdentity({}, "google", { sub: "new" })).toBe(false);
    expect(
      admittedSocialIdentity(socialAuthSettings(env), "google", {
        sub: "new-public-sub",
      }),
    ).toBe(false);
  });
  it.each(["", "PUBLIC", "all", "false"])(
    "rejects ambiguous registration mode %s",
    (mode) => {
      expect(() =>
        socialAuthSettings({ ...env, SOCIAL_REGISTRATION_MODE: mode }),
      ).toThrow();
    },
  );
  it("rejects stale allowlists in public mode and incomplete public credentials", () => {
    expect(() =>
      socialAuthSettings({ ...env, SOCIAL_REGISTRATION_MODE: "public" }),
    ).toThrow();
    expect(() =>
      socialAuthSettings({
        ...env,
        SOCIAL_REGISTRATION_MODE: "public",
        GOOGLE_ALLOWED_SUBJECTS: "[]",
        GOOGLE_CLIENT_SECRET: "",
      }),
    ).toThrow();
  });
  it("defaults off and only exposes provider names from complete explicit settings", () => {
    expect(socialProviderNames(socialAuthSettings({}))).toEqual([]);
    expect(socialProviderNames(socialAuthSettings(env))).toEqual(["google"]);
    expect(
      socialProviderNames(
        socialAuthSettings({
          GOOGLE_CLIENT_ID: "present",
          GOOGLE_CLIENT_SECRET: "present",
        }),
      ),
    ).toEqual([]);
  });
  it.each([
    { GOOGLE_CLIENT_SECRET: "" },
    { GOOGLE_CLIENT_SECRET: "short" },
    { GOOGLE_CLIENT_ID: "wrong-provider-client" },
    { GOOGLE_ALLOWED_SUBJECTS: "[]" },
    { GOOGLE_ALLOWED_SUBJECTS: '["person@example.com"]' },
    { GOOGLE_ALLOWED_SUBJECTS: '["same","same"]' },
    { GOOGLE_AUTH_ENABLED: "yes" },
  ])("fails closed without printing secrets for invalid opt-in %o", (patch) => {
    expect(() => socialAuthSettings({ ...env, ...patch })).toThrow();
    try {
      socialAuthSettings({ ...env, ...patch });
    } catch (error) {
      expect(String(error)).not.toContain("synthetic-secret");
    }
  });
  it("admits subjects rather than matching email claims", () => {
    const settings = socialAuthSettings(env);
    expect(
      admittedSocialIdentity(settings, "google", {
        sub: "synthetic-sub",
        email: "changed@example.invalid",
      }),
    ).toBe(true);
    expect(
      admittedSocialIdentity(settings, "google", {
        sub: "other",
        email: "synthetic-sub",
      }),
    ).toBe(false);
    expect(
      admittedSocialIdentity(settings, "github", {
        email: "synthetic-sub",
        email_verified: true,
      }),
    ).toBe(false);
  });
  it("admits GitHub's stable ID rather than mutable username or email", () => {
    const settings = socialAuthSettings({
      GITHUB_AUTH_ENABLED: "true",
      GITHUB_CLIENT_ID: "synthetic-github-client",
      GITHUB_CLIENT_SECRET: "synthetic-github-secret",
      GITHUB_ALLOWED_SUBJECTS: '["10001"]',
    });
    expect(socialProviderNames(settings)).toEqual(["github"]);
    expect(admittedSocialIdentity(settings, "github", { id: 10001 })).toBe(
      true,
    );
    expect(admittedSocialIdentity(settings, "github", { id: "10001" })).toBe(
      true,
    );
    for (const id of [
      undefined,
      "alice",
      "010001",
      -1,
      1.5,
      Number.MAX_SAFE_INTEGER + 1,
    ])
      expect(
        admittedSocialIdentity(settings, "github", {
          id,
          login: "10001",
          email: "10001",
        }),
      ).toBe(false);
  });
  it.each(["[]", '["alice"]', '["001"]', '["10001","10001"]', "[10001]"])(
    "rejects invalid GitHub admission %s",
    (subjects) => {
      expect(() =>
        socialAuthSettings({
          GITHUB_AUTH_ENABLED: "true",
          GITHUB_CLIENT_ID: "synthetic-github-client",
          GITHUB_CLIENT_SECRET: "synthetic-github-secret",
          GITHUB_ALLOWED_SUBJECTS: subjects,
        }),
      ).toThrow();
    },
  );
  it.each([
    { callbackURL: "//evil.example" },
    { callbackURL: "/app/settings" },
    { callbackURL: origin + "/app/dashboard?next=evil" },
    { scopes: ["offline_access"] },
    { additionalParams: { prompt: "none" } },
    { requestSignUp: true },
    { idToken: { token: "untrusted" } },
    { additionalData: { link: { userId: "foreign" } } },
    { errorCallbackURL: "https://evil.example" },
  ])("refuses caller overrides %o", (patch) => {
    expect(
      socialRequestBody(
        { provider: "google", ...patch },
        origin,
        false,
        socialAuthSettings(env),
      ),
    ).toBeUndefined();
  });
  it("pins exact success/error destinations and callback methods", () => {
    expect(
      socialRequestBody(
        { provider: "google" },
        origin,
        false,
        socialAuthSettings(env),
      ),
    ).toMatchObject({
      callbackURL: origin + "/app/dashboard",
      errorCallbackURL: origin + SOCIAL_ERROR_PATH,
    });
    expect(
      socialRequestBody(
        { provider: "google" },
        origin,
        true,
        socialAuthSettings(env),
      ),
    ).toMatchObject({ callbackURL: origin + "/app/account-access" });
    expect(safeSocialLocation("https://evil.example", origin)).toBe(
      origin + SOCIAL_ERROR_PATH,
    );
    expect(
      safeSocialLocation(origin + "/sign-in?error=private-token", origin),
    ).toBe(origin + SOCIAL_ERROR_PATH);
    expect(validSocialCallback(new URL(origin + "/?code=one&code=two"))).toBe(
      false,
    );
    expect(validSocialCallback(new URL(origin + "/?state=one&code=two"))).toBe(
      true,
    );
  });
});
