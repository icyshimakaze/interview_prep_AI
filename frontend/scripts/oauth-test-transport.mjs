// SYNTHETIC ONLY. Loaded by owned disposable test processes, never by app source.
import { generateKeyPairSync, sign } from "node:crypto";

export function installSyntheticOAuth(fixture = {}) {
  const { publicKey, privateKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048,
  });
  const jwk = {
    ...publicKey.export({ format: "jwk" }),
    kid: "synthetic-oauth-key",
    alg: "RS256",
    use: "sig",
  };
  const calls = [];
  const encode = (value) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");
  const googleBase = "https://accounts.google.com";
  let githubBob = false;
  globalThis.fetch = async (input, init) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (url === "https://www.googleapis.com/oauth2/v3/certs") {
      calls.push("jwks");
      return Response.json({ keys: [jwk] });
    }
    if (
      url === "https://api.github.com/user" ||
      url === "https://api.github.com/user/emails"
    ) {
      if (
        new Headers(init?.headers).get("authorization") !==
        "Bearer synthetic-provider-access-token"
      )
        throw new Error("Synthetic GitHub requires the exchanged access token");
      const email =
        fixture.email ??
        (githubBob
          ? "social-bob@example.invalid"
          : "social-alice@example.invalid");
      if (url.endsWith("/emails")) {
        calls.push("github_emails");
        if (fixture.emailApiFailure)
          return Response.json(
            { message: "synthetic unavailable" },
            { status: 403 },
          );
        return Response.json(
          fixture.missingEmail
            ? []
            : [
                {
                  email,
                  primary: true,
                  verified: !fixture.unverifiedEmail,
                  visibility: "private",
                },
              ],
        );
      }
      calls.push("github_user");
      if (fixture.userApiFailure)
        return Response.json(
          { message: "synthetic unavailable" },
          { status: 401 },
        );
      return Response.json({
        id: fixture.githubId ?? (githubBob ? 10002 : 10001),
        login: fixture.githubLogin ?? "synthetic-candidate",
        name: "Synthetic OAuth Candidate",
        email: fixture.missingEmail || fixture.privateEmail ? null : email,
        avatar_url: "https://avatars.githubusercontent.com/synthetic",
      });
    }
    const provider =
      url === "https://oauth2.googleapis.com/token"
        ? "google"
        : url === "https://github.com/login/oauth/access_token"
          ? "github"
          : null;
    if (!provider)
      throw new Error(
        "Synthetic OAuth blocks every non-fixture network destination",
      );
    calls.push(provider + "_token");
    const body = new URLSearchParams(init?.body ?? "");
    const browserBob = fixture.browser && body.get("code") === "synthetic-bob";
    if (
      !body.get("code_verifier") ||
      body.get("grant_type") !== "authorization_code" ||
      !body.get("redirect_uri")?.endsWith("/api/auth/callback/" + provider)
    )
      throw new Error("Synthetic exchange requires PKCE and exact callback");
    if (fixture.invalidCode)
      return Response.json({ error: "invalid_grant" }, { status: 400 });
    if (provider === "github") {
      githubBob = browserBob;
      return Response.json({
        token_type: "Bearer",
        access_token: "synthetic-provider-access-token",
        scope: "user:email",
      });
    }
    const now = Math.floor(Date.now() / 1000);
    const claims = {
      iss: googleBase,
      aud: fixture.wrongAudience
        ? "wrong-client"
        : "synthetic-google-client.apps.googleusercontent.com",
      sub:
        fixture.sub ??
        (browserBob ? "synthetic-google-bob" : "synthetic-google-alice"),
      iat: now,
      exp: fixture.expired ? now - 120 : now + 300,
      name: "Synthetic OAuth Candidate",
      email:
        fixture.email ??
        (browserBob
          ? "social-bob@example.invalid"
          : "social-alice@example.invalid"),
      email_verified: !fixture.unverifiedEmail,
    };
    if (fixture.wrongIssuer) claims.iss = "https://untrusted.example.invalid";
    if (fixture.missingEmail) delete claims.email;
    const unsigned =
      encode({ alg: "RS256", kid: jwk.kid }) + "." + encode(claims);
    const signature = sign(
      "RSA-SHA256",
      Buffer.from(unsigned),
      privateKey,
    ).toString("base64url");
    return Response.json({
      token_type: "Bearer",
      access_token: "synthetic-provider-access-token",
      refresh_token: "synthetic-provider-refresh-token",
      expires_in: 300,
      id_token:
        unsigned +
        "." +
        (fixture.badSignature
          ? signature.slice(0, -8) + "AAAAAAAA"
          : signature),
      scope: "openid profile email",
    });
  };
  return calls;
}
