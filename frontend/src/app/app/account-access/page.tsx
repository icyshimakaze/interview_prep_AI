import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { accountAuthProvider, accountAuthConfigured } from "@/lib/auth-config";
import {
  betterAuthServer,
  readBetterAuthSession,
} from "@/lib/better-auth/server";
import { socialProviderNames } from "@/lib/better-auth/social-settings";
import { SocialControls } from "@/components/better-auth/social-controls";
import { ButtonLink } from "@/components/ui/button";

export default async function AccountAccessPage() {
  if (!accountAuthConfigured() || accountAuthProvider() !== "better_auth")
    redirect("/app/settings");
  const session = await readBetterAuthSession(new Headers(await headers()));
  if (!session) redirect("/sign-in");
  const providers = socialProviderNames(betterAuthServer().settings.social);
  return (
    <section className="grid max-w-xl gap-6 border border-line bg-surface p-6 sm:p-8">
      <h1 className="page-title">Account access</h1>
      <p className="leading-7 text-muted">
        Connect another sign-in method to this account while keeping your saved
        work. Sign in again within five minutes before connecting, then choose
        the provider account you control. Matching email addresses never
        connects accounts automatically.
      </p>
      <SocialControls providers={providers} link />
      {providers.length === 0 && (
        <p>No social providers are enabled in this environment.</p>
      )}
      <p className="text-sm leading-6 text-muted">
        Access is limited to authorized testers. Password recovery and
        verification emails remain unavailable.
      </p>
      <ButtonLink href="/app/settings" variant="ghost">
        Back to settings
      </ButtonLink>
    </section>
  );
}
