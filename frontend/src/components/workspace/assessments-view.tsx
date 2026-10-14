"use client";

import { useEffect, useRef, useState } from "react";
import type {
  Assessment,
  AssessmentApi,
  AssessmentConfig,
  AssessmentOptions,
  AssessmentPage,
} from "@/lib/api/assessments";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { DataTable } from "@/components/ui/table";
import { SectionHeader } from "./section-header";
import { AssessmentConfigure } from "./assessment-configure";
import { AssessmentAttemptView } from "./assessment-attempt";
import { displayDate } from "./history-view";

export function AssessmentsWorkspace({ api }: { api: AssessmentApi }) {
  const [offset, setOffset] = useState(0),
    [refresh, setRefresh] = useState(0);
  const [state, setState] = useState<{
    options: AssessmentOptions;
    history: AssessmentPage;
    offset: number;
    refresh: number;
  } | null>(null);
  const [selected, setSelected] = useState<Assessment | null>(null),
    [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const startKey = useRef<{ signature: string; key: string } | null>(null),
    lock = useRef(false);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void Promise.all([
      api.options(controller.signal),
      api.history(offset, controller.signal),
    ])
      .then(([options, history]) => {
        if (active) {
          setState({ options, history, offset, refresh });
          setError(null);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Assessments could not load.",
          );
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, offset, refresh]);
  async function perform(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Assessment request failed. Try again.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  function start(config: AssessmentConfig) {
    void perform(async () => {
      const signature = JSON.stringify(config);
      if (startKey.current?.signature !== signature)
        startKey.current = { signature, key: crypto.randomUUID() };
      setSelected(
        await api.start({ ...config, submission_key: startKey.current.key }),
      );
      startKey.current = null;
    });
  }
  const current =
    state?.offset === offset && state.refresh === refresh ? state : null;
  return (
    <>
      <SectionHeader
        title="Assessments"
        eyebrow="Evidence from your responses"
        description="Answer real questions, save your work, and review objective results separately from simulated conceptual feedback."
      />
      {selected ? (
        <AssessmentAttemptView
          key={selected.id}
          initial={selected}
          api={api}
          onBack={() => {
            setSelected(null);
            setRefresh((v) => v + 1);
          }}
        />
      ) : (
        <>
          {error && (
            <div className="mb-6">
              <ErrorDisplay
                message={error}
                busy={busy}
                onRetry={() => setRefresh((v) => v + 1)}
              />
            </div>
          )}
          {!current && !error && (
            <WorkspaceSkeleton label="Loading assessments…" />
          )}
          {current && (
            <>
              <AssessmentConfigure
                options={current.options}
                busy={busy}
                onStart={start}
              />
              <h2 className="section-title mb-3">Attempt history</h2>
              <p className="mb-5 text-sm leading-6 text-muted">
                Resume unfinished work or review a completed attempt. Questions
                and submitted responses remain attached to their original
                versions.
              </p>
              {!current.history.total ? (
                <p className="rounded-xl border border-line p-6 text-sm">
                  No attempts yet. Configure your first assessment above.
                </p>
              ) : (
                <DataTable
                  caption="Assessment history"
                  headers={[
                    "Assessment",
                    "State",
                    "Saved responses",
                    "Started (UTC)",
                    "Action",
                  ]}
                >
                  {current.history.items.map((a) => (
                    <tr key={a.id}>
                      <td className="min-w-40">
                        {a.title}
                        {a.simulated && (
                          <span className="mt-1 block text-xs text-muted">
                            Includes simulation
                          </span>
                        )}
                      </td>
                      <td>{a.status.replaceAll("_", " ")}</td>
                      <td>
                        {a.answered} of {a.question_count}
                      </td>
                      <td className="whitespace-nowrap">
                        {displayDate(a.started_at)}
                      </td>
                      <td>
                        <Button
                          variant="outline"
                          disabled={busy}
                          aria-label={`${a.status === "in_progress" ? "Resume" : "Review"} ${a.title}`}
                          onClick={() =>
                            void perform(async () => {
                              setSelected(await api.read(a.id));
                            })
                          }
                        >
                          {a.status === "in_progress" ? "Resume" : "Review"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </DataTable>
              )}
              <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
                <p className="text-sm text-muted">
                  {current.history.total} saved attempts
                </p>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    disabled={busy || offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 10))}
                  >
                    Previous page
                  </Button>
                  <Button
                    variant="outline"
                    disabled={busy || offset + 10 >= current.history.total}
                    onClick={() => setOffset(offset + 10)}
                  >
                    Next page
                  </Button>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
