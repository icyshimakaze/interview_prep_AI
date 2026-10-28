import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import {
  NextResponse,
  type NextFetchEvent,
  type NextRequest,
} from "next/server";
import { gatewayHeaders } from "@/lib/gateway";

const protectedRoute = createRouteMatcher(["/app(.*)"]);
const accountProxy = clerkMiddleware(
  async (auth, request) => {
    if (protectedRoute(request)) await auth.protect();
  },
  {
    signInUrl: "/sign-in",
    signUpUrl: "/sign-up",
    authorizedParties:
      process.env.VERCEL_ENV === "production"
        ? process.env.FRONTEND_ORIGIN
          ? [process.env.FRONTEND_ORIGIN]
          : []
        : [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            ...(process.env.FRONTEND_ORIGIN
              ? [process.env.FRONTEND_ORIGIN]
              : []),
          ],
  },
);

export default function proxy(request: NextRequest, event: NextFetchEvent) {
  if (request.nextUrl.pathname.startsWith("/api/v1/")) {
    const headers = gatewayHeaders(request.headers);
    if (!headers)
      return NextResponse.json(
        {
          code: "gateway_unavailable",
          message: "The application gateway is not configured.",
        },
        { status: 503, headers: { "Cache-Control": "no-store" } },
      );
    return NextResponse.next({ request: { headers } });
  }
  if (
    (process.env.AUTH_PROVIDER ?? "clerk") !== "clerk" ||
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
    !process.env.CLERK_SECRET_KEY
  ) {
    return NextResponse.next();
  }
  return accountProxy(request, event);
}

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/api/(.*)"],
};
