import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const workspaceRoot = fileURLToPath(new URL("..", import.meta.url));

const backendUrl = new URL(
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000",
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
