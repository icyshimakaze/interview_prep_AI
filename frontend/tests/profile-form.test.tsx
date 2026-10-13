import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "@/components/workspace/profile-form";
import { workspaceFixture } from "./workspace-fixture";

describe("preparation profile", () => {
  it("saves trimmed input through the existing revision contract and announces success", async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ProfileForm profile={null} onSave={save} />);
    await user.type(screen.getByLabelText("Target role"), " Backend Engineer ");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(save).toHaveBeenCalledExactlyOnceWith({
      display_name: null,
      target_role: "Backend Engineer",
      experience_band: "entry",
      timezone: "Asia/Kolkata",
      weekly_minutes: 240,
      expected_revision: null,
    });
    expect(screen.getByRole("status")).toHaveTextContent("Profile saved");
    await user.type(screen.getByLabelText("Target role"), " II");
    expect(screen.getByRole("status")).toBeEmptyDOMElement();
  });
  it("associates errors with fields and focuses the first invalid entry", async () => {
    const save = vi.fn();
    const user = userEvent.setup();
    render(<ProfileForm profile={null} onSave={save} />);
    await user.type(screen.getByLabelText("Target role"), "   ");
    await user.clear(screen.getByLabelText("Timezone"));
    await user.type(screen.getByLabelText("Timezone"), "not-a-timezone");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(screen.getByLabelText("Target role")).toHaveFocus();
    expect(screen.getByLabelText("Target role")).toHaveAccessibleDescription(
      "Enter the role you want to prepare for.",
    );
    expect(screen.getByLabelText("Timezone")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(save).not.toHaveBeenCalled();
  });
  it("keeps edits when a stale revision fails, with explicit discard-and-reload recovery", async () => {
    const save = vi
      .fn()
      .mockRejectedValue(
        new Error("Your profile changed in another tab. Reload and try again."),
      );
    const reload = vi.fn();
    const user = userEvent.setup();
    render(
      <ProfileForm
        profile={workspaceFixture.profile}
        onSave={save}
        onReload={reload}
      />,
    );
    await user.clear(screen.getByLabelText("Target role"));
    await user.type(screen.getByLabelText("Target role"), "Platform Engineer");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({ expected_revision: 1 }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "changed in another tab",
    );
    expect(screen.getByLabelText("Target role")).toHaveValue(
      "Platform Engineer",
    );
    expect(screen.getByText(/Reloading discards unsaved edits/)).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Reload saved profile" }),
    );
    expect(reload).toHaveBeenCalledOnce();
  });
  it("blocks duplicate submissions while saving", async () => {
    let resolve: () => void = () => {
      throw new Error("Save was not started");
    };
    const save = vi.fn(
      () =>
        new Promise<void>((done) => {
          resolve = done;
        }),
    );
    const user = userEvent.setup();
    render(<ProfileForm profile={workspaceFixture.profile} onSave={save} />);
    await user.dblClick(screen.getByRole("button", { name: "Save profile" }));
    expect(
      screen.getByRole("button", { name: "Saving profile…" }),
    ).toBeDisabled();
    expect(save).toHaveBeenCalledOnce();
    resolve();
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Profile saved"),
    );
  });
});
