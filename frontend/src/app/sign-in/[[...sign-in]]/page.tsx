import { SignIn } from "@clerk/nextjs";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured } from "@/lib/auth-config";
import { PublicShell } from "@/components/public/public-shell";

export default function SignInPage() {
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
          <SignIn
            routing="path"
            path="/sign-in"
            signUpUrl="/sign-up"
            forceRedirectUrl="/app/dashboard"
          />
        </div>
      </div>
    </PublicShell>
  );
}
