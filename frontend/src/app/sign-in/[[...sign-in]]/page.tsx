import { BetterAuthForm } from "@/components/better-auth/auth-form";
import { SignIn } from "@clerk/nextjs";
import { Suspense } from "react";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured, accountAuthProvider } from "@/lib/auth-config";
import { PublicShell } from "@/components/public/public-shell";
import {
  betterAuthSettings,
  localRegistrationEnabled,
} from "@/lib/better-auth/settings";
import { socialProviderNames } from "@/lib/better-auth/social-settings";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ social_error?: string }>;
}) {
  const query = await searchParams;
  if (!accountAuthConfigured()) return <AuthSetup />;
  return (
    <PublicShell>
      <div className="public-width grid gap-10 py-16 md:grid-cols-2">
        <div>
          <p className="eyebrow">Welcome back</p>
          <h1 className="editorial-title mt-5">
            Pick up where
            <br />
            you left off.
          </h1>
          <p className="mt-5 max-w-sm leading-8 text-muted">
            Sign in to your private preparation workspace.
          </p>
        </div>
        <div className="flex justify-center">
          <Suspense fallback={<p role="status">Loading sign-in…</p>}>
            {accountAuthProvider() === "better_auth" ? (
              <BetterAuthForm
                socialProviders={socialProviderNames(
                  betterAuthSettings(process.env).social,
                )}
                socialError={query.social_error === "1"}
                registrationEnabled={localRegistrationEnabled(process.env)}
              />
            ) : (
              <SignIn
                routing="path"
                path="/sign-in"
                signUpUrl="/sign-up"
                forceRedirectUrl="/app/dashboard"
              />
            )}
          </Suspense>
        </div>
      </div>
    </PublicShell>
  );
}
