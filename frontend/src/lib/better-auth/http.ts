import { isIP } from "node:net";
import type { Pool } from "pg";
import {
  createLimiter,
  type AuthSettings,
  type createBetterAuth,
} from "./factory";
import {
  safeSocialLocation,
  socialProviderEnabled,
  socialRequestBody,
  validSocialCallback,
} from "./social-http";
import { SOCIAL_ERROR_PATH, SOCIAL_FRESH_SECONDS } from "./social-settings";

type Auth = ReturnType<typeof createBetterAuth>;
const reads = new Set(["/ok", "/get-session", "/token", "/jwks"]);
const writes = new Set(["/sign-in/email", "/sign-up/email", "/sign-out"]);
const safeHeaders = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};

function failure(status: number, code: string, retryAfter?: number) {
  return Response.json(
    { code, message: "The account request could not be completed." },
    {
      status,
      headers: {
        ...safeHeaders,
        ...(retryAfter ? { "Retry-After": String(retryAfter) } : {}),
      },
    },
  );
}

export async function authRequest(
  request: Request,
  auth: Auth,
  pool: Pool,
  settings: AuthSettings,
  vercel: boolean,
  registrationEmails?: ReadonlySet<string>,
): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname.slice("/api/auth".length);
  const callbackProvider = /^\/callback\/(google|github)$/.exec(path)?.[1];
  const callback = Boolean(callbackProvider);
  const social = path === "/sign-in/social" || path === "/link-social";
  if (social && !settings.social?.google && !settings.social?.github)
    return failure(404, "auth_route_unavailable");
  if (
    callback &&
    request.method === "GET" &&
    url.origin === settings.origin &&
    !socialProviderEnabled(settings.social, callbackProvider)
  )
    return new Response(null, {
      status: 303,
      headers: {
        ...safeHeaders,
        Location: settings.origin + SOCIAL_ERROR_PATH,
      },
    });
  if (path === "/sign-up/email" && !settings.registrationEnabled)
    return failure(404, "auth_registration_closed");
  if (
    url.origin !== settings.origin ||
    !(request.method === "GET"
      ? reads.has(path) ||
        (callback &&
          socialProviderEnabled(settings.social, callbackProvider) &&
          validSocialCallback(url))
      : request.method === "POST" && (writes.has(path) || social))
  )
    return failure(404, "auth_route_unavailable");
  if (
    request.method === "POST" &&
    (request.headers.get("origin") !== settings.origin ||
      request.headers.get("sec-fetch-site") === "cross-site" ||
      request.headers.get("content-type")?.split(";")[0] !== "application/json")
  )
    return failure(403, "auth_origin_required");
  const peer = vercel
    ? request.headers.get("x-vercel-forwarded-for")
    : "127.0.0.1";
  if (!peer || !isIP(peer)) return failure(503, "auth_gateway_unavailable");
  const headers = new Headers(request.headers);
  headers.delete("x-interview-auth-peer");
  headers.set("x-interview-auth-peer", peer);
  let body: string | undefined;
  try {
    const limit =
      path === "/sign-in/email" ? 5 : path === "/sign-up/email" ? 3 : 120;
    const ingress = await createLimiter(pool, settings.rateLimitKey).consume(
      "ingress:" + peer + ":" + path,
      { window: 60, max: limit },
    );
    if (!ingress.allowed) return failure(429, "auth_rate_limited", 60);
    if (request.method === "POST") {
      if (
        request.headers.get("content-encoding") &&
        request.headers.get("content-encoding") !== "identity"
      )
        return failure(415, "auth_encoding");
      const reader = request.body?.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      if (reader) {
        let expired = false;
        const timer = setTimeout(() => {
          expired = true;
          void reader.cancel().catch(() => undefined);
        }, 5000);
        try {
          while (true) {
            const next = await reader.read();
            if (expired) return failure(408, "auth_request_timeout");
            if (next.done) break;
            size += next.value.length;
            if (size > 16384) {
              await reader.cancel();
              return failure(413, "auth_request_size");
            }
            chunks.push(next.value);
          }
        } finally {
          clearTimeout(timer);
          reader.releaseLock();
        }
      }
      body = Buffer.concat(chunks).toString("utf8");
      let input: unknown;
      try {
        input = JSON.parse(body);
      } catch {
        return failure(422, "auth_input");
      }
      if (!input || typeof input !== "object" || Array.isArray(input))
        return failure(422, "auth_input");
      let values = input as Record<string, unknown>;
      if (social) {
        const normalized = socialRequestBody(
          values,
          settings.origin,
          path === "/link-social",
          settings.social,
        );
        if (!normalized) return failure(400, "auth_social_request_unavailable");
        values = normalized;
        body = JSON.stringify(normalized);
        if (path === "/link-social") {
          const current = await auth.api.getSession({
            headers,
            query: { disableRefresh: true },
          });
          if (!current) return failure(401, "auth_session_required");
          if (
            Date.now() - current.session.createdAt.getTime() >
            SOCIAL_FRESH_SECONDS * 1000
          )
            return failure(403, "auth_recent_session_required");
        }
      }
      if (
        !social &&
        path !== "/sign-out" &&
        (typeof values.email !== "string" ||
          values.email.length > 254 ||
          typeof values.password !== "string" ||
          values.password.length > 128 ||
          (path === "/sign-up/email" &&
            (typeof values.name !== "string" || values.name.length > 150)))
      )
        return failure(422, "auth_input");
      if (
        path === "/sign-up/email" &&
        registrationEmails &&
        !registrationEmails.has(String(values.email).trim().toLowerCase())
      )
        return failure(404, "auth_registration_closed");
      if (path === "/sign-in/email" || path === "/sign-up/email") {
        const decision = await createLimiter(
          pool,
          settings.rateLimitKey,
        ).consume("identifier:" + String(values.email).trim().toLowerCase(), {
          window: 900,
          max: 15,
        });
        if (!decision.allowed) return failure(429, "auth_rate_limited", 900);
      }
    }
    const response = await auth.handler(
      new Request(request.url, {
        method: request.method,
        headers,
        body,
      }),
    );
    if (response.status >= 500) return failure(503, "auth_unavailable");
    const outgoing = new Headers(response.headers);
    for (const [key, value] of Object.entries(safeHeaders))
      outgoing.set(key, value);
    if (callback && response.status >= 300 && response.status < 400)
      outgoing.set(
        "Location",
        safeSocialLocation(response.headers.get("location"), settings.origin),
      );
    if (
      ["/sign-in/email", "/sign-up/email", "/get-session"].includes(path) &&
      response.ok
    ) {
      const value: unknown = await response.json();
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const data = { ...value } as Record<string, unknown>;
        delete data.token;
        if (
          data.session &&
          typeof data.session === "object" &&
          !Array.isArray(data.session)
        ) {
          const session = { ...data.session } as Record<string, unknown>;
          delete session.token;
          data.session = session;
        }
        outgoing.delete("content-length");
        return Response.json(data, {
          status: response.status,
          headers: outgoing,
        });
      }
      return Response.json(value, {
        status: response.status,
        headers: outgoing,
      });
    }
    return new Response(response.body, {
      status: response.status,
      headers: outgoing,
    });
  } catch {
    // Never return/log driver, request, password or key material.
    return failure(503, "auth_unavailable");
  }
}
