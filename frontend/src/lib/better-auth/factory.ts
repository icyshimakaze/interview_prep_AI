import { createHmac } from "node:crypto";
import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import {
  addOAuthServerContext,
  createAuthMiddleware,
  getOAuthState,
  getSessionFromCtx,
} from "better-auth/api";
import type { Pool } from "pg";
import { configuredSocialProviders } from "./social-providers";
import {
  admittedSocialIdentity,
  SOCIAL_ERROR_PATH,
  SOCIAL_FRESH_SECONDS,
  type SocialSettings,
} from "./social-settings";

export interface AuthSettings {
  origin: string;
  secret: string;
  rateLimitKey: string;
  production: boolean;
  registrationEnabled?: boolean;
  social?: SocialSettings;
}

export function createLimiter(pool: Pool, secret: string) {
  return {
    async consume(key: string, rule: { window: number; max: number }) {
      const hash = createHmac("sha256", secret).update(key).digest("hex");
      const result = await pool.query<{ count: number }>(
        `INSERT INTO auth.request_limits (key_hash, count, expires_at)
         VALUES ($1, 1, clock_timestamp() + $2 * interval '1 second')
         ON CONFLICT (key_hash) DO UPDATE SET
           count = CASE WHEN auth.request_limits.expires_at <= clock_timestamp()
                        THEN 1 ELSE auth.request_limits.count + 1 END,
           expires_at = CASE WHEN auth.request_limits.expires_at <= clock_timestamp()
                        THEN clock_timestamp() + $2 * interval '1 second'
                        ELSE auth.request_limits.expires_at END
         WHERE auth.request_limits.expires_at <= clock_timestamp()
            OR auth.request_limits.count < $3
         RETURNING count`,
        [hash, rule.window, rule.max],
      );
      await pool.query(`DELETE FROM auth.request_limits WHERE key_hash IN
        (SELECT key_hash FROM auth.request_limits
         WHERE expires_at < clock_timestamp() LIMIT 100)`);
      await pool.query(`DELETE FROM auth.session WHERE id IN
        (SELECT id FROM auth.session WHERE "expiresAt" < clock_timestamp() LIMIT 100)`);
      return { allowed: result.rowCount === 1, retryAfter: rule.window };
    },
  };
}

// No environment reads or implicit DB target: the runtime and test harness supply both.
export function createBetterAuth(pool: Pool, settings: AuthSettings) {
  return betterAuth({
    appName: "Interview Prep",
    telemetry: { enabled: false },
    baseURL: settings.origin,
    secret: settings.secret,
    database: pool,
    trustedOrigins: [settings.origin],
    logger: { disabled: true },
    onAPIError: { errorURL: settings.origin + SOCIAL_ERROR_PATH },
    socialProviders: configuredSocialProviders(settings.social),
    hooks: {
      before: createAuthMiddleware(async (context) => {
        if (
          context.path !== "/sign-in/social" &&
          context.path !== "/link-social"
        )
          return;
        const provider: unknown = context.body?.provider;
        if (provider === "google" || provider === "github")
          await addOAuthServerContext({ interviewProvider: provider });
      }),
    },
    user: {
      validateUserInfo: async ({ user, source }, context) => {
        if (source.method !== "oauth") return;
        const state = await getOAuthState();
        if (
          state?.serverContext?.interviewProvider !== source.oauth?.providerId
        )
          return { error: "social_provider_state_mismatch" };
        if (
          !admittedSocialIdentity(
            settings.social ?? {},
            source.oauth?.providerId ?? "",
            source.oauth?.profile,
          )
        )
          return { error: "social_admission_closed" };
        if (source.action === "link-account") {
          const current = await getSessionFromCtx(context, {
            disableCookieCache: true,
            disableRefresh: true,
          });
          if (
            !current ||
            current.user.id !== user.id ||
            Date.now() - current.session.createdAt.getTime() >
              SOCIAL_FRESH_SECONDS * 1000
          )
            return { error: "social_link_requires_recent_session" };
        }
      },
    },
    databaseHooks: {
      session: {
        create: {
          before: async (session) => ({
            data: { ...session, ipAddress: null, userAgent: null },
          }),
        },
      },
      account: {
        create: {
          before: async (account) => ({
            data: {
              ...account,
              accessToken: null,
              refreshToken: null,
              idToken: null,
              accessTokenExpiresAt: null,
              refreshTokenExpiresAt: null,
            },
          }),
        },
        update: {
          before: async (account) => ({
            data: {
              ...account,
              accessToken: null,
              refreshToken: null,
              idToken: null,
              accessTokenExpiresAt: null,
              refreshTokenExpiresAt: null,
            },
          }),
        },
      },
    },
    emailAndPassword: {
      enabled: true,
      disableSignUp: !settings.registrationEnabled,
      minPasswordLength: 12,
      maxPasswordLength: 128,
      requireEmailVerification: false,
    },
    // Explicit dual-proof linking only. Provider email is never an ownership key.
    account: {
      accountLinking: {
        enabled: true,
        disableImplicitLinking: true,
        allowDifferentEmails: true,
        trustedProviders: ["google", "github"],
      },
      storeAccountCookie: false,
      storeStateStrategy: "database",
      skipStateCookieCheck: false,
    },
    session: {
      expiresIn: 60 * 60 * 24 * 7,
      updateAge: 60 * 60 * 24,
      cookieCache: { enabled: false },
    },
    advanced: {
      useSecureCookies: settings.production,
      cookiePrefix: "interview-auth",
      defaultCookieAttributes: { httpOnly: true, sameSite: "lax", path: "/" },
      ipAddress: { ipAddressHeaders: ["x-interview-auth-peer"] },
    },
    rateLimit: {
      enabled: true,
      window: 60,
      max: 120,
      customRules: {
        "/sign-in/email": { window: 60, max: 5 },
        "/sign-up/email": { window: 60, max: 3 },
        "/token": { window: 60, max: 90 },
      },
      customStorage: createLimiter(pool, settings.rateLimitKey),
    },
    plugins: [
      jwt({
        disableSettingJwtHeader: true,
        jwks: {
          keyPairConfig: { alg: "RS256", modulusLength: 2048 },
          rotationInterval: 60 * 60 * 24 * 30,
          gracePeriod: 60 * 60 * 24,
        },
        jwt: {
          issuer: settings.origin,
          audience: "interview-prep-api",
          expirationTime: "60s",
          definePayload: ({ session }) => {
            const now = Math.floor(Date.now() / 1000);
            return {
              iat: now,
              nbf: now,
              exp: now + 60,
              azp: settings.origin,
              sid: session.id,
            };
          },
        },
      }),
    ],
  });
}
