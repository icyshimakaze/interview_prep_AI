import type { ReactNode } from "react";
import { AccountWorkspace } from "@/components/account-workspace";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured, accountAuthProvider } from "@/lib/auth-config";
import { BetterAuthWorkspace } from "@/components/better-auth/workspace";
import { readBetterAuthSession } from "@/lib/better-auth/server";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export default async function AccountLayout({
  children,
}: {
  children: ReactNode;
}) {
  if (accountAuthConfigured() && accountAuthProvider() === "better_auth") {
    const session = await readBetterAuthSession(new Headers(await headers()));
    if (!session) redirect("/sign-in");
    return <BetterAuthWorkspace>{children}</BetterAuthWorkspace>;
  }
  return accountAuthConfigured() ? (
    <AccountWorkspace>{children}</AccountWorkspace>
  ) : (
    <AuthSetup />
  );
}
