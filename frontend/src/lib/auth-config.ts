import "server-only";
import { betterAuthSettings } from "./better-auth/settings";

export function accountAuthProvider(): "clerk" | "better_auth" | "off" {
  const provider = process.env.AUTH_PROVIDER ?? "clerk";
  if (provider !== "clerk" && provider !== "better_auth" && provider !== "off")
    throw new Error("Unsupported authentication provider.");
  return provider;
}

export function accountAuthConfigured(): boolean {
  if (accountAuthProvider() === "off") return false;
  if (accountAuthProvider() === "better_auth") {
    try {
      betterAuthSettings(process.env);
      return true;
    } catch {
      return false;
    }
  }
  return Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.CLERK_SECRET_KEY,
  );
}
