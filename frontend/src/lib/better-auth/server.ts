import "server-only";
import { Pool } from "pg";
import { createBetterAuth } from "./factory";
import { betterAuthSettings } from "./settings";

let instance:
  | {
      auth: ReturnType<typeof createBetterAuth>;
      pool: Pool;
      settings: ReturnType<typeof betterAuthSettings>;
    }
  | undefined;

export function betterAuthServer() {
  if (instance) return instance;
  const settings = betterAuthSettings(process.env);
  const pool = new Pool({
    connectionString: settings.databaseUrl,
    max: 3,
    idleTimeoutMillis: 10000,
    connectionTimeoutMillis: 10000,
  });
  pool.on("error", () => {
    /* Never log connection details. Requests fail closed. */
  });
  instance = { settings, pool, auth: createBetterAuth(pool, settings) };
  return instance;
}

export async function readBetterAuthSession(headers: Headers) {
  try {
    // RSC cannot forward refreshed cookies. Let the HTTP session endpoint renew
    // both the DB record and cookie together, after this server-side check.
    return await betterAuthServer().auth.api.getSession({
      headers,
      query: { disableRefresh: true },
    });
  } catch {
    throw new Error("The account session service is temporarily unavailable.");
  }
}
