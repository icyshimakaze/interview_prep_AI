"use client";
import { useEffect, useState } from "react";
import type { TargetApi } from "@/lib/api/targets";
import {
  WorkspaceError,
  type Target,
  type TargetInput,
  type TargetList,
  type TargetStatus,
} from "@/lib/api/workspace";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { SelectField } from "@/components/ui/field";
import {
  EmptyState,
  ErrorDisplay,
  WorkspaceSkeleton,
} from "@/components/ui/states";
import { Badge, DataTable } from "@/components/ui/table";
import { SectionHeader } from "./section-header";
import { TargetForm } from "./target-form";
import { TargetDetails } from "./target-details";

export function TargetJobsView({ api }: { api: TargetApi }) {
  const [page, setPage] = useState<TargetList | null>(null);
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState<TargetStatus | "all">("all");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [editor, setEditor] = useState<{ target: Target | null } | null>(null);
  const [details, setDetails] = useState<Target | null>(null);
  const [deleting, setDeleting] = useState<Target | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [inUse, setInUse] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void api
      .list(offset, status, controller.signal)
      .then((result) => {
        if (active) setPage(result);
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Your jobs could not load.",
          );
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, offset, status, attempt]);
  function refresh() {
    setPage(null);
    setError(null);
    setAttempt((value) => value + 1);
  }
  async function save(input: TargetInput) {
    setBusy(true);
    try {
      await api.save(input, editor?.target ?? null);
      setEditor(null);
      setNotice("Target job saved.");
      refresh();
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!deleting) return;
    setBusy(true);
    setDeleteError(null);
    setInUse(false);
    try {
      await api.remove(deleting);
      setDeleting(null);
      setNotice("Target job deleted.");
      if (offset > 0 && page?.items.length === 1) {
        setOffset(Math.max(0, offset - 20));
        setPage(null);
      } else refresh();
    } catch (reason: unknown) {
      setDeleteError(
        reason instanceof Error
          ? reason.message
          : "The job could not be deleted.",
      );
      setInUse(
        reason instanceof WorkspaceError && reason.code === "target_in_use",
      );
    } finally {
      setBusy(false);
    }
  }
  const openEditor = (target: Target | null) => {
    setNotice("");
    setEditor({ target });
  };
  const editingTarget = editor?.target;
  return (
    <>
      <SectionHeader
        title="Target Job"
        eyebrow="Set the context"
        description="Save the roles you are considering and keep their supplied requirements and your notes together."
        action={
          <Button onClick={() => openEditor(null)}>Add target job</Button>
        }
      />
      <p role="status" className="mb-4 text-sm text-accent">
        {notice}
      </p>
      <div className="mb-6 max-w-xs">
        <SelectField
          label="Filter by status"
          value={status}
          onChange={(event) => {
            const value = event.target.value;
            if (
              value === "all" ||
              value === "saved" ||
              value === "applied" ||
              value === "interviewing" ||
              value === "archived"
            ) {
              setStatus(value);
              setOffset(0);
              setPage(null);
              setError(null);
            }
          }}
        >
          <option value="all">All jobs</option>
          <option value="saved">Saved</option>
          <option value="applied">Applied</option>
          <option value="interviewing">Interviewing</option>
          <option value="archived">Archived</option>
        </SelectField>
      </div>
      {error ? (
        <ErrorDisplay
          title="Target jobs could not load"
          message={error}
          onRetry={refresh}
        />
      ) : !page ? (
        <WorkspaceSkeleton label="Loading your target jobs…" />
      ) : page.items.length ? (
        <>
          <DataTable
            caption="Your target jobs"
            headers={["Job", "Priority", "Status", "Actions"]}
          >
            {page.items.map((target) => (
              <tr key={target.id}>
                <td className="min-w-44">
                  <button
                    className="text-left font-semibold text-accent underline underline-offset-4"
                    onClick={() => setDetails(target)}
                  >
                    {target.title}
                  </button>
                  {target.organization && (
                    <p className="mt-1 text-xs text-muted">
                      {target.organization}
                    </p>
                  )}
                </td>
                <td>
                  <Badge
                    tone={target.priority === "high" ? "amber" : "neutral"}
                  >
                    {target.priority}
                  </Badge>
                </td>
                <td>
                  <Badge>{target.status}</Badge>
                </td>
                <td>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      onClick={() => openEditor(target)}
                      aria-label={`Edit ${target.title}`}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setDeleteError(null);
                        setInUse(false);
                        setDeleting(target);
                      }}
                      aria-label={`Delete ${target.title}`}
                    >
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </DataTable>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
            <p className="text-xs text-muted">
              {offset + 1}–{offset + page.items.length} of {page.total} jobs
            </p>
            <nav aria-label="Target job pages" className="flex gap-3">
              <Button
                variant="outline"
                disabled={offset === 0}
                onClick={() => {
                  setOffset((value) => Math.max(0, value - 20));
                  setPage(null);
                }}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={offset + page.items.length >= page.total}
                onClick={() => {
                  setOffset((value) => value + 20);
                  setPage(null);
                }}
              >
                Next
              </Button>
            </nav>
          </div>
        </>
      ) : (
        <EmptyState
          icon="target"
          title={
            status === "all"
              ? "Start with a job you are considering."
              : "No jobs in this view."
          }
          description={
            status === "all"
              ? "Add a job title and description. Company, source link, and personal preparation notes are optional. Nothing is inferred from the description."
              : "Try another status, or add a job to your preparation context."
          }
          action={
            <Button variant="outline" onClick={() => openEditor(null)}>
              Add your first target job
            </Button>
          }
        />
      )}
      <Dialog
        open={editor !== null}
        onClose={() => setEditor(null)}
        title={editor?.target ? "Edit target job" : "Add target job"}
        busy={busy}
      >
        {editor && (
          <TargetForm
            key={
              editor.target
                ? `${editor.target.id}-${editor.target.revision}`
                : "new"
            }
            target={editor.target}
            onSave={save}
            onCancel={() => setEditor(null)}
            onReload={
              editingTarget
                ? async () => {
                    setBusy(true);
                    try {
                      const target = await api.read(editingTarget.id);
                      setEditor({ target });
                      refresh();
                    } finally {
                      setBusy(false);
                    }
                  }
                : undefined
            }
          />
        )}
      </Dialog>
      <Dialog
        open={details !== null}
        onClose={() => setDetails(null)}
        title="Target job details"
      >
        {details && <TargetDetails target={details} />}
      </Dialog>
      <Dialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete this target job?"
        busy={busy}
      >
        <p className="mt-4 text-sm leading-7 text-muted">
          This removes “{deleting?.title}”, its notes and description versions.
          Jobs referenced by preparation history must be archived instead.
        </p>
        {deleteError && (
          <>
            <ErrorDisplay message={deleteError} />
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => {
                if (!deleting) return;
                setBusy(true);
                void api
                  .read(deleting.id)
                  .then((target) => {
                    setDeleting(target);
                    setDeleteError(null);
                    refresh();
                  })
                  .catch((reason: unknown) =>
                    setDeleteError(
                      reason instanceof Error
                        ? reason.message
                        : "The job could not reload.",
                    ),
                  )
                  .finally(() => setBusy(false));
              }}
            >
              Reload job before deleting
            </Button>
          </>
        )}
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => setDeleting(null)}
          >
            Keep job
          </Button>
          {inUse && (
            <Button
              variant="outline"
              onClick={() => {
                const target = deleting;
                setDeleting(null);
                if (target) openEditor(target);
              }}
            >
              Edit status to archive
            </Button>
          )}
          <Button
            variant="danger"
            disabled={busy}
            onClick={() => void remove()}
          >
            {busy ? "Deleting job…" : "Delete target job"}
          </Button>
        </div>
      </Dialog>
    </>
  );
}
