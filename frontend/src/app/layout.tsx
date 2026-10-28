import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";
import { accountAuthConfigured, accountAuthProvider } from "@/lib/auth-config";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: {
    default: "Interview Prep — Preparation with a clear direction",
    template: "%s · Interview Prep",
  },
  description:
    "A focused workspace for your target role, interview practice, and preparation history. Explore the fictional interactive demo.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const content = (
    <>
      <a
        href="#main-content"
        className="sr-only rounded-md bg-accent p-3 text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
      >
        Skip to main content
      </a>
      {children}
    </>
  );
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {accountAuthProvider() === "clerk" && accountAuthConfigured() ? (
          <ClerkProvider
            signInUrl="/sign-in"
            signUpUrl="/sign-up"
            signInFallbackRedirectUrl="/app/dashboard"
            signUpFallbackRedirectUrl="/app/dashboard"
          >
            {content}
          </ClerkProvider>
        ) : (
          content
        )}
      </body>
    </html>
  );
}
