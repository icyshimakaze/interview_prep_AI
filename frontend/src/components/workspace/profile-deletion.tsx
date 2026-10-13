"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ErrorDisplay } from "@/components/ui/states";

export function ProfileDeletion({
  onDelete,
  onReload,
  disabled,
}: {
  onDelete: () => Promise<void>;
  onReload?: () => void;
  disabled: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await onDelete();
      setOpen(false);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Your profile could not be deleted.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="section-rule">
      <h2 className="section-title">Delete preparation profile</h2>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-muted">
        Remove your preparation preferences and optional background details.
        Your account, target jobs, and preparation history remain.
      </p>
      <Button
        variant="outline"
        className="mt-4 text-danger"
        disabled={disabled}
        onClick={() => {
          setError(null);
          setOpen(true);
        }}
      >
        Delete profile
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Delete your preparation profile?"
        busy={busy}
      >
        <p className="mt-4 text-sm leading-7 text-muted">
          This deletes all profile details, including education and interests.
          This cannot be undone. Your account and other saved work stay
          available.
        </p>
        {error && (
          <>
            <ErrorDisplay message={error} />
            {onReload && (
              <Button variant="outline" onClick={onReload}>
                Reload profile before deleting
              </Button>
            )}
          </>
        )}
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => setOpen(false)}
          >
            Keep profile
          </Button>
          <Button
            variant="danger"
            disabled={busy}
            onClick={() => void remove()}
          >
            {busy ? "Deleting profile…" : "Delete preparation profile"}
          </Button>
        </div>
      </Dialog>
    </section>
  );
}
