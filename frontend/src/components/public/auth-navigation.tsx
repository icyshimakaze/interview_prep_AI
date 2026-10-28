import { Suspense } from "react";
import { ButtonLink } from "@/components/ui/button";
import { accountAuthConfigured, accountAuthProvider } from "@/lib/auth-config";
import { BetterAuthNavigation } from "@/components/better-auth/navigation";
import { ConfiguredAuthNavigation } from "./configured-auth-navigation";
import { localRegistrationEnabled } from "@/lib/better-auth/settings";

export function AuthNavigation() {
  const signIn = (
    <ButtonLink href="/sign-in" variant="outline">
      Sign in
    </ButtonLink>
  );

  if (!accountAuthConfigured()) return signIn;
  if (accountAuthProvider() === "better_auth")
    return (
      <div className="flex items-center gap-3">
        <BetterAuthNavigation
          registrationEnabled={localRegistrationEnabled(process.env)}
        />
      </div>
    );

  return (
    <div className="flex items-center gap-3">
      <Suspense fallback={signIn}>
        <ConfiguredAuthNavigation signIn={signIn} />
      </Suspense>
    </div>
  );
}
