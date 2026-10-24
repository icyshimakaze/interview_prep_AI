import { SignUp } from "@clerk/nextjs";
import { Suspense } from "react";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured } from "@/lib/auth-config";
import { PublicShell } from "@/components/public/public-shell";

export default function SignUpPage() {
  if (!accountAuthConfigured()) return <AuthSetup />;
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
            <SignUp
              routing="path"
              path="/sign-up"
              signInUrl="/sign-in"
              forceRedirectUrl="/app/dashboard"
            />
          </Suspense>
        </div>
      </div>
    </PublicShell>
  );
}
