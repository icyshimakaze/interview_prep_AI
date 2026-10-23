// @vitest-environment node

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("VERCEL_ENV", "production");
  vi.stubEnv("BACKEND_INTERNAL_URL", "https://backend.example.test");
  vi.stubEnv("FRONTEND_ORIGIN", "https://app.example.test");
  vi.stubEnv(
    "BACKEND_PROXY_SECRET",
    "test-gateway-secret-longer-than-32-characters",
  );
  vi.stubEnv("PUBLIC_DEMO_ONLY", "true");
  vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "");
  vi.stubEnv("CLERK_SECRET_KEY", "");
});
afterEach(() => vi.unstubAllEnvs());

describe("Vercel production configuration", () => {
  it("builds a same-origin HTTPS API rewrite without exposing credentials", async () => {
    const { default: config } = await import("../next.config");
    if (!config.rewrites) throw new Error("Missing API rewrite");
    expect(await config.rewrites()).toEqual([
      {
        source: "/api/v1/:path*",
        destination: "https://backend.example.test/api/v1/:path*",
      },
    ]);
    expect(config.env).toBeUndefined();
    expect("publicRuntimeConfig" in config).toBe(false);
  });
  it.each([
    ["BACKEND_INTERNAL_URL", ""],
    ["BACKEND_INTERNAL_URL", "http://backend.example.test"],
    ["FRONTEND_ORIGIN", "https://app.example.test/path"],
    ["BACKEND_PROXY_SECRET", ""],
    ["BACKEND_PROXY_SECRET", "short"],
  ])("rejects unsafe production configuration: %s", async (key, value) => {
    vi.stubEnv(key, value);
    await expect(import("../next.config")).rejects.toThrow(
      "Production requires",
    );
  });
  it("keeps account credentials out of the public demo profile", async () => {
    vi.stubEnv("CLERK_SECRET_KEY", "never-use-real-keys-in-tests");
    await expect(import("../next.config")).rejects.toThrow("public demo");
  });
  it.each([
    ["", ""],
    ["pk_test_example", "sk_test_example"],
    ["pk_live_example", ""],
  ])(
    "requires both production Clerk keys for accounts",
    async (publishable, secret) => {
      vi.stubEnv("PUBLIC_DEMO_ONLY", "false");
      vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", publishable);
      vi.stubEnv("CLERK_SECRET_KEY", secret);
      await expect(import("../next.config")).rejects.toThrow(
        "Clerk production",
      );
    },
  );
  it("supports accounts beside the demo and sets HSTS without bundling secrets", async () => {
    vi.stubEnv("PUBLIC_DEMO_ONLY", "false");
    vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_live_fictional");
    vi.stubEnv("CLERK_SECRET_KEY", "sk_live_fictional");
    const { default: config } = await import("../next.config");
    expect(config.env).toBeUndefined();
    if (!config.headers) throw new Error("Missing security headers");
    expect((await config.headers())[0]?.headers).toContainEqual({
      key: "Strict-Transport-Security",
      value: "max-age=15552000",
    });
  });
});
