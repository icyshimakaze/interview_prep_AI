"use client";

import { ClerkLoading, Show, UserButton } from "@clerk/nextjs";
import type { ReactNode } from "react";
import { ButtonLink } from "@/components/ui/button";

export function ConfiguredAuthNavigation({ signIn }: { signIn: ReactNode }) {
  return (
    <>
      <ClerkLoading>{signIn}</ClerkLoading>
      <Show when="signed-out">
        {signIn}
        <ButtonLink href="/sign-up">Sign up</ButtonLink>
      </Show>
      <Show when="signed-in">
        <ButtonLink href="/app/dashboard" variant="outline">
          My workspace
        </ButtonLink>
        <UserButton />
      </Show>
    </>
  );
}
