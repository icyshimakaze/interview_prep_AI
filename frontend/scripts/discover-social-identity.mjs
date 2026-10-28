// Manual local operator enrollment. No application database or account creation.
import { createServer } from "node:http";
import { randomBytes } from "node:crypto";
import { registerHooks } from "node:module";
import { betterAuth } from "better-auth";
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (
      specifier.startsWith("./") &&
      context.parentURL?.includes("/src/lib/better-auth/") &&
      !specifier.endsWith(".ts")
    )
      return nextResolve(specifier + ".ts", context);
    return nextResolve(specifier, context);
  },
});
const { configuredSocialProviders } =
  await import("../src/lib/better-auth/social-providers.ts");

const provider = process.argv[2];
if (!["google", "github"].includes(provider))
  throw new Error("Choose google or github");
const prefix = provider.toUpperCase();
const clientId = process.env[prefix + "_CLIENT_ID"];
const clientSecret = process.env[prefix + "_CLIENT_SECRET"];
if (!clientId || !clientSecret || /REPLACE|YOUR_/.test(clientId + clientSecret))
  throw new Error(
    "Set provider credentials securely before local identity discovery",
  );
const port = Number(process.env.SOCIAL_DISCOVERY_PORT ?? "3000");
if (!Number.isInteger(port) || port < 1024 || port > 65535)
  throw new Error("Choose an unprivileged local port");
const origin = "http://localhost:" + port;
const settings = {
  [provider]: {
    clientId,
    clientSecret,
    allowedSubjects: [],
  },
};
const auth = betterAuth({
  baseURL: origin,
  secret: randomBytes(32).toString("hex"),
  telemetry: { enabled: false },
  logger: { disabled: true },
  trustedOrigins: [origin],
  socialProviders: configuredSocialProviders(settings),
  emailAndPassword: { enabled: false },
  account: { accountLinking: { enabled: false } },
  onAPIError: { errorURL: origin + "/complete" },
  user: {
    validateUserInfo: async ({ source }) => {
      const profile = source.oauth?.profile;
      const subject =
        provider === "google"
          ? profile?.sub
          : typeof profile?.id === "number" || typeof profile?.id === "string"
            ? String(profile.id)
            : undefined;
      if (
        source.method === "oauth" &&
        source.oauth?.providerId === provider &&
        typeof subject === "string"
      )
        console.log(
          JSON.stringify({
            verified_provider: provider,
            allowed_subject: subject,
            account_created: false,
          }),
        );
      return { error: "operator_discovery_only_no_account" };
    },
  },
});
const server = createServer(async (incoming, outgoing) => {
  try {
    const url = new URL(incoming.url ?? "/", origin);
    if (
      ["/", "/complete"].includes(url.pathname) &&
      incoming.method === "GET"
    ) {
      outgoing.writeHead(200, {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
      });
      outgoing.end(
        url.pathname === "/complete"
          ? "<h1>Discovery finished</h1><p>If verification succeeded, the terminal contains only the provider subject. No account was created. Close this tab and stop the local server.</p>"
          : `<h1>Local ${provider} identity discovery</h1><p>Use only your authorized test account. No InterviewOS account or database is modified.</p><button id="start">Continue</button><p id="status"></p><script>document.getElementById('start').onclick=async()=>{try{const r=await fetch('/api/auth/sign-in/social',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider:'${provider}',callbackURL:'${origin}/complete',errorCallbackURL:'${origin}/complete',disableRedirect:true})});const d=await r.json();if(!r.ok||!d.url)throw Error();location.assign(d.url)}catch{document.getElementById('status').textContent='Could not start. Check your registration and retry.'}}</script>`,
      );
      return;
    }
    if (!(
      (url.pathname === "/api/auth/sign-in/social" &&
        incoming.method === "POST" &&
        incoming.headers.origin === origin) ||
      (url.pathname === "/api/auth/callback/" + provider &&
        incoming.method === "GET")
    )) {
      outgoing.writeHead(404);
      outgoing.end();
      return;
    }
    let size = 0;
    for await (const chunk of incoming) {
      size += chunk.length;
      if (size > 16384) throw new Error("bounded_request");
    }
    const headers = new Headers();
    for (const [key, value] of Object.entries(incoming.headers))
      if (typeof value === "string") headers.set(key, value);
    const response = await auth.handler(
      new Request(url, {
        method: incoming.method,
        headers,
        ...(incoming.method === "POST"
          ? {
              body: JSON.stringify({
                provider,
                callbackURL: origin + "/complete",
                errorCallbackURL: origin + "/complete",
                disableRedirect: true,
              }),
            }
          : {}),
      }),
    );
    outgoing.writeHead(response.status, {
      ...Object.fromEntries(response.headers),
      ...(url.pathname.startsWith("/api/auth/callback/") &&
      response.status >= 300 &&
      response.status < 400
        ? { location: origin + "/complete" }
        : {}),
      "set-cookie": response.headers.getSetCookie(),
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
    });
    outgoing.end(Buffer.from(await response.arrayBuffer()));
  } catch {
    outgoing.writeHead(503);
    outgoing.end("Discovery unavailable. No account created.");
  }
});
server.requestTimeout = 10000;
server.on("error", (error) => {
  console.error(
    "Local discovery could not start; choose a free registered callback port. " +
      (error.code === "EADDRINUSE"
        ? "Port is already in use."
        : "Local listener unavailable."),
  );
  process.exitCode = 1;
});
server.listen(port, "127.0.0.1", () =>
  console.log(
    "Open " + origin + " using an authorized test account. Stop with Ctrl+C.",
  ),
);
setTimeout(
  () => {
    server.closeAllConnections();
    server.close();
  },
  10 * 60 * 1000,
).unref();
