import { socialAuthSettings, type SocialEnvironment } from "./social-settings";

export interface BetterAuthEnvironment extends SocialEnvironment {
  AUTH_PROVIDER?: string;
  PUBLIC_DEMO_ONLY?: string;
  BETTER_AUTH_URL?: string;
  BETTER_AUTH_SECRET?: string;
  AUTH_DATABASE_URL?: string;
  AUTH_RATE_LIMIT_KEY?: string;
  FRONTEND_ORIGIN?: string;
  VERCEL_ENV?: string;
  NODE_ENV?: string;
  AUTH_LOCAL_REGISTRATION_ENABLED?: string;
}

export function localRegistrationEnabled(env: BetterAuthEnvironment): boolean {
  if (env.AUTH_LOCAL_REGISTRATION_ENABLED !== "true") return false;
  const origin = new URL(env.BETTER_AUTH_URL ?? "http://invalid");
  if (
    env.NODE_ENV !== "development" ||
    Boolean(env.VERCEL_ENV) ||
    !["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname)
  )
    throw new Error(
      "Unverified registration is restricted to local development.",
    );
  return true;
}

export function betterAuthSettings(env: BetterAuthEnvironment) {
  if (env.AUTH_PROVIDER !== "better_auth" || env.PUBLIC_DEMO_ONLY === "true")
    throw new Error("Better Auth is not enabled.");
  const production = env.NODE_ENV === "production" || Boolean(env.VERCEL_ENV);
  const origin = new URL(env.BETTER_AUTH_URL ?? "http://invalid");
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname);
  if (
    origin.origin !== env.BETTER_AUTH_URL ||
    origin.username ||
    origin.password ||
    (production
      ? origin.protocol !== "https:"
      : origin.protocol !== "https:" &&
        !(local && origin.protocol === "http:")) ||
    (production && env.FRONTEND_ORIGIN !== origin.origin)
  )
    throw new Error("Better Auth requires an exact trusted frontend origin.");
  if (
    !env.BETTER_AUTH_SECRET ||
    env.BETTER_AUTH_SECRET.length < 32 ||
    !env.AUTH_RATE_LIMIT_KEY ||
    env.AUTH_RATE_LIMIT_KEY.length < 32 ||
    env.AUTH_RATE_LIMIT_KEY === env.BETTER_AUTH_SECRET
  )
    throw new Error(
      "Better Auth requires separate server secrets of at least 32 characters.",
    );
  const database = new URL(env.AUTH_DATABASE_URL ?? "http://invalid");
  if (
    !["postgres:", "postgresql:"].includes(database.protocol) ||
    !database.username ||
    !database.password ||
    database.pathname.length < 2 ||
    Boolean(database.hash) ||
    new Set(database.searchParams.keys()).size !== database.searchParams.size ||
    (production && database.searchParams.get("sslmode") !== "verify-full") ||
    [...database.searchParams.keys()].some(
      (key) => !["sslmode", "application_name"].includes(key),
    )
  )
    throw new Error(
      "Better Auth requires a private PostgreSQL URL with verified production TLS.",
    );
  return {
    origin: origin.origin,
    secret: env.BETTER_AUTH_SECRET,
    rateLimitKey: env.AUTH_RATE_LIMIT_KEY,
    production,
    registrationEnabled: localRegistrationEnabled(env),
    social: socialAuthSettings(env),
    databaseUrl: database.toString(),
  };
}
