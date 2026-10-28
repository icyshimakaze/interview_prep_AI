import { createBetterAuth } from "@/lib/better-auth/factory";
import { authRequest } from "@/lib/better-auth/http";
import { betterAuthServer } from "@/lib/better-auth/server";
import {
  stagingAdmission,
  STAGING_ORIGIN,
} from "@/lib/better-auth/staging-admission";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const headers = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

export async function POST(request: Request): Promise<Response> {
  const emails = stagingAdmission(request, process.env);
  if (!emails)
    return Response.json({ code: "not_found" }, { status: 404, headers });
  try {
    const server = betterAuthServer();
    const settings = { ...server.settings, registrationEnabled: true };
    const auth = createBetterAuth(server.pool, settings);
    const response = await authRequest(
      new Request(new URL("/api/auth/sign-up/email", STAGING_ORIGIN), request),
      auth,
      server.pool,
      settings,
      true,
      emails,
    );
    // Do not forward account/session details or the fixture's automatic cookie.
    return Response.json(
      response.ok ? { created: true } : { code: "staging_registration_failed" },
      {
        status: response.ok ? 201 : response.status,
        headers: {
          ...headers,
          ...(response.headers.has("retry-after")
            ? { "Retry-After": response.headers.get("retry-after") ?? "60" }
            : {}),
        },
      },
    );
  } catch {
    return Response.json(
      { code: "staging_registration_unavailable" },
      { status: 503, headers },
    );
  }
}
