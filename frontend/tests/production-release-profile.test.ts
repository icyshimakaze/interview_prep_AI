// @vitest-environment node
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { betterAuthSettings } from "@/lib/better-auth/settings";

const profile: Record<string, string> = Object.fromEntries(
  readFileSync(
    resolve("../deploy/frontend.oauth.production.env.example"),
    "utf8",
  )
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => {
      const separator = line.indexOf("=");
      return [line.slice(0, separator), line.slice(separator + 1)];
    }),
);

describe("prepared production OAuth profile", () => {
  it("keeps providers off and email signup closed in the prepared public profile", () => {
    const settings = betterAuthSettings({ ...profile, NODE_ENV: "production" });
    expect(settings.origin).toBe("https://interviewprepai.webredirect.org");
    expect(settings.registrationEnabled).toBe(false);
    expect(settings.social).toEqual({});
    expect(profile.SOCIAL_REGISTRATION_MODE).toBe("public");
    expect(new URL(settings.databaseUrl).hostname).toBe(
      "ep-square-brook-b3ybm6sa-pooler.c-4.ap-southeast-1.aws.neon.tech",
    );
  });

  it("rejects unconfigured enablement and accepts public OAuth after valid setup", () => {
    for (const flag of ["GOOGLE_AUTH_ENABLED", "GITHUB_AUTH_ENABLED"])
      expect(() =>
        betterAuthSettings({
          ...profile,
          NODE_ENV: "production",
          [flag]: "true",
        }),
      ).toThrow();
    const settings = betterAuthSettings({
      ...profile,
      NODE_ENV: "production",
      GOOGLE_AUTH_ENABLED: "true",
      GITHUB_AUTH_ENABLED: "true",
      GOOGLE_CLIENT_ID: "synthetic.apps.googleusercontent.com",
      GOOGLE_CLIENT_SECRET: "synthetic-google-secret-1234567890",
      GITHUB_CLIENT_ID: "synthetic-github-client-1234567890",
      GITHUB_CLIENT_SECRET: "synthetic-github-secret-1234567890",
    });
    expect(Object.keys(settings.social).sort()).toEqual(["github", "google"]);
    expect(settings.social.google?.publicRegistration).toBe(true);
    expect(settings.social.github?.publicRegistration).toBe(true);
    expect(settings.registrationEnabled).toBe(false);
    expect(Object.keys(profile).some((key) => key.startsWith("STAGING_"))).toBe(
      false,
    );
  });
});
