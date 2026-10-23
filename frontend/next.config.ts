import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const workspaceRoot = fileURLToPath(new URL("..", import.meta.url));

const backendUrl = new URL(
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000",
);
if (
  !["http:", "https:"].includes(backendUrl.protocol) ||
  backendUrl.username ||
  backendUrl.password ||
  backendUrl.pathname !== "/" ||
  backendUrl.search ||
  backendUrl.hash
) {
  throw new Error(
    "BACKEND_INTERNAL_URL must be an HTTP(S) origin without credentials or a path.",
  );
}

if (process.env.VERCEL_ENV === "production") {
  const frontendOrigin = new URL(
    process.env.FRONTEND_ORIGIN ?? "http://invalid",
  );
  const proxySecret = process.env.BACKEND_PROXY_SECRET ?? "";
  if (
    !process.env.BACKEND_INTERNAL_URL ||
    backendUrl.protocol !== "https:" ||
    frontendOrigin.protocol !== "https:" ||
    frontendOrigin.username ||
    frontendOrigin.password ||
    frontendOrigin.pathname !== "/" ||
    frontendOrigin.search ||
    frontendOrigin.hash ||
    proxySecret.length < 32 ||
    proxySecret.length > 256
  )
    throw new Error(
      "Production requires explicit HTTPS frontend/backend origins and BACKEND_PROXY_SECRET.",
    );
  if (
    process.env.PUBLIC_DEMO_ONLY === "true" &&
    (process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
      process.env.CLERK_SECRET_KEY)
  )
    throw new Error("The public demo must not configure account credentials.");
  if (
    process.env.PUBLIC_DEMO_ONLY !== "true" &&
    (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith("pk_live_") ||
      !process.env.CLERK_SECRET_KEY?.startsWith("sk_live_"))
  )
    throw new Error(
      "Production accounts require Clerk production publishable and secret keys, or PUBLIC_DEMO_ONLY=true.",
    );
}

const config: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.resolve(workspaceRoot),
  turbopack: { root: path.resolve(workspaceRoot) },
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl.origin}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          ...(process.env.VERCEL_ENV === "production"
            ? [{ key: "Strict-Transport-Security", value: "max-age=15552000" }]
            : []),
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Content-Security-Policy",
            value: "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
          },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default config;
