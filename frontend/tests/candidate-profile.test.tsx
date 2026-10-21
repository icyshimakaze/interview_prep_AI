import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "@/components/workspace/profile-form";
import { ProfileDeletion } from "@/components/workspace/profile-deletion";
import { workspaceFixture } from "./workspace-fixture";

describe("optional candidate context", () => {
  it("stores supplied optional fields and converts hours to whole minutes", async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ProfileForm profile={null} onSave={save} />);
    await user.type(screen.getByLabelText("Target role"), "Software Engineer");
    await user.type(
      screen.getByLabelText("Education (optional)"),
      " Computer science ",
    );
    await user.type(
      screen.getByLabelText("Graduation year (optional)"),
      "2027",
    );
    await user.type(
      screen.getByLabelText("Technologies / interests (optional)"),
      " Python, Distributed systems ",
    );
    await user.clear(screen.getByLabelText("Preparation hours per week"));
    await user.type(screen.getByLabelText("Preparation hours per week"), "2.5");
    await user.type(
      screen.getByLabelText("Interview date (optional)"),
      "2027-01-15",
    );
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({
        education: "Computer science",
        graduation_year: 2027,
        interests: ["Python", "Distributed systems"],
        weekly_minutes: 150,
        interview_date: "2027-01-15",
      }),
    );
  });
  it("rejects duplicate supplied labels without inventing alternatives", async () => {
    const save = vi.fn();
    const user = userEvent.setup();
    render(<ProfileForm profile={workspaceFixture.profile} onSave={save} />);
    await user.type(
      screen.getByLabelText("Technologies / interests (optional)"),
      "Python, python",
    );
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(
      screen.getByLabelText("Technologies / interests (optional)"),
    ).toHaveAttribute("aria-invalid", "true");
    expect(save).not.toHaveBeenCalled();
  });
  it("clears optional saved context deliberately while retaining revision and identity", async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    const profile = workspaceFixture.profile;
    if (!profile) throw new Error("Missing profile fixture");
    render(
      <ProfileForm
        profile={{
          ...profile,
          education: "Computer science",
          graduation_year: 2027,
          interests: ["Python"],
          interview_date: "2027-01-15",
        }}
        onSave={save}
      />,
    );
    for (const label of [
      "Education (optional)",
      "Graduation year (optional)",
      "Technologies / interests (optional)",
      "Interview date (optional)",
    ])
      await user.clear(screen.getByLabelText(label));
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_id: profile.id,
        expected_revision: 1,
        education: null,
        graduation_year: null,
        interests: [],
        interview_date: null,
      }),
    );
  });
  it("requires a deletion confirmation and preserves the profile on failure", async () => {
    const remove = vi
      .fn()
      .mockRejectedValueOnce(new Error("Record changed. Reload it."))
      .mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<ProfileDeletion onDelete={remove} disabled={false} />);
    await user.click(screen.getByRole("button", { name: "Delete profile" }));
    expect(remove).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Keep profile" }));
    expect(remove).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Delete profile" }));
    await user.click(
      screen.getByRole("button", { name: "Delete preparation profile" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Record changed",
    );
    await user.click(
      screen.getByRole("button", { name: "Delete preparation profile" }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(remove).toHaveBeenCalledTimes(2);
  });
});
