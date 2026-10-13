"use client";

import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { InputField } from "@/components/ui/field";
import { ErrorDisplay } from "@/components/ui/states";
import { validateResumeFile } from "@/lib/api/resumes";

export function ResumeUpload({
  busy,
  onUpload,
}: {
  busy: boolean;
  onUpload: (file: File) => Promise<void>;
}) {
  const [error, setError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string>();
  const lock = useRef(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (lock.current || busy) return;
    const form = event.currentTarget;
    const input = form.elements.namedItem("resume");
    const file =
      input instanceof HTMLInputElement ? input.files?.[0] : undefined;
    const invalid =
      !(file instanceof File) || !file.size
        ? "Choose a PDF to upload."
        : validateResumeFile(file);
    setFileError(invalid ?? undefined);
    if (invalid || !(file instanceof File)) {
      form.querySelector("input")?.focus();
      return;
    }
    lock.current = true;
    setError(null);
    try {
      await onUpload(file);
      form.reset();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Upload failed. Please try again.",
      );
    } finally {
      lock.current = false;
    }
  }
  return (
    <section className="border-y border-line bg-surface p-6 sm:p-8">
      <h2 className="section-title">Upload a resume</h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">
        Choose a PDF with selectable text, up to 5 MiB and 20 pages. Remove
        contact details or anything you do not want to share. The raw PDF is
        discarded after parsing; selected evidence excerpts stay until you
        delete them.
      </p>
      <form
        className="mt-6 space-y-5"
        onSubmit={(event) => void submit(event)}
        noValidate
        aria-busy={busy}
      >
        <InputField
          type="file"
          name="resume"
          label="PDF resume"
          accept=".pdf,application/pdf"
          required
          disabled={busy}
          error={fileError}
          hint="Encrypted PDFs and image-only scans cannot be read. No OCR or AI service is used."
        />
        {error && <ErrorDisplay title="Resume upload failed" message={error} />}
        <Button type="submit" disabled={busy}>
          {busy ? "Uploading and parsing…" : "Upload PDF"}
        </Button>
      </form>
    </section>
  );
}
