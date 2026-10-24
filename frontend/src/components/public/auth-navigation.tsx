import { Suspense } from "react";
import { ButtonLink } from "@/components/ui/button";
import { accountAuthConfigured } from "@/lib/auth-config";
import { ConfiguredAuthNavigation } from "./configured-auth-navigation";

export function AuthNavigation() {
  const signIn = (
    <ButtonLink href="/sign-in" variant="outline">
      Sign in
    </ButtonLink>
  );

  if (!accountAuthConfigured()) return signIn;

  return (
    <div className="flex items-center gap-3">
      <Suspense fallback={signIn}>
        <ConfiguredAuthNavigation signIn={signIn} />
      </Suspense>
    </div>
  );
}
