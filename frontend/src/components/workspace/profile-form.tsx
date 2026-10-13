"use client";

import { useRef, useState, type FormEvent } from "react";
import type { Dashboard, ProfileInput } from "@/lib/api/workspace";
import { Button } from "@/components/ui/button";
import {
  FormSection,
  InputField,
  SelectField,
  TextareaField,
} from "@/components/ui/field";
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
  const [saved, setSaved] = useState(Boolean(profile));
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
    const hours = Number(values.get("hours"));
    const minutes = Math.round(hours * 60);
    const yearText = String(values.get("year") ?? "");
    const year = yearText ? Number(yearText) : null;
    const interests = String(values.get("interests") ?? "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    const interviewDate = String(values.get("date") ?? "") || null;
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
    if (
      !Number.isFinite(hours) ||
      minutes < 15 ||
      minutes > 10080 ||
      Math.abs(hours * 60 - minutes) > 0.000001
    )
      validation.hours = "Enter 0.25 to 168 hours, in whole-minute increments.";
    if (
      year !== null &&
      (!Number.isInteger(year) || year < 1900 || year > 2100)
    )
      validation.year = "Enter a year from 1900 to 2100.";
    if (
      interests.length > 20 ||
      interests.some((value) => value.length > 80) ||
      new Set(interests.map((value) => value.toLowerCase())).size !==
        interests.length
    )
      validation.interests =
        "Use up to 20 distinct interests, each 80 characters or fewer.";
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
        expected_id: profile?.id ?? null,
        education: String(values.get("education") ?? "").trim() || null,
        graduation_year: year,
        interests,
        interview_date: interviewDate,
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
        title="Your background (optional)"
        description="Share only what helps you prepare. These details are optional; your interests are not treated as proof of skill."
      >
        <InputField
          label="Education (optional)"
          name="education"
          maxLength={300}
          defaultValue={profile?.education ?? ""}
          hint="A short description is enough. No institution or grades are needed."
          disabled={saving}
        />
        <InputField
          label="Graduation year (optional)"
          name="year"
          type="number"
          min={1900}
          max={2100}
          step={1}
          defaultValue={profile?.graduation_year ?? ""}
          error={errors.year}
          disabled={saving}
        />
        <div className="sm:col-span-2">
          <TextareaField
            label="Technologies / interests (optional)"
            name="interests"
            maxLength={1638}
            rows={2}
            defaultValue={profile?.interests.join(", ") ?? ""}
            hint="Separate your own labels with commas. Up to 20; no skills are inferred."
            error={errors.interests}
            disabled={saving}
          />
        </div>
      </FormSection>
      <FormSection
        title="Make time for practice"
        description="Choose a realistic weekly budget. This is your intention, not a measure of completed practice."
      >
        <InputField
          label="Preparation hours per week"
          name="hours"
          type="number"
          inputMode="numeric"
          required
          min={0.25}
          max={168}
          step="any"
          defaultValue={(profile?.weekly_minutes ?? 240) / 60}
          hint="Choose a realistic budget. 0.5 hours is 30 minutes."
          error={errors.hours}
          disabled={saving}
        />
        <InputField
          label="Interview date (optional)"
          name="date"
          type="date"
          min="1900-01-01"
          max="2100-12-31"
          defaultValue={profile?.interview_date ?? ""}
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
