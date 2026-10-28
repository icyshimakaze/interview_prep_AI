import { timingSafeEqual } from "node:crypto";

// This operator fixture can only run on the separately approved staging project.
export const STAGING_PROJECT_ID = "prj_kQtaYbGd25ulIufNKnenHw7MG2bN";
export const STAGING_ORIGIN =
  "https://interview-prep-ai-auth-staging.vercel.app";

export interface StagingAdmissionEnvironment {
  NODE_ENV?: string;
  VERCEL?: string;
  VERCEL_ENV?: string;
  VERCEL_PROJECT_ID?: string;
  AUTH_PROVIDER?: string;
  PUBLIC_DEMO_ONLY?: string;
  FRONTEND_ORIGIN?: string;
  BETTER_AUTH_URL?: string;
  STAGING_AUTH_TESTS_ENABLED?: string;
  STAGING_AUTH_TEST_SECRET?: string;
  STAGING_AUTH_TEST_EMAILS?: string;
  STAGING_AUTH_TESTS_EXPIRES_AT?: string;
}

export function stagingAdmission(
  request: Request,
  env: StagingAdmissionEnvironment,
  now = Date.now(),
): ReadonlySet<string> | undefined {
  const url = new URL(request.url);
  const secret = env.STAGING_AUTH_TEST_SECRET ?? "";
  const supplied = request.headers.get("x-interview-staging-admission") ?? "";
  const expires = Date.parse(env.STAGING_AUTH_TESTS_EXPIRES_AT ?? "");
  if (
    env.NODE_ENV !== "production" ||
    env.VERCEL !== "1" ||
    env.VERCEL_ENV !== "production" ||
    env.VERCEL_PROJECT_ID !== STAGING_PROJECT_ID ||
    env.AUTH_PROVIDER !== "better_auth" ||
    env.PUBLIC_DEMO_ONLY !== "false" ||
    env.FRONTEND_ORIGIN !== STAGING_ORIGIN ||
    env.BETTER_AUTH_URL !== STAGING_ORIGIN ||
    env.STAGING_AUTH_TESTS_ENABLED !== "true" ||
    !/^[a-f0-9]{64}$/.test(secret) ||
    !/^[a-f0-9]{64}$/.test(supplied) ||
    !Number.isFinite(expires) ||
    expires <= now ||
    expires > now + 2 * 60 * 60 * 1000 ||
    request.method !== "POST" ||
    url.origin !== STAGING_ORIGIN ||
    url.pathname !== "/api/staging/auth/register" ||
    Boolean(url.search) ||
    request.headers.get("origin") !== STAGING_ORIGIN ||
    request.headers.get("sec-fetch-site") === "cross-site"
  )
    return undefined;
  if (!timingSafeEqual(Buffer.from(secret), Buffer.from(supplied)))
    return undefined;
  let emails: unknown;
  try {
    emails = JSON.parse(env.STAGING_AUTH_TEST_EMAILS ?? "");
  } catch {
    return undefined;
  }
  if (
    !Array.isArray(emails) ||
    emails.length !== 2 ||
    !emails.every(
      (email: unknown): email is string =>
        typeof email === "string" &&
        /^phase3-[a-f0-9]{12}-(alice|bob)@example\.invalid$/.test(email),
    )
  )
    return undefined;
  const allowed = new Set<string>(emails);
  return allowed.size === 2 ? allowed : undefined;
}
