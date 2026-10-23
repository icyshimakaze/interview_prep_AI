"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import {
  EmptyState,
  ErrorDisplay,
  WorkspaceSkeleton,
} from "@/components/ui/states";
import type {
  Evidence,
  EvidenceInput,
  Resume,
  ResumeApi,
} from "@/lib/api/resumes";
import { ResumeUpload } from "./resume-upload";
import { ResumeEvidence } from "./resume-evidence";
import { EvidenceForm } from "./evidence-form";
import { AIReview } from "./ai-review";

type Editor = { resume: Resume; evidence?: Evidence };

export function ResumeView({ api }: { api: ResumeApi }) {
  const [items, setItems] = useState<Resume[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [editor, setEditor] = useState<Editor | null>(null);
  const [deleting, setDeleting] = useState<Editor | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const lock = useRef(false);
  const resume = items.find((item) => item.id === selected) ?? items[0];
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    void api
      .list(controller.signal)
      .then((result) => {
        if (active) {
          setItems(result);
          setLoading(false);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Resumes could not be loaded.",
          );
          setLoading(false);
        }
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, attempt]);
  function replace(result: Resume) {
    setItems((current) => [
      result,
      ...current.filter((item) => item.id !== result.id),
    ]);
    setSelected(result.id);
  }
  async function upload(file: File) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setNotice(null);
    try {
      replace(await api.upload(file));
      setNotice("Resume parsed. Review the proposed evidence below.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function save(input: EvidenceInput) {
    if (!editor || lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      replace(await api.saveEvidence(editor.resume, input, editor.evidence));
      setEditor(null);
      setNotice("Evidence saved.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function reloadEditor() {
    if (!editor || lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      const latest = await api.read(editor.resume.id);
      replace(latest);
      const evidence = editor.evidence
        ? latest.evidence.find((item) => item.id === editor.evidence?.id)
        : undefined;
      if (editor.evidence && !evidence) {
        setEditor(null);
        setNotice("This evidence entry has been deleted.");
      } else setEditor({ resume: latest, evidence });
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function remove() {
    if (!deleting || lock.current) return;
    lock.current = true;
    setBusy(true);
    setDeleteError(null);
    try {
      if (deleting.evidence) {
        replace(await api.removeEvidence(deleting.resume, deleting.evidence));
        setNotice("Evidence entry deleted.");
      } else {
        await api.remove(deleting.resume);
        setItems((current) =>
          current.filter((item) => item.id !== deleting.resume.id),
        );
        setSelected(null);
        setNotice("Resume and all its evidence deleted.");
      }
      setDeleting(null);
    } catch (reason) {
      setDeleteError(
        reason instanceof Error
          ? reason.message
          : "Deletion failed. Please try again.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function reloadDeletion() {
    if (!deleting || lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      const latest = await api.read(deleting.resume.id);
      replace(latest);
      const evidence = deleting.evidence
        ? latest.evidence.find((item) => item.id === deleting.evidence?.id)
        : undefined;
      if (deleting.evidence && !evidence) {
        setDeleting(null);
        setNotice("This evidence entry has already been deleted.");
      } else setDeleting({ resume: latest, evidence });
      setDeleteError(null);
    } catch (reason) {
      setDeleteError(
        reason instanceof Error ? reason.message : "Reload failed.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Your candidate evidence</p>
          <h1 className="page-title">Resume</h1>
          <p className="page-description">
            Bring your experience into view, then check every claim.
          </p>
        </div>
      </header>
      {loading ? (
        <WorkspaceSkeleton label="Loading your resumes…" />
      ) : error ? (
        <ErrorDisplay
          title="Resumes could not be loaded"
          message={error}
          onRetry={() => {
            setLoading(true);
            setError(null);
            setAttempt((value) => value + 1);
          }}
        />
      ) : (
        <>
          <ResumeUpload busy={busy} onUpload={upload} />
          <p className="mt-4 min-h-6 text-sm text-accent" role="status">
            {notice}
          </p>
          {!items.length ? (
            <div className="mt-6">
              <EmptyState
                icon="resume"
                title="Your experience starts with your evidence."
                description="Upload a PDF to find explicit mentions, or remove private details before uploading. You will review and correct the results."
                note="No evidence detected never means the candidate does not know something."
              />
            </div>
          ) : (
            <>
              <nav
                aria-label="Saved resumes"
                className="mt-8 flex flex-wrap gap-3"
              >
                {items.map((item) => (
                  <Button
                    key={item.id}
                    variant={item.id === resume?.id ? "default" : "outline"}
                    disabled={busy}
                    aria-pressed={item.id === resume?.id}
                    onClick={() => setSelected(item.id)}
                    className="max-w-full break-all"
                  >
                    {item.label}
                  </Button>
                ))}
              </nav>
              {resume && (
                <section className="section-rule">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h2 className="section-title break-all">
                        {resume.label}
                      </h2>
                      <p className="mt-2 text-xs text-muted">
                        {resume.page_count
                          ? `${resume.page_count} ${resume.page_count === 1 ? "page" : "pages"} · `
                          : ""}
                        Raw PDF discarded · evidence is editable
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={() => {
                        setDeleting({ resume });
                        setDeleteError(null);
                      }}
                    >
                      Delete resume
                    </Button>
                  </div>
                  <ResumeEvidence
                    resume={resume}
                    busy={busy}
                    onEdit={(evidence) => setEditor({ resume, evidence })}
                    onDelete={(evidence) => {
                      setDeleting({ resume, evidence });
                      setDeleteError(null);
                    }}
                  />
                  {api.ai && (
                    <>
                      <p className="mt-5 text-sm text-muted">
                        Optional review covers retained claims and excerpts
                        only. The raw PDF has been discarded.
                      </p>
                      <AIReview
                        key={`${resume.id}-${resume.revision}`}
                        api={api.ai}
                        resource={`resumes/${encodeURIComponent(resume.id)}`}
                        label="Review resume evidence"
                      />
                    </>
                  )}
                  <Button
                    className="mt-6"
                    variant="outline"
                    disabled={busy || resume.evidence.length >= 100}
                    onClick={() => setEditor({ resume })}
                  >
                    Add your own evidence
                  </Button>
                </section>
              )}
            </>
          )}
        </>
      )}
      <Dialog
        open={Boolean(editor)}
        onClose={() => setEditor(null)}
        title={
          editor?.evidence
            ? "Review candidate evidence"
            : "Add candidate evidence"
        }
        busy={busy}
      >
        {editor && (
          <EvidenceForm
            key={`${editor.resume.id}-${editor.resume.revision}-${editor.evidence?.id ?? "new"}`}
            evidence={editor.evidence}
            busy={busy}
            onSave={save}
            onReload={reloadEditor}
          />
        )}
      </Dialog>
      <Dialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        title={
          deleting?.evidence ? "Delete evidence entry?" : "Delete this resume?"
        }
        busy={busy}
      >
        <p className="mt-5 text-sm leading-7 text-muted">
          {deleting?.evidence
            ? "This removes the selected claim and its retained excerpt. You can add information again later."
            : "This permanently removes the resume record, all versions, and all retained evidence excerpts and corrections. Your profile and target jobs are preserved."}
        </p>
        {deleteError && (
          <div className="mt-5">
            <ErrorDisplay
              title="Deletion could not complete"
              message={deleteError}
            />
            <Button
              className="mt-3"
              variant="outline"
              disabled={busy}
              onClick={() => void reloadDeletion()}
            >
              Reload latest record
            </Button>
          </div>
        )}
        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            variant="danger"
            disabled={busy}
            onClick={() => void remove()}
          >
            {busy
              ? "Deleting…"
              : deleting?.evidence
                ? "Delete evidence entry"
                : "Confirm resume deletion"}
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => setDeleting(null)}
          >
            Keep it
          </Button>
        </div>
      </Dialog>
    </>
  );
}
