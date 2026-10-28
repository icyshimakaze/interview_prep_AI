// @vitest-environment node
import { afterEach, expect, it, vi } from "vitest";
import { navigateToSocialProvider } from "@/lib/better-auth/social-navigation";
afterEach(() => vi.unstubAllGlobals());
it.each([
  "https://evil.example",
  "javascript:alert(1)",
  "//accounts.google.com/",
  "https://user:password@accounts.google.com/",
  "https://accounts.google.com:444/",
  "https://accounts.google.com.evil.example/",
])("rejects unsafe redirect %s", (url) => {
  const assign = vi.fn();
  vi.stubGlobal("window", { location: { assign } });
  expect(() => navigateToSocialProvider(url, "google")).toThrow();
  expect(assign).not.toHaveBeenCalled();
});
it("accepts only the selected provider's HTTPS host", () => {
  const assign = vi.fn();
  vi.stubGlobal("window", { location: { assign } });
  navigateToSocialProvider(
    "https://accounts.google.com/o/oauth2/v2/auth",
    "google",
  );
  expect(assign).toHaveBeenCalledOnce();
  expect(() =>
    navigateToSocialProvider("https://accounts.google.com/", "github"),
  ).toThrow();
  navigateToSocialProvider(
    "https://github.com/login/oauth/authorize",
    "github",
  );
  expect(assign).toHaveBeenCalledTimes(2);
  expect(() =>
    navigateToSocialProvider("https://github.com.evil.example/", "github"),
  ).toThrow();
});
