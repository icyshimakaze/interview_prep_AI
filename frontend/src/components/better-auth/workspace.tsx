"use client";
import { useCallback, type ReactNode } from "react";
import { authClient } from "@/lib/better-auth/client";
import { AccountSession } from "@/components/account-workspace";
import { WorkspaceShell } from "@/components/workspace/workspace-shell";
import { WorkspaceSkeleton } from "@/components/ui/states";
import { ButtonLink } from "@/components/ui/button";
import { navigateAfterAuthentication } from "@/lib/better-auth/client-navigation";

export function BetterAuthWorkspace({ children }: { children: ReactNode }) {
  const session = authClient.useSession();
  const getToken = useCallback(async () => {
    const result = await authClient.token();
    if (result.error) {
      await authClient.getSession();
      throw new Error("Sign in again to open your workspace.");
    }
    return result.data?.token ?? null;
  }, []);
  const signOut = useCallback(async () => {
    const result = await authClient.signOut();
    if (result.error) throw new Error("Sign-out could not complete.");
  }, []);
  if (session.isPending)
    return (
      <WorkspaceShell mode="account">
        <WorkspaceSkeleton label="Checking your session…" />
      </WorkspaceShell>
    );
  if (!session.data)
    return (
      <WorkspaceShell mode="account">
        <h1 className="page-title mb-6">Sign in to your workspace</h1>
        <ButtonLink href="/sign-in">Sign in</ButtonLink>
      </WorkspaceShell>
    );
  return (
    <AccountSession
      key={session.data.user.id}
      getToken={getToken}
      signOut={signOut}
      onSignedOut={() => navigateAfterAuthentication("/")}
      userControl={
        <ButtonLink href="/app/account-access" variant="ghost">
          Account
        </ButtonLink>
      }
    >
      {children}
    </AccountSession>
  );
}
