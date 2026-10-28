"use client";
import { useRef, useState, useSyncExternalStore, type FormEvent } from "react";
import { authClient } from "@/lib/better-auth/client";
import { navigateAfterAuthentication } from "@/lib/better-auth/client-navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { InputField } from "@/components/ui/field";
import { AuthSeparator, SocialControls } from "./social-controls";
import type { SocialProviderName } from "@/lib/better-auth/social-settings";

const subscribeToHydration = () => () => {};
const clientHydrated = () => true;
const serverHydrated = () => false;

export function BetterAuthForm({
  signUp = false,
  registrationEnabled = false,
  socialProviders = [],
  socialError = false,
}: {
  signUp?: boolean;
  registrationEnabled?: boolean;
  socialProviders?: readonly SocialProviderName[];
  socialError?: boolean;
}) {
  const locked = useRef(false);
  const hydrated = useSyncExternalStore(
    subscribeToHydration,
    clientHydrated,
    serverHydrated,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hydrated || busy || locked.current) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      const credentials = {
        email: String(values.get("email") ?? "").trim(),
        password: String(values.get("password") ?? ""),
      };
      const result = signUp
        ? await authClient.signUp.email({
            ...credentials,
            name: String(values.get("name") ?? "").trim() || "Candidate",
          })
        : await authClient.signIn.email(credentials);
      if (result.error) throw new Error("Authentication failed");
      form.reset();
      navigateAfterAuthentication("/app/dashboard");
    } catch {
      setError(
        "Unable to sign in or create this account. Check your details, or wait before trying again.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <form
      method="post"
      onSubmit={(event) => void submit(event)}
      className="grid w-full max-w-md gap-6 border border-line bg-surface p-6 sm:p-8"
    >
      <h2 className="section-title">
        {signUp ? "Create your account" : "Sign in"}
      </h2>
      {socialError && (
        <p role="alert" className="field-error">
          Social sign-in was not completed. Consent may have been declined or
          the request expired. Use your existing method, or retry with your
          Google or GitHub account. To add a provider to an existing account,
          sign in first and open Account access. GitHub must provide an email
          verified email address; check its email permissions if sign-in keeps
          failing.
        </p>
      )}
      <SocialControls
        providers={socialProviders}
        disabled={busy}
        onBusyChange={setBusy}
      />
      {socialProviders.length > 0 && <AuthSeparator />}
      {signUp && (
        <InputField
          label="Display name (optional)"
          name="name"
          maxLength={150}
          autoComplete="nickname"
          disabled={!hydrated || busy}
        />
      )}
      <InputField
        label="Email address"
        name="email"
        type="email"
        maxLength={254}
        required
        autoComplete="email"
        disabled={!hydrated || busy}
      />
      <InputField
        label="Password"
        name="password"
        type="password"
        minLength={signUp ? 12 : 1}
        maxLength={128}
        required
        autoComplete={signUp ? "new-password" : "current-password"}
        disabled={!hydrated || busy}
        hint={signUp ? "Use 12 to 128 characters." : undefined}
      />
      <p className="text-sm leading-6 text-muted">
        Email ownership is not verified. Password recovery is currently
        unavailable. Keep your password safe.
      </p>
      {error && (
        <p role="alert" className="field-error">
          {error}
        </p>
      )}
      <Button type="submit" disabled={!hydrated || busy}>
        {busy ? "Please wait…" : signUp ? "Create account" : "Sign in"}
      </Button>
      {(signUp || registrationEnabled) && (
        <ButtonLink href={signUp ? "/sign-in" : "/sign-up"} variant="ghost">
          {signUp ? "Already have an account? Sign in" : "Create an account"}
        </ButtonLink>
      )}
    </form>
  );
}
