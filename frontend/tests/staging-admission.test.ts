import { describe, expect, it } from "vitest";
import {
  stagingAdmission,
  STAGING_ORIGIN,
  STAGING_PROJECT_ID,
  type StagingAdmissionEnvironment,
} from "@/lib/better-auth/staging-admission";

const now = Date.parse("2026-10-25T17:00:00Z");
const secret = "a".repeat(64);
const emails = [
  "phase3-000000000001-alice@example.invalid",
  "phase3-000000000001-bob@example.invalid",
];
const valid: StagingAdmissionEnvironment = {
  NODE_ENV: "production",
  VERCEL: "1",
  VERCEL_ENV: "production",
  VERCEL_PROJECT_ID: STAGING_PROJECT_ID,
  AUTH_PROVIDER: "better_auth",
  PUBLIC_DEMO_ONLY: "false",
  FRONTEND_ORIGIN: STAGING_ORIGIN,
  BETTER_AUTH_URL: STAGING_ORIGIN,
  STAGING_AUTH_TESTS_ENABLED: "true",
  STAGING_AUTH_TEST_SECRET: secret,
  STAGING_AUTH_TEST_EMAILS: JSON.stringify(emails),
  STAGING_AUTH_TESTS_EXPIRES_AT: "2026-10-25T18:00:00Z",
};

function request(
  changes: Record<string, string> = {},
  url = STAGING_ORIGIN + "/api/staging/auth/register",
  method = "POST",
) {
  return new Request(url, {
    method,
    headers: {
      origin: STAGING_ORIGIN,
      "x-interview-staging-admission": secret,
      ...changes,
    },
  });
}

describe("private staging admission", () => {
  it("admits only the explicitly configured synthetic accounts", () => {
    expect(stagingAdmission(request(), valid, now)).toEqual(new Set(emails));
  });

  it.each([
    ["NODE_ENV", "development"],
    ["VERCEL", ""],
    ["VERCEL_ENV", "preview"],
    ["VERCEL_PROJECT_ID", "prj_wsxEcvVC17paXs5pco4K9eHwWKgd"],
    ["AUTH_PROVIDER", "clerk"],
    ["PUBLIC_DEMO_ONLY", "true"],
    ["FRONTEND_ORIGIN", "https://interviewprepai.webredirect.org"],
    ["BETTER_AUTH_URL", "https://foreign.example.test"],
    ["STAGING_AUTH_TESTS_ENABLED", "false"],
    ["STAGING_AUTH_TEST_SECRET", "short"],
    ["STAGING_AUTH_TESTS_EXPIRES_AT", "invalid"],
    ["STAGING_AUTH_TESTS_EXPIRES_AT", "2026-10-25T17:00:00Z"],
    ["STAGING_AUTH_TESTS_EXPIRES_AT", "2026-10-25T19:00:01Z"],
    ["STAGING_AUTH_TEST_EMAILS", "not-json"],
    ["STAGING_AUTH_TEST_EMAILS", JSON.stringify([emails[0], emails[0]])],
    ["STAGING_AUTH_TEST_EMAILS", JSON.stringify([emails[0]])],
    [
      "STAGING_AUTH_TEST_EMAILS",
      JSON.stringify([emails[0], "real@example.com"]),
    ],
    ["STAGING_AUTH_TEST_EMAILS", JSON.stringify([emails[0], 12])],
  ])("fails closed for %s=%s", (key, value) => {
    expect(
      stagingAdmission(request(), { ...valid, [key]: value }, now),
    ).toBeUndefined();
  });

  it.each<Record<string, string>>([
    { "x-interview-staging-admission": "" },
    { "x-interview-staging-admission": "b".repeat(64) },
    { "x-interview-staging-admission": "é".repeat(64) },
    { origin: "" },
    { origin: "https://foreign.example.test" },
    { "sec-fetch-site": "cross-site" },
  ])(
    "rejects invalid request credentials/origins without throwing",
    (headers) => {
      expect(stagingAdmission(request(headers), valid, now)).toBeUndefined();
    },
  );

  it.each([
    [STAGING_ORIGIN + "/api/staging/auth/register?token=forbidden", "POST"],
    ["https://alternate.vercel.app/api/staging/auth/register", "POST"],
    [STAGING_ORIGIN + "/api/auth/sign-up/email", "POST"],
    [STAGING_ORIGIN + "/api/staging/auth/register", "GET"],
  ])("rejects alternate URL/method %s %s", (url, method) => {
    expect(
      stagingAdmission(request({}, url, method), valid, now),
    ).toBeUndefined();
  });

  it("is closed with no fixture configuration", () => {
    expect(stagingAdmission(request(), {}, now)).toBeUndefined();
  });
});
