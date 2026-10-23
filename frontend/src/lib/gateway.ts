import { isIP } from "node:net";

// These are request headers only. They must never be sent as response headers.
export function gatewayHeaders(incoming: Headers): Headers | null {
  const forwarded = new Headers(incoming);
  forwarded.delete("x-interview-prep-gateway");
  forwarded.delete("x-interview-prep-client-ip");
  const secret = process.env.BACKEND_PROXY_SECRET;
  if (!secret)
    return process.env.VERCEL_ENV === "production" ? null : forwarded;
  if (secret.length < 32 || secret.length > 256) return null;
  // Vercel overwrites this header at its ingress. Native use is loopback only;
  // generic client-supplied X-Forwarded-For is never a source of trust.
  const address =
    process.env.VERCEL === "1"
      ? incoming.get("x-vercel-forwarded-for")
      : "127.0.0.1";
  if (!address || !isIP(address)) return null;
  forwarded.set("x-interview-prep-gateway", secret);
  forwarded.set("x-interview-prep-client-ip", address);
  return forwarded;
}
