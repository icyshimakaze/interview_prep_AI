"use client";

import { useAuth, useClerk } from "@clerk/nextjs";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { ButtonLink } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { WorkspaceShell } from "@/components/workspace/workspace-shell";
import { WorkspaceContext } from "@/components/workspace/workspace-context";
import {
  parseDashboard,
  workspaceRequest,
  type Dashboard,
  type ProfileInput,
} from "@/lib/api/workspace";

export function AccountWorkspace({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, userId } = useAuth();
  if (!isLoaded)
    return (
      <WorkspaceShell mode="account">
        <WorkspaceSkeleton label="Checking your session…" />
      </WorkspaceShell>
    );
  if (!isSignedIn || !userId)
    return (
      <WorkspaceShell mode="account">
        <h1 className="page-title mb-6">Sign in to your workspace</h1>
        <ButtonLink href="/sign-in">Sign in</ButtonLink>
      </WorkspaceShell>
    );
  // A subject change remounts all private data, forms and pending UI state.
  return <AccountSession key={userId}>{children}</AccountSession>;
}

function AccountSession({ children }: { children: ReactNode }) {
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const router = useRouter();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  const authenticatedRequest = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = await getToken({ template: "interview-prep-api" });
      if (!active.current)
        throw new Error(
          "Your account changed. Open your current workspace again.",
        );
      if (!token) throw new Error("Sign in again to open your workspace.");
      const headers = new Headers(init.headers);
      headers.set("Authorization", `Bearer ${token}`);
      return workspaceRequest(path, { ...init, headers });
    },
    [getToken],
  );
  const readDashboard = useCallback(
    async (signal?: AbortSignal) => {
      const result = parseDashboard(
        await (
          await authenticatedRequest("/api/v1/account/dashboard", { signal })
        ).json(),
      );
      if (result.mode !== "account")
        throw new Error("The account workspace response is invalid.");
      return result;
    },
    [authenticatedRequest],
  );
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const load = async () => {
      await authenticatedRequest("/api/v1/account/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
        signal: controller.signal,
      });
      const result = await readDashboard(controller.signal);
      if (active) setData(result);
    };
    void load().catch((reason: unknown) => {
      if (active)
        setError(
          reason instanceof Error
            ? reason.message
            : "Your workspace could not load.",
        );
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [authenticatedRequest, readDashboard, attempt]);
  function reload() {
    setData(null);
    setError(null);
    setAttempt((value) => value + 1);
  }
  async function saveProfile(profile: ProfileInput) {
    setBusy(true);
    try {
      await authenticatedRequest("/api/v1/account/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      try {
        setData(await readDashboard());
      } catch {
        throw new Error(
          "Your save was accepted, but the updated profile could not be loaded. Reload the saved profile before editing again.",
        );
      }
    } finally {
      setBusy(false);
    }
  }
  async function leave() {
    setBusy(true);
    setData(null);
    setError(null);
    try {
      await signOut();
      router.replace("/");
      router.refresh();
    } catch {
      setError("Sign-out could not complete. Please try again.");
      setBusy(false);
    }
  }
  return (
    <WorkspaceShell mode="account" onLeave={() => void leave()} busy={busy}>
      {error && (
        <ErrorDisplay
          title="Your workspace needs attention"
          message={error}
          onRetry={reload}
        />
      )}
      {data ? (
        <WorkspaceContext
          value={{ data, busy, onSaveProfile: saveProfile, onReload: reload }}
        >
          {children}
        </WorkspaceContext>
      ) : (
        !error && (
          <WorkspaceSkeleton label={busy ? "Signing out…" : undefined} />
        )
      )}
    </WorkspaceShell>
  );
}
