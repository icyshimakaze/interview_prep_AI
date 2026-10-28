import { afterEach, describe, expect, it, vi } from "vitest";
import { gatewayHeaders } from "@/lib/gateway";

afterEach(() => vi.unstubAllEnvs());

describe("server gateway headers", () => {
  it("replaces forged headers with the configured secret and Vercel client address", () => {
    vi.stubEnv("VERCEL", "1");
    vi.stubEnv(
      "BACKEND_PROXY_SECRET",
      "server-only-test-secret-longer-than-32-characters",
    );
    const headers = gatewayHeaders(
      new Headers({
        "x-interview-prep-gateway": "forged",
        "x-interview-prep-client-ip": "192.0.2.99",
        "x-forwarded-for": "192.0.2.88",
        "x-vercel-forwarded-for": "2001:db8::1",
        "x-csrf-token": "csrf",
        cookie:
          "session=unrelated; interview_prep_demo=owned; __Secure-interview-auth.session_token=private",
      }),
    );
    expect(headers?.get("x-interview-prep-gateway")).toBe(
      "server-only-test-secret-longer-than-32-characters",
    );
    expect(headers?.get("x-interview-prep-client-ip")).toBe("2001:db8::1");
    expect(headers?.get("cookie")).toBe("interview_prep_demo=owned");
    expect(headers?.get("x-csrf-token")).toBe("csrf");
  });

  it.each([null, "invalid", "192.0.2.1, 192.0.2.2"])(
    "fails closed for invalid Vercel metadata: %s",
    (address) => {
      vi.stubEnv("VERCEL", "1");
      vi.stubEnv(
        "BACKEND_PROXY_SECRET",
        "server-only-test-secret-longer-than-32-characters",
      );
      const headers = new Headers();
      if (address) headers.set("x-vercel-forwarded-for", address);
      expect(gatewayHeaders(headers)).toBeNull();
    },
  );

  it("never trusts forwarding headers in native mode", () => {
    vi.stubEnv("VERCEL", "");
    vi.stubEnv(
      "BACKEND_PROXY_SECRET",
      "server-only-test-secret-longer-than-32-characters",
    );
    expect(
      gatewayHeaders(
        new Headers({ "x-vercel-forwarded-for": "192.0.2.2" }),
      )?.get("x-interview-prep-client-ip"),
    ).toBe("127.0.0.1");
  });

  it("requires a secret in Vercel production, while removing spoofed development headers", () => {
    vi.stubEnv("BACKEND_PROXY_SECRET", "");
    vi.stubEnv("VERCEL_ENV", "production");
    expect(gatewayHeaders(new Headers())).toBeNull();
    vi.stubEnv("VERCEL_ENV", "preview");
    const headers = gatewayHeaders(
      new Headers({
        "x-interview-prep-gateway": "forged",
        "x-interview-prep-client-ip": "192.0.2.1",
      }),
    );
    expect(headers?.has("x-interview-prep-gateway")).toBe(false);
    expect(headers?.has("x-interview-prep-client-ip")).toBe(false);
  });
});
