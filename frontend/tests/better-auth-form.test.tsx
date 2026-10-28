import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BetterAuthForm } from "@/components/better-auth/auth-form";

const auth = vi.hoisted(() => ({
  signIn: vi.fn(),
  signUp: vi.fn(),
  replace: vi.fn(),
}));
vi.mock("@/lib/better-auth/client", () => ({
  authClient: {
    signIn: { email: auth.signIn },
    signUp: { email: auth.signUp },
  },
}));
vi.mock("@/lib/better-auth/client-navigation", () => ({
  navigateAfterAuthentication: auth.replace,
}));
beforeEach(() => {
  auth.signIn.mockResolvedValue({ data: {} });
  auth.signUp.mockResolvedValue({ data: {} });
});

describe("password-only auth form in existing design", () => {
  it.each([false, true])(
    "prevents native credential GET submission before hydration (signup=%s)",
    (signUp) => {
      const document = new DOMParser().parseFromString(
        renderToStaticMarkup(<BetterAuthForm signUp={signUp} />),
        "text/html",
      );
      const form = document.querySelector("form");
      expect(form?.getAttribute("method")).toBe("post");
      const controls = [
        ...document.querySelectorAll("input,button[type=submit]"),
      ];
      expect(controls.length).toBeGreaterThanOrEqual(3);
      for (const control of controls)
        expect(control.hasAttribute("disabled")).toBe(true);
    },
  );
  it("does not offer public registration by default", () => {
    render(<BetterAuthForm />);
    expect(
      screen.queryByRole("link", { name: "Create an account" }),
    ).toBeNull();
  });
  it("registers with bounded inputs and clearly unavailable recovery/social features", async () => {
    const user = userEvent.setup();
    render(<BetterAuthForm signUp />);
    expect(
      screen.getByText(/Password recovery is currently unavailable/),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /Google|GitHub|reset|verify/i }),
    ).toBeNull();
    await user.type(
      screen.getByLabelText("Email address"),
      "synthetic@example.test",
    );
    await user.type(
      screen.getByLabelText("Password"),
      "Synthetic-password-0001",
    );
    await user.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() =>
      expect(auth.signUp).toHaveBeenCalledWith({
        email: "synthetic@example.test",
        password: "Synthetic-password-0001",
        name: "Candidate",
      }),
    );
    expect(auth.replace).toHaveBeenCalledWith("/app/dashboard");
  });
  it("shows a generic failure, keeps the form usable, and never displays raw provider errors", async () => {
    const user = userEvent.setup();
    auth.signIn.mockResolvedValue({
      error: { message: "private driver error" },
    });
    render(<BetterAuthForm />);
    await user.type(
      screen.getByLabelText("Email address"),
      "synthetic@example.test",
    );
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).not.toHaveTextContent(
      "private driver error",
    );
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });
});
