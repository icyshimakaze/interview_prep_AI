"use client";

import { useRef, useState, type FormEvent } from "react";
import type { Dashboard, ProfileInput } from "@/lib/api/workspace";
import { Button } from "@/components/ui/button";
import { FormSection, InputField, SelectField } from "@/components/ui/field";
import { ErrorDisplay } from "@/components/ui/states";

export function ProfileForm({
  profile,
  onSave,
  onReload,
}: {
  profile: Dashboard["profile"];
  onSave: (input: ProfileInput) => Promise<void>;
  onReload?: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const locked = useRef(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked.current) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    const role = String(values.get("role") ?? "").trim();
    const timezone = String(values.get("timezone") ?? "").trim();
    const minutes = Number(values.get("minutes"));
    const experience = values.get("experience");
    const validation: Record<string, string> = {};
    if (!role) validation.role = "Enter the role you want to prepare for.";
    try {
      if (!timezone) throw new Error();
      new Intl.DateTimeFormat("en", { timeZone: timezone });
    } catch {
      validation.timezone =
        "Enter a valid timezone, such as Asia/Kolkata or Europe/London.";
    }
    if (!Number.isInteger(minutes) || minutes < 15 || minutes > 10080)
      validation.minutes = "Enter a whole number from 15 to 10,080.";
    if (
      experience !== "student" &&
      experience !== "entry" &&
      experience !== "mid" &&
      experience !== "senior"
    )
      validation.experience = "Choose an experience level.";
    setErrors(validation);
    setError(null);
    setSaved(false);
    if (
      Object.keys(validation).length ||
      (experience !== "student" &&
        experience !== "entry" &&
        experience !== "mid" &&
        experience !== "senior")
    ) {
      const first = form.elements.namedItem(
        Object.keys(validation)[0] ?? "role",
      );
      if (first instanceof HTMLElement) first.focus();
      return;
    }
    locked.current = true;
    setSaving(true);
    try {
      await onSave({
        display_name: String(values.get("name") ?? "").trim() || null,
        target_role: role,
        experience_band: experience,
        timezone,
        weekly_minutes: minutes,
        expected_revision: profile?.revision ?? null,
      });
      setSaved(true);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Your profile could not be saved. Please try again.",
      );
    } finally {
      setSaving(false);
      locked.current = false;
    }
  }
  return (
    <form
      onSubmit={(event) => void submit(event)}
      onChange={() => setSaved(false)}
    >
      <FormSection
        title="About your preparation"
        description="A little context helps give your preparation a direction. Your display name is optional."
      >
        <InputField
          label="Display name (optional)"
          name="name"
          autoComplete="nickname"
          maxLength={150}
          defaultValue={profile?.display_name ?? ""}
          disabled={saving}
        />
        <InputField
          label="Target role"
          name="role"
          placeholder="e.g. Backend Engineer"
          required
          maxLength={200}
          defaultValue={profile?.target_role ?? ""}
          error={errors.role}
          disabled={saving}
        />
        <SelectField
          label="Experience level"
          name="experience"
          defaultValue={profile?.experience_band ?? "entry"}
          error={errors.experience}
          disabled={saving}
        >
          <option value="student">Student</option>
          <option value="entry">Entry level</option>
          <option value="mid">Mid level</option>
          <option value="senior">Senior</option>
        </SelectField>
      </FormSection>
      <FormSection
        title="Make time for practice"
        description="Choose a realistic weekly budget. This is your intention, not a measure of completed practice."
      >
        <InputField
          label="Study minutes per week"
          name="minutes"
          type="number"
          inputMode="numeric"
          required
          min={15}
          max={10080}
          step={1}
          defaultValue={profile?.weekly_minutes ?? 240}
          hint="For example, 240 minutes is 4 hours a week."
          error={errors.minutes}
          disabled={saving}
        />
        <InputField
          label="Timezone"
          name="timezone"
          required
          maxLength={100}
          defaultValue={profile?.timezone ?? "Asia/Kolkata"}
          hint="Use a region/city, such as Asia/Kolkata."
          error={errors.timezone}
          disabled={saving}
        />
      </FormSection>
      {error && (
        <>
          <ErrorDisplay title="Profile could not be saved" message={error} />
          {onReload && (
            <Button variant="outline" onClick={onReload} className="mb-5">
              Reload saved profile
            </Button>
          )}
          <p className="mb-5 text-xs text-muted">
            Your entries are still in this form. Reloading discards unsaved
            edits.
          </p>
        </>
      )}
      <div className="flex flex-wrap items-center gap-5 border-t border-line py-6">
        <Button type="submit" disabled={saving}>
          {saving ? "Saving profile…" : "Save profile"}
        </Button>
        <p role="status" className="text-sm text-accent">
          {saved
            ? "Profile saved. Your preparation direction is up to date."
            : saving
              ? "Saving your changes…"
              : ""}
        </p>
      </div>
    </form>
  );
}
