import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthNavigation } from "@/components/public/auth-navigation";

const auth = vi.hoisted(() => ({ configured: false, signedIn: false }));

vi.mock("@/lib/auth-config", () => ({
  accountAuthConfigured: () => auth.configured,
  accountAuthProvider: () => "clerk",
}));

vi.mock("@clerk/nextjs", () => ({
  ClerkLoading: () => null,
  Show: ({
    when,
    children,
  }: {
    when: "signed-in" | "signed-out";
    children: ReactNode;
  }) => {
    if (!auth.configured) throw new Error("Clerk provider is unavailable");
    return (when === "signed-in") === auth.signedIn ? children : null;
  },
  UserButton: () => <button type="button">Manage account</button>,
}));

beforeEach(() => {
  auth.configured = false;
  auth.signedIn = false;
});

describe("public authentication navigation", () => {
  it("keeps the missing-key fallback usable without a Clerk provider", () => {
    render(<AuthNavigation />);
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/sign-in",
    );
    expect(screen.queryByRole("link", { name: "Sign up" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Manage account" })).toBeNull();
  });

  it("offers sign-in and sign-up when signed out of configured accounts", () => {
    auth.configured = true;
    render(<AuthNavigation />);
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/sign-in",
    );
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
    expect(screen.queryByRole("button", { name: "Manage account" })).toBeNull();
  });

  it("shows workspace and profile controls after sign-in", () => {
    auth.configured = true;
    auth.signedIn = true;
    render(<AuthNavigation />);
    expect(screen.getByRole("link", { name: "My workspace" })).toHaveAttribute(
      "href",
      "/app/dashboard",
    );
    expect(
      screen.getByRole("button", { name: "Manage account" }),
    ).toBeVisible();
    expect(screen.queryByRole("link", { name: "Sign in" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Sign up" })).toBeNull();
  });
});
