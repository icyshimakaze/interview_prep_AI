"use client";
import { useRef, useState, useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import { authClient } from "@/lib/better-auth/client";
import { navigateToSocialProvider } from "@/lib/better-auth/social-navigation";
import {
  SOCIAL_ERROR_PATH,
  SOCIAL_LINK_PATH,
  SOCIAL_SUCCESS_PATH,
  type SocialProviderName,
} from "@/lib/better-auth/social-settings";

function ProviderIcon({ provider }: { provider: SocialProviderName }) {
  return provider === "github" ? (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      className="size-5 shrink-0"
    >
      <path
        fill="currentColor"
        d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.03a9.6 9.6 0 0 1 5 0c1.91-1.3 2.75-1.03 2.75-1.03.55 1.38.2 2.4.1 2.65.64.7 1.03 1.6 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86v2.59c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"
      />
    </svg>
  ) : (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 48 48"
      className="size-5 shrink-0"
    >
      <path
        fill="#4285f4"
        d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5h6.7c3.9-3.6 6-8.8 6-14.9Z"
      />
      <path
        fill="#34a853"
        d="M24 44c5.5 0 10.1-1.8 13.5-4.9l-6.7-5c-1.9 1.3-4.3 2-6.8 2-5.3 0-9.8-3.6-11.4-8.4H5.7v5.2A20.4 20.4 0 0 0 24 44Z"
      />
      <path
        fill="#fbbc05"
        d="M12.6 27.7a12 12 0 0 1 0-7.4v-5.2H5.7a20 20 0 0 0 0 17.8Z"
      />
      <path
        fill="#ea4335"
        d="M24 11.9c3 0 5.7 1 7.8 3l5.8-5.8A19.7 19.7 0 0 0 24 4 20.4 20.4 0 0 0 5.7 15.1l6.9 5.2C14.2 15.5 18.7 11.9 24 11.9Z"
      />
    </svg>
  );
}

const subscribe = () => () => {};

export function SocialControls({
  providers,
  link = false,
  disabled = false,
  onBusyChange,
}: {
  providers: readonly SocialProviderName[];
  link?: boolean;
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const hydrated = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const locked = useRef(false);
  const [pending, setPending] = useState<SocialProviderName | null>(null);
  const [error, setError] = useState(false);
  if (!providers.length) return null;
  async function start(provider: SocialProviderName) {
    if (!hydrated || disabled || locked.current) return;
    locked.current = true;
    setPending(provider);
    setError(false);
    onBusyChange?.(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const body = {
        provider,
        callbackURL: link ? SOCIAL_LINK_PATH : SOCIAL_SUCCESS_PATH,
        errorCallbackURL: SOCIAL_ERROR_PATH,
        disableRedirect: true,
      };
      const result = link
        ? await authClient.linkSocial(body, { signal: controller.signal })
        : await authClient.signIn.social(body, { signal: controller.signal });
      if (result.error) throw new Error("Social sign-in unavailable");
      navigateToSocialProvider(result.data?.url, provider);
    } catch {
      setError(true);
    } finally {
      clearTimeout(timer);
      locked.current = false;
      setPending(null);
      onBusyChange?.(false);
    }
  }
  return (
    <div className="grid gap-3">
      {providers.map((provider) => {
        const name = provider === "google" ? "Google" : "GitHub";
        return (
          <Button
            key={provider}
            variant="outline"
            className="w-full"
            disabled={!hydrated || disabled || pending !== null}
            aria-busy={pending === provider}
            onClick={() => void start(provider)}
          >
            <ProviderIcon provider={provider} />
            {pending === provider
              ? `Opening ${name}…`
              : link
                ? `Connect ${name}`
                : `Continue with ${name}`}
          </Button>
        );
      })}
      {pending && (
        <p role="status" className="text-sm text-muted">
          Opening secure account selection…
        </p>
      )}
      {error && (
        <p role="alert" className="field-error">
          {link
            ? "Account connection could not start. Sign out and sign in again, then retry. Both accounts must be authorized for this test."
            : "Social sign-in could not start. Try again or use your existing sign-in method."}
        </p>
      )}
    </div>
  );
}

export function AuthSeparator() {
  return (
    <div
      role="separator"
      aria-label="or continue with email"
      className="flex items-center gap-3 text-xs text-muted"
    >
      <span className="h-px flex-1 bg-line" />
      <span>or continue with email</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}
