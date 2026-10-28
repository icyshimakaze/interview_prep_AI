import type { SocialProviderName } from "./social-settings";

export function navigateToSocialProvider(
  value: unknown,
  provider: SocialProviderName,
): void {
  if (typeof value !== "string")
    throw new Error("Provider redirect unavailable");
  const url = new URL(value);
  const expected = provider === "google" ? "accounts.google.com" : "github.com";
  if (
    url.protocol !== "https:" ||
    url.hostname !== expected ||
    url.username ||
    url.password ||
    url.port
  )
    throw new Error("Provider redirect unavailable");
  window.location.assign(url.toString());
}
