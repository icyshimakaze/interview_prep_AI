import { betterAuthServer } from "@/lib/better-auth/server";
import { authRequest } from "@/lib/better-auth/http";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function handle(request: Request): Promise<Response> {
  try {
    const { auth, pool, settings } = betterAuthServer();
    return await authRequest(
      request,
      auth,
      pool,
      settings,
      process.env.VERCEL === "1",
    );
  } catch {
    return Response.json(
      { code: "auth_unavailable", message: "Account access is unavailable." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export { handle as GET, handle as POST };
