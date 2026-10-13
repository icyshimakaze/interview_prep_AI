"use client";

import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { SelectField, TextareaField } from "@/components/ui/field";
import { ErrorDisplay } from "@/components/ui/states";
import {
  categoryLabels,
  evidenceCategories,
  isEvidenceCategory,
  type Evidence,
  type EvidenceInput,
} from "@/lib/api/resumes";

export function EvidenceForm({
  evidence,
  busy,
  onSave,
  onReload,
}: {
  evidence?: Evidence;
  busy: boolean;
  onSave: (input: EvidenceInput) => Promise<void>;
  onReload: () => Promise<void>;
}) {
  const [claim, setClaim] = useState(
    evidence?.user_correction ?? evidence?.claim ?? "",
  );
  const [category, setCategory] = useState(evidence?.category ?? "other");
  const [review, setReview] = useState(evidence?.review_status ?? "confirmed");
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string>();
  const lock = useRef(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (lock.current || busy) return;
    const invalid = !claim.trim()
      ? "Enter the evidence you want to record."
      : claim.trim().length > 2000
        ? "Keep this entry within 2,000 characters."
        : undefined;
    setFieldError(invalid);
    if (invalid) {
      event.currentTarget.querySelector("textarea")?.focus();
      return;
    }
    lock.current = true;
    setError(null);
    try {
      await onSave({ category, claim: claim.trim(), review_status: review });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Evidence could not be saved.",
      );
    } finally {
      lock.current = false;
    }
  }
  return (
    <form
      className="mt-6 space-y-5"
      noValidate
      onSubmit={(event) => void submit(event)}
      aria-busy={busy}
    >
      <p className="text-sm leading-7 text-muted">
        Record only information you choose to supply. Confirmation records your
        review of the claim; it does not verify competence.
      </p>
      {evidence?.source_excerpt && (
        <div className="border-l-2 border-line pl-4">
          <p className="eyebrow">
            Original PDF excerpt
            {evidence.source_page ? ` · page ${evidence.source_page}` : ""}
          </p>
          <p className="mt-2 text-sm leading-7 break-words whitespace-pre-wrap">
            {evidence.source_excerpt}
          </p>
        </div>
      )}
      <TextareaField
        label="Evidence or correction"
        value={claim}
        onChange={(event) => setClaim(event.target.value)}
        required
        maxLength={2000}
        error={fieldError}
        disabled={busy}
        rows={4}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          label="Category"
          value={category}
          disabled={busy}
          onChange={(event) => {
            if (isEvidenceCategory(event.target.value))
              setCategory(event.target.value);
          }}
        >
          {evidenceCategories.map((item) => (
            <option key={item} value={item}>
              {categoryLabels[item]}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Review status"
          value={review}
          disabled={busy}
          onChange={(event) => {
            const value = event.target.value;
            if (
              value === "proposed" ||
              value === "confirmed" ||
              value === "rejected"
            )
              setReview(value);
          }}
        >
          <option value="proposed">Proposed · needs review</option>
          <option value="confirmed">Confirmed by you</option>
          <option value="rejected">Rejected · exclude from context</option>
        </SelectField>
      </div>
      {error && (
        <>
          <ErrorDisplay title="Evidence could not be saved" message={error} />
          <Button
            variant="outline"
            disabled={busy}
            onClick={() =>
              void onReload().catch((reason: unknown) =>
                setError(
                  reason instanceof Error ? reason.message : "Reload failed.",
                ),
              )
            }
          >
            Discard edits and reload
          </Button>
        </>
      )}
      <Button type="submit" disabled={busy}>
        {busy ? "Saving…" : "Save evidence"}
      </Button>
    </form>
  );
}
