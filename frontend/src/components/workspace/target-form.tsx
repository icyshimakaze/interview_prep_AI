"use client";
import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { InputField, SelectField, TextareaField } from "@/components/ui/field";
import { ErrorDisplay } from "@/components/ui/states";
import {
  validSourceUrl,
  type Target,
  type TargetInput,
} from "@/lib/api/workspace";

export function TargetForm({
  target,
  onSave,
  onCancel,
  onReload,
}: {
  target: Target | null;
  onSave: (input: TargetInput) => Promise<void>;
  onCancel: () => void;
  onReload?: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const locked = useRef(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked.current) return;
    const form = event.currentTarget,
      values = new FormData(form);
    const text = (key: string) => String(values.get(key) ?? "").trim();
    const priority = text("priority"),
      status = text("status");
    const validation: Record<string, string> = {};
    if (!text("title")) validation.title = "Enter a job title.";
    if (!text("description"))
      validation.description = "Paste or write the job description.";
    if (text("source") && !validSourceUrl(text("source")))
      validation.source = "Use an HTTP(S) link without sign-in credentials.";
    if (priority !== "low" && priority !== "normal" && priority !== "high")
      validation.priority = "Choose a priority.";
    if (
      status !== "saved" &&
      status !== "applied" &&
      status !== "interviewing" &&
      status !== "archived"
    )
      validation.status = "Choose a status.";
    setErrors(validation);
    setError(null);
    if (
      Object.keys(validation).length ||
      (priority !== "low" && priority !== "normal" && priority !== "high") ||
      (status !== "saved" &&
        status !== "applied" &&
        status !== "interviewing" &&
        status !== "archived")
    ) {
      const first = form.elements.namedItem(
        Object.keys(validation)[0] ?? "title",
      );
      if (first instanceof HTMLElement) first.focus();
      return;
    }
    locked.current = true;
    setBusy(true);
    try {
      await onSave({
        title: text("title"),
        organization: text("company") || null,
        description: text("description"),
        source_url: text("source") || null,
        notes: text("notes") || null,
        priority,
        status,
      });
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "This job could not be saved. Your entries are still here.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <form onSubmit={(event) => void submit(event)} className="mt-5 space-y-5">
      <p className="text-sm leading-6 text-muted">
        Only the title and description are required. Paste job information,
        without confidential or personal details.
      </p>
      <div className="grid gap-5 sm:grid-cols-2">
        <InputField
          label="Job title"
          name="title"
          required
          maxLength={200}
          defaultValue={target?.title ?? ""}
          error={errors.title}
          disabled={busy}
        />
        <InputField
          label="Company (optional)"
          name="company"
          maxLength={200}
          defaultValue={target?.organization ?? ""}
          disabled={busy}
        />
      </div>
      <TextareaField
        label="Job description"
        name="description"
        required
        maxLength={30000}
        rows={7}
        defaultValue={target?.description ?? ""}
        error={errors.description}
        disabled={busy}
        hint="Up to 30,000 characters. Saved as supplied text; no skills are inferred."
      />
      <InputField
        label="Source URL (optional)"
        name="source"
        type="url"
        maxLength={2000}
        defaultValue={target?.source_url ?? ""}
        error={errors.source}
        disabled={busy}
        hint="The application stores this link and does not visit or import it."
      />
      <TextareaField
        label="Notes (optional)"
        name="notes"
        maxLength={5000}
        rows={3}
        defaultValue={target?.notes ?? ""}
        disabled={busy}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          label="Priority"
          name="priority"
          defaultValue={target?.priority ?? "normal"}
          error={errors.priority}
          disabled={busy}
        >
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
        </SelectField>
        <SelectField
          label="Status"
          name="status"
          defaultValue={target?.status ?? "saved"}
          error={errors.status}
          disabled={busy}
        >
          <option value="saved">Saved</option>
          <option value="applied">Applied</option>
          <option value="interviewing">Interviewing</option>
          <option value="archived">Archived</option>
        </SelectField>
      </div>
      {error && (
        <>
          <ErrorDisplay title="Job could not be saved" message={error} />
          {onReload && (
            <>
              <p className="text-xs text-muted">
                Reloading replaces this form with the saved job and discards
                unsaved entries.
              </p>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  void onReload()
                    .catch((reason: unknown) =>
                      setError(
                        reason instanceof Error
                          ? reason.message
                          : "The latest job could not load.",
                      ),
                    )
                    .finally(() => setBusy(false));
                }}
              >
                Reload saved job
              </Button>
            </>
          )}
        </>
      )}
      <div className="flex flex-wrap justify-end gap-3 border-t border-line pt-5">
        <Button variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? "Saving job…" : target ? "Save changes" : "Save job"}
        </Button>
      </div>
    </form>
  );
}
