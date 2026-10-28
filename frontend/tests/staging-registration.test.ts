import { Pool } from "pg";
import {
  afterAll,
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { createBetterAuth } from "@/lib/better-auth/factory";
import {
  STAGING_ORIGIN,
  STAGING_PROJECT_ID,
} from "@/lib/better-auth/staging-admission";

const mocks = vi.hoisted(() => ({
  server:
    vi.fn<
      () => ReturnType<
        typeof import("@/lib/better-auth/server").betterAuthServer
      >
    >(),
  request: vi.fn<typeof import("@/lib/better-auth/http").authRequest>(),
}));
vi.mock("@/lib/better-auth/server", () => ({ betterAuthServer: mocks.server }));
vi.mock("@/lib/better-auth/http", () => ({ authRequest: mocks.request }));

import { POST } from "@/app/api/staging/auth/register/route";

const pool = new Pool();
const settings = {
  origin: STAGING_ORIGIN,
  secret: "synthetic-staging-secret-0000000000000000000000",
  rateLimitKey: "synthetic-staging-limiter-000000000000000000000",
  production: true,
  registrationEnabled: false,
  social: {},
  databaseUrl: "postgresql://unused:unused@127.0.0.1:1/not_connected_test",
};
const server = { pool, settings, auth: createBetterAuth(pool, settings) };
const emails = [
  "phase3-000000000001-alice@example.invalid",
  "phase3-000000000001-bob@example.invalid",
];

function request(): Request {
  return new Request(STAGING_ORIGIN + "/api/staging/auth/register", {
    method: "POST",
    headers: {
      origin: STAGING_ORIGIN,
      "content-type": "application/json",
      "x-interview-staging-admission": "a".repeat(64),
    },
    body: JSON.stringify({
      email: emails[0],
      password: "Synthetic-password-0001",
      name: "Synthetic",
    }),
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-25T17:00:00Z"));
  const env = {
    NODE_ENV: "production",
    VERCEL: "1",
    VERCEL_ENV: "production",
    VERCEL_PROJECT_ID: STAGING_PROJECT_ID,
    AUTH_PROVIDER: "better_auth",
    PUBLIC_DEMO_ONLY: "false",
    FRONTEND_ORIGIN: STAGING_ORIGIN,
    BETTER_AUTH_URL: STAGING_ORIGIN,
    STAGING_AUTH_TESTS_ENABLED: "true",
    STAGING_AUTH_TEST_SECRET: "a".repeat(64),
    STAGING_AUTH_TEST_EMAILS: JSON.stringify(emails),
    STAGING_AUTH_TESTS_EXPIRES_AT: "2026-10-25T18:00:00Z",
  };
  for (const [key, value] of Object.entries(env)) vi.stubEnv(key, value);
  mocks.server.mockReturnValue(server);
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.useRealTimers();
});
afterAll(async () => pool.end());

describe("private registration fixture response boundary", () => {
  it("does not initialize auth or access the database when admission is closed", async () => {
    vi.stubEnv("STAGING_AUTH_TESTS_ENABLED", "false");
    expect((await POST(request())).status).toBe(404);
    expect(mocks.server).not.toHaveBeenCalled();
    expect(mocks.request).not.toHaveBeenCalled();
  });

  it("discards the automatic session cookie and raw account response", async () => {
    mocks.request.mockResolvedValue(
      Response.json(
        { token: "synthetic-session-token", user: { email: emails[0] } },
        { headers: { "Set-Cookie": "synthetic=secret; Secure; HttpOnly" } },
      ),
    );
    const response = await POST(request());
    expect(response.status).toBe(201);
    expect(await response.json()).toEqual({ created: true });
    expect(response.headers.has("set-cookie")).toBe(false);
    expect(response.headers.get("cache-control")).toBe("no-store");
    const call = mocks.request.mock.calls[0];
    expect(call?.[0].url).toBe(STAGING_ORIGIN + "/api/auth/sign-up/email");
    expect(call?.[3].registrationEnabled).toBe(true);
    expect(call?.[4]).toBe(true);
    expect(call?.[5]).toEqual(new Set(emails));
    expect(server.settings.registrationEnabled).toBe(false);
  });

  it("keeps failure details private and preserves retry guidance", async () => {
    mocks.request.mockResolvedValue(
      Response.json(
        { private_detail: "not-for-the-caller" },
        { status: 429, headers: { "Retry-After": "60" } },
      ),
    );
    const response = await POST(request());
    expect(response.status).toBe(429);
    expect(response.headers.get("retry-after")).toBe("60");
    expect(await response.json()).toEqual({
      code: "staging_registration_failed",
    });
  });
});
