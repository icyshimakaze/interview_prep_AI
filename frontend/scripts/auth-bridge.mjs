// Synthetic-data process bridge. Refuses every non-loopback / non-test DB.
import { registerHooks } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Pool } from "pg";

const packageInfo = JSON.parse(
  readFileSync(
    new URL("../node_modules/better-auth/package.json", import.meta.url),
    "utf8",
  ),
);
if (packageInfo.version !== "1.7.12")
  throw new Error(
    "Pinned Better Auth 1.7.12 is required for this schema/proof.",
  );

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (
      specifier.startsWith("./") &&
      context.parentURL?.includes("/src/lib/better-auth/") &&
      !specifier.endsWith(".ts")
    ) {
      return nextResolve(specifier + ".ts", context);
    }
    return nextResolve(specifier, context);
  },
});
const { createBetterAuth } = await import("../src/lib/better-auth/factory.ts");
const { authRequest } = await import("../src/lib/better-auth/http.ts");
const target = new URL(process.env.TEST_AUTH_DATABASE_URL ?? "http://invalid");
if (
  !["localhost", "127.0.0.1", "[::1]"].includes(target.hostname) ||
  !target.pathname.endsWith("_test") ||
  !["postgres:", "postgresql:"].includes(target.protocol)
)
  throw new Error("Disposable test database required");
const pool = new Pool({
  connectionString: target.toString(),
  // Restricted role tests must use the same defaults as the pooled runtime.
  // The migration owner used by other disposable proofs needs an explicit path.
  options: target.username.startsWith("auth_test_")
    ? undefined
    : "-c search_path=auth",
  max: 3,
});
const settings = {
  origin: "https://auth.example.test",
  secret: "synthetic-better-auth-secret-00000000000000000000",
  rateLimitKey: "synthetic-rate-limit-secret-00000000000000000000",
  production: true,
};
try {
  if (process.argv.includes("--generate")) {
    const auth = createBetterAuth(pool, settings);
    await pool.query("CREATE SCHEMA auth");
    const { getMigrations } = await import("better-auth/db/migration");
    const migration = await getMigrations(auth.options);
    const sql = await migration.compileMigrations();
    const destination = new URL(
      "../../backend/alembic/better_auth_1_7_12.sql",
      import.meta.url,
    );
    writeFileSync(
      destination,
      "-- Generated from pinned better-auth 1.7.12 on an empty disposable DB.\n" +
        sql +
        "\n",
    );
    console.log("Generated pinned auth schema: " + fileURLToPath(destination));
  } else {
    const input = JSON.parse(readFileSync(0, "utf8"));
    // This bridge already refuses non-loopback/non-test databases. Production
    // configuration cannot enable registration; cookie tests still use HTTPS.
    settings.registrationEnabled = input.registrationEnabled !== false;
    let oauthCalls;
    if (input.social) {
      const { installSyntheticOAuth } =
        await import("./oauth-test-transport.mjs");
      oauthCalls = installSyntheticOAuth(input.oauthFixture ?? {});
      settings.social = input.social;
    }
    const auth = createBetterAuth(pool, settings);
    const headers = new Headers({
      origin: settings.origin,
      "content-type": "application/json",
      "x-vercel-forwarded-for": input.peer ?? "192.0.2.10",
      ...(input.headers ?? {}),
    });
    if (input.omitOrigin) headers.delete("origin");
    if (input.cookie) headers.set("cookie", input.cookie);
    const method = input.method ?? "GET";
    const request = new Request(settings.origin + "/api/auth" + input.path, {
      method,
      headers,
      body: method === "POST" ? JSON.stringify(input.body ?? {}) : undefined,
    });
    let response;
    if (input.body?.schemaCheck) {
      const { getMigrations } = await import("better-auth/db/migration");
      const plan = await getMigrations(auth.options);
      response = Response.json({
        missing:
          plan.toBeCreated.length +
          plan.toBeAdded.length +
          plan.toBeAddedIndexes.length,
        problems: plan.schemaProblems.length + plan.unsafeChanges.length,
      });
    } else
      response = input.sign
        ? Response.json(
            await auth.api.signJWT({ body: { payload: input.sign } }),
          )
        : input.directHandler
          ? await auth.handler(request)
          : await authRequest(
              request,
              auth,
              pool,
              settings,
              true,
              input.registrationEmails
                ? new Set(input.registrationEmails)
                : undefined,
            );
    const body = await response.json().catch(() => null);
    const cookies = response.headers.getSetCookie();
    process.stdout.write(
      JSON.stringify({
        status: response.status,
        body,
        cookies,
        location: response.headers.get("location"),
        oauthCalls,
        cacheControl: response.headers.get("cache-control"),
      }),
    );
  }
} finally {
  await pool.end();
}
