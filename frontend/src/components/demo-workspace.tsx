"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { WorkspaceShell } from "@/components/workspace/workspace-shell";
import { WorkspaceContext } from "@/components/workspace/workspace-context";
import { createSkillApi } from "@/lib/api/skills";
import { createQuestionApi } from "@/lib/api/questions";
import { createAssessmentApi } from "@/lib/api/assessments";
import { createInterviewApi } from "@/lib/api/interviews";
import {
  csrfToken,
  enterDemo,
  parseDashboard,
  workspaceRequest,
  type Dashboard,
} from "@/lib/api/workspace";

const skillApi = createSkillApi(workspaceRequest, "demo");
const questionApi = createQuestionApi(workspaceRequest, "demo");
const assessmentApi = createAssessmentApi(workspaceRequest, "demo");
const interviewApi = createInterviewApi(workspaceRequest, "demo");

export function DemoWorkspace({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmExit, setConfirmExit] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    void enterDemo()
      .then((result) => {
        if (active) setData(result);
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "The demo could not start.",
          );
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  async function complete(id: string) {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await workspaceRequest(
        `/api/v1/demo/roadmap-items/${encodeURIComponent(id)}/complete`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken(),
          },
          body: "{}",
        },
      );
      const result = parseDashboard(
        await (await workspaceRequest("/api/v1/demo/dashboard")).json(),
      );
      if (result.mode !== "demo")
        throw new Error("The demo workspace response is invalid.");
      setData(result);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The task could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function leave() {
    setBusy(true);
    setDeleteError(null);
    try {
      await workspaceRequest("/api/v1/demo/session", {
        method: "DELETE",
        headers: { "X-CSRF-Token": csrfToken() },
      });
      setData(null);
      setConfirmExit(false);
      router.replace("/");
      router.refresh();
    } catch (reason: unknown) {
      setDeleteError(
        reason instanceof Error
          ? reason.message
          : "The demo could not be closed.",
      );
      setBusy(false);
    }
  }
  async function restart() {
    setBusy(true);
    setError(null);
    try {
      await workspaceRequest("/api/v1/demo/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken(),
        },
        body: "{}",
      });
      setData(await enterDemo());
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The demo could not restart.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <WorkspaceShell
      mode="demo"
      onLeave={
        data
          ? () => {
              setDeleteError(null);
              setConfirmExit(true);
            }
          : undefined
      }
      busy={busy}
    >
      {error && (
        <ErrorDisplay
          title={
            data
              ? "Your change could not be confirmed"
              : "The demo could not load"
          }
          message={error}
          onRetry={
            data
              ? undefined
              : () => {
                  setError(null);
                  setAttempt((value) => value + 1);
                }
          }
          busy={busy}
        />
      )}
      {data ? (
        <WorkspaceContext
          value={{
            data,
            busy,
            skillApi,
            questionApi,
            assessmentApi,
            interviewApi,
            onComplete: (id) => void complete(id),
          }}
        >
          {children}
        </WorkspaceContext>
      ) : (
        !error && (
          <WorkspaceSkeleton label="Preparing your isolated fictional workspace…" />
        )
      )}
      {error && !data && (
        <Button
          variant="outline"
          disabled={busy}
          onClick={() => void restart()}
        >
          Start a fresh demo
        </Button>
      )}
      <Dialog
        open={confirmExit}
        onClose={() => setConfirmExit(false)}
        title="Delete this demo workspace?"
        busy={busy}
      >
        <p className="mt-4 text-sm leading-7 text-muted">
          This removes your fictional profile, sample history, and any task
          changes in this demo. Your real account is separate. This cannot be
          undone.
        </p>
        {deleteError && <ErrorDisplay message={deleteError} />}
        <div className="mt-7 flex flex-wrap justify-end gap-3">
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => setConfirmExit(false)}
          >
            Keep exploring
          </Button>
          <Button variant="danger" disabled={busy} onClick={() => void leave()}>
            {busy ? "Deleting demo…" : "Delete demo and exit"}
          </Button>
        </div>
      </Dialog>
    </WorkspaceShell>
  );
}
