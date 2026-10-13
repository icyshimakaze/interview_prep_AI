import type { ReactNode } from "react";
import { AccountWorkspace } from "@/components/account-workspace";
import { AuthSetup } from "@/components/auth-setup";
import { accountAuthConfigured } from "@/lib/auth-config";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return accountAuthConfigured() ? (
    <AccountWorkspace>{children}</AccountWorkspace>
  ) : (
    <AuthSetup />
  );
}
