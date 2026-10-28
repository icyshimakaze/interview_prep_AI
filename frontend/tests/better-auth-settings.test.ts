// @vitest-environment node
import { describe, expect, it } from "vitest";
import {
  betterAuthSettings,
  localRegistrationEnabled,
} from "@/lib/better-auth/settings";

const valid = {
  AUTH_PROVIDER: "better_auth",
  PUBLIC_DEMO_ONLY: "false",
  NODE_ENV: "production",
  BETTER_AUTH_URL: "https://app.example.test",
  FRONTEND_ORIGIN: "https://app.example.test",
  BETTER_AUTH_SECRET: "synthetic-auth-secret-longer-than-32-characters",
  AUTH_RATE_LIMIT_KEY: "synthetic-rate-secret-longer-than-32-characters",
  AUTH_DATABASE_URL:
    "postgresql://auth:synthetic@db.example.test/app?sslmode=verify-full",
};

describe("Better Auth explicit configuration", () => {
  it("closes registration by default and refuses hosted opt-in", () => {
    expect(betterAuthSettings(valid).registrationEnabled).toBe(false);
    expect(() =>
      betterAuthSettings({ ...valid, AUTH_LOCAL_REGISTRATION_ENABLED: "true" }),
    ).toThrow("local development");
    expect(
      localRegistrationEnabled({
        NODE_ENV: "development",
        BETTER_AUTH_URL: "http://localhost:3456",
        AUTH_LOCAL_REGISTRATION_ENABLED: "true",
      }),
    ).toBe(true);
    for (const patch of [
      { VERCEL_ENV: "preview" },
      { BETTER_AUTH_URL: "https://remote.example.test" },
    ])
      expect(() =>
        localRegistrationEnabled({
          NODE_ENV: "development",
          BETTER_AUTH_URL: "http://localhost:3456",
          AUTH_LOCAL_REGISTRATION_ENABLED: "true",
          ...patch,
        }),
      ).toThrow();
  });
  it("requires explicit selection, preserves Clerk/off and closed demo profiles", () => {
    for (const patch of [
      { AUTH_PROVIDER: "clerk" },
      { AUTH_PROVIDER: "off" },
      { PUBLIC_DEMO_ONLY: "true" },
    ])
      expect(() => betterAuthSettings({ ...valid, ...patch })).toThrow(
        "not enabled",
      );
    expect(betterAuthSettings(valid).origin).toBe(valid.BETTER_AUTH_URL);
  });
  it.each([
    { BETTER_AUTH_URL: "https://app.example.test/" },
    { BETTER_AUTH_URL: "https://app.example.test/path" },
    { BETTER_AUTH_URL: "http://app.example.test" },
    { FRONTEND_ORIGIN: "https://other.example.test" },
    { BETTER_AUTH_SECRET: "short" },
    { AUTH_RATE_LIMIT_KEY: valid.BETTER_AUTH_SECRET },
    {
      AUTH_DATABASE_URL:
        "postgresql://auth:synthetic@db.example.test/app?sslmode=disable",
    },
    { AUTH_DATABASE_URL: valid.AUTH_DATABASE_URL + "&ssl=false" },
    { AUTH_DATABASE_URL: valid.AUTH_DATABASE_URL + "&sslmode=disable" },
  ])("rejects unsafe settings without echoing server secrets: %o", (patch) => {
    expect(() => betterAuthSettings({ ...valid, ...patch })).toThrow();
    try {
      betterAuthSettings({ ...valid, ...patch });
    } catch (error) {
      expect(String(error)).not.toContain("synthetic@");
    }
  });
  it("allows HTTP only for exact loopback in development", () => {
    const development = {
      ...valid,
      NODE_ENV: "development",
      BETTER_AUTH_URL: "http://localhost:3456",
      FRONTEND_ORIGIN: "http://localhost:3456",
      AUTH_DATABASE_URL:
        "postgresql://test:synthetic@localhost/disposable_test",
    };
    expect(betterAuthSettings(development).production).toBe(false);
    expect(() =>
      betterAuthSettings({
        ...development,
        BETTER_AUTH_URL: "http://remote.example.test",
      }),
    ).toThrow();
  });
});
