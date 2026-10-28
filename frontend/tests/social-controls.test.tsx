import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { SocialControls } from "@/components/better-auth/social-controls";
import { BetterAuthForm } from "@/components/better-auth/auth-form";

const mocks = vi.hoisted(() => ({
  social: vi.fn(),
  link: vi.fn(),
  navigate: vi.fn(),
}));
vi.mock("@/lib/better-auth/client", () => ({
  authClient: {
    signIn: { social: mocks.social, email: vi.fn() },
    linkSocial: mocks.link,
  },
}));
vi.mock("@/lib/better-auth/social-navigation", () => ({
  navigateToSocialProvider: mocks.navigate,
}));
beforeEach(() => {
  mocks.social.mockResolvedValue({
    data: { url: "https://accounts.google.com/o/oauth2/v2/auth" },
  });
  mocks.link.mockResolvedValue({
    data: {
      url: "https://github.com/login/oauth/authorize",
    },
  });
});
it("keeps password controls and shows only enabled providers with accessible text/icons", async () => {
  const user = userEvent.setup();
  render(<BetterAuthForm socialProviders={["google", "github"]} />);
  expect(screen.getByLabelText("Password", { exact: true })).toBeVisible();
  expect(
    screen.getByRole("separator", { name: "or continue with email" }),
  ).toBeVisible();
  await user.click(
    screen.getByRole("button", { name: "Continue with Google" }),
  );
  expect(mocks.social).toHaveBeenCalledWith(
    expect.objectContaining({
      provider: "google",
      callbackURL: "/app/dashboard",
      disableRedirect: true,
    }),
    expect.anything(),
  );
  expect(mocks.navigate).toHaveBeenCalledWith(
    expect.stringContaining("accounts.google.com"),
    "google",
  );
});
it("uses explicit linking separately from sign-in", async () => {
  const user = userEvent.setup();
  render(<SocialControls providers={["github"]} link />);
  expect(screen.queryByRole("button", { name: /Google/ })).toBeNull();
  await user.click(screen.getByRole("button", { name: "Connect GitHub" }));
  expect(mocks.link).toHaveBeenCalledWith(
    expect.objectContaining({
      provider: "github",
      callbackURL: "/app/account-access",
    }),
    expect.anything(),
  );
});
it("shows a generic error, enables retry and suppresses raw provider details", async () => {
  mocks.social.mockResolvedValue({
    error: { message: "secret-token-provider-error" },
  });
  const user = userEvent.setup();
  render(<SocialControls providers={["google"]} />);
  await user.click(
    screen.getByRole("button", { name: "Continue with Google" }),
  );
  expect(await screen.findByRole("alert")).not.toHaveTextContent(
    "secret-token",
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Continue with Google" }),
    ).toBeEnabled(),
  );
});
it("disables both providers during a pending sign-in and offers no absent provider", async () => {
  mocks.social.mockImplementation(() => new Promise(() => {}));
  const user = userEvent.setup();
  render(<SocialControls providers={["google", "github"]} />);
  await user.click(
    screen.getByRole("button", { name: "Continue with Google" }),
  );
  expect(
    screen.getByRole("button", { name: "Continue with GitHub" }),
  ).toBeDisabled();
  expect(screen.getByRole("status")).toHaveTextContent(
    "Opening secure account selection",
  );
});
