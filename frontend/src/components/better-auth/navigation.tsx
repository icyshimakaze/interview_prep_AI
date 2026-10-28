"use client";
import { authClient } from "@/lib/better-auth/client";
import { ButtonLink } from "@/components/ui/button";

export function BetterAuthNavigation({
  registrationEnabled = false,
}: {
  registrationEnabled?: boolean;
}) {
  const session = authClient.useSession();
  if (session.isPending)
    return (
      <p role="status" className="text-sm text-muted">
        Checking account…
      </p>
    );
  return session.data ? (
    <>
      <ButtonLink href="/app/dashboard" variant="outline">
        My workspace
      </ButtonLink>
      <ButtonLink href="/app/settings" variant="ghost">
        Account
      </ButtonLink>
    </>
  ) : (
    <>
      <ButtonLink href="/sign-in" variant="outline">
        Sign in
      </ButtonLink>
      {registrationEnabled && <ButtonLink href="/sign-up">Sign up</ButtonLink>}
    </>
  );
}
