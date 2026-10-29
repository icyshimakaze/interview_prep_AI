import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import SignUpPage from "@/app/sign-up/[[...sign-up]]/page";

const policy = vi.hoisted(() => ({
  publicRegistration: true,
  provider: "google" as "google" | "github",
}));
vi.mock("@clerk/nextjs", () => ({ SignUp: () => <p>Clerk sign-up</p> }));
vi.mock("@/lib/auth-config", () => ({
  accountAuthConfigured: () => true,
  accountAuthProvider: () => "better_auth",
}));
vi.mock("@/lib/better-auth/settings", () => ({
  localRegistrationEnabled: () => false,
  betterAuthSettings: () => ({
    social: {
      [policy.provider]: {
        clientId: "synthetic-client",
        clientSecret: "synthetic-secret",
        allowedSubjects: [],
        publicRegistration: policy.publicRegistration,
      },
    },
  }),
}));
vi.mock("@/lib/better-auth/client", () => ({
  authClient: { signIn: { social: vi.fn() } },
}));
vi.mock("@/components/public/public-shell", () => ({
  PublicShell: ({ children }: { children: ReactNode }) => (
    <main>{children}</main>
  ),
}));

describe("hosted social registration page", () => {
  beforeEach(() => {
    policy.publicRegistration = true;
    policy.provider = "google";
  });

  it("offers public OAuth enrollment while keeping email signup absent", () => {
    render(<SignUpPage />);
    expect(
      screen.getByRole("heading", { name: "Create your account" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Continue with Google" }),
    ).toBeVisible();
    expect(
      screen.getByText(/Email\/password registration is unavailable/),
    ).toBeVisible();
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
    expect(
      screen.queryByText("Registration is closed"),
    ).not.toBeInTheDocument();
  });

  it("preserves the closed-registration message for invited configurations", () => {
    policy.publicRegistration = false;
    render(<SignUpPage />);
    expect(
      screen.getByRole("heading", { name: "Registration is closed" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Continue with Google" }),
    ).toBeVisible();
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
  });

  it("offers only GitHub in the public GitHub-only release", () => {
    policy.provider = "github";
    render(<SignUpPage />);
    expect(
      screen.getByRole("button", { name: "Continue with GitHub" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Continue with Google" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Email\/password registration is unavailable/),
    ).toBeVisible();
  });
});
