import { BetterAuthForm } from "@/components/better-auth/auth-form";
import { SignUp } from "@clerk/nextjs";
import { Suspense } from "react";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured, accountAuthProvider } from "@/lib/auth-config";
import { PublicShell } from "@/components/public/public-shell";
import {
  betterAuthSettings,
  localRegistrationEnabled,
} from "@/lib/better-auth/settings";
import { socialProviderNames } from "@/lib/better-auth/social-settings";
import {
  AuthSeparator,
  SocialControls,
} from "@/components/better-auth/social-controls";
import { ButtonLink } from "@/components/ui/button";

export default function SignUpPage() {
  if (!accountAuthConfigured()) return <AuthSetup />;
  const social =
    accountAuthProvider() === "better_auth"
      ? betterAuthSettings(process.env).social
      : {};
  const providers = socialProviderNames(social);
  const publicSocialRegistration = Object.values(social).some(
    (provider) => provider?.publicRegistration === true,
  );
  return (
    <PublicShell>
      <div className="public-width grid gap-10 py-16 md:grid-cols-2">
        <div>
          <p className="eyebrow">A place to begin</p>
          <h1 className="editorial-title mt-5">
            Give your preparation
            <br />a direction.
          </h1>
          <p className="mt-5 max-w-sm leading-8 text-muted">
            Create an account to save your preparation profile. Practice
            workflows are still in development.
          </p>
        </div>
        <div className="flex justify-center">
          <Suspense fallback={<p role="status">Loading sign-up…</p>}>
            {accountAuthProvider() === "better_auth" ? (
              localRegistrationEnabled(process.env) ? (
                <BetterAuthForm
                  signUp
                  registrationEnabled
                  socialProviders={providers}
                />
              ) : (
                <div className="grid max-w-md gap-6 border border-line bg-surface p-6 sm:p-8">
                  <h2 className="section-title">
                    {publicSocialRegistration
                      ? "Create your account"
                      : "Registration is closed"}
                  </h2>
                  <p>
                    {publicSocialRegistration
                      ? "Continue with an available provider to create your account. Email/password registration is unavailable."
                      : "Public registration awaits a reviewed release policy. Authorized testers can use an enabled sign-in method below."}
                  </p>
                  <SocialControls providers={providers} />
                  <AuthSeparator />
                  <ButtonLink href="/sign-in">Sign in with email</ButtonLink>
                </div>
              )
            ) : (
              <SignUp
                routing="path"
                path="/sign-up"
                signInUrl="/sign-in"
                forceRedirectUrl="/app/dashboard"
              />
            )}
          </Suspense>
        </div>
      </div>
    </PublicShell>
  );
}
