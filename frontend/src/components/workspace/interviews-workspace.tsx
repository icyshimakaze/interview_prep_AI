"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  interviewLabel,
  type Interview,
  type InterviewApi,
  type InterviewConfig,
  type InterviewOptions,
  type InterviewPage,
} from "@/lib/api/interviews";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { SectionHeader } from "./section-header";
import { InterviewConfigure } from "./interview-configure";
import { InterviewSession } from "./interview-session";

export function InterviewsWorkspace({ api }: { api: InterviewApi }) {
  const [state, setState] = useState<{
      options: InterviewOptions;
      history: InterviewPage;
    } | null>(null),
    [selected, setSelected] = useState<Interview | null>(null),
    [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false),
    [offset, setOffset] = useState(0),
    [refresh, setRefresh] = useState(0);
  const lock = useRef(false),
    start = useRef<{
      signature: string;
      key: string;
      session: Interview | null;
      startKey: string;
    } | null>(null);
  const back = useCallback(() => {
    setSelected(null);
    setRefresh((v) => v + 1);
  }, []);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void Promise.all([
      api.options(controller.signal),
      api.history(offset, controller.signal),
    ])
      .then(([options, history]) => {
        if (active) {
          setState({ options, history });
          setError(null);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Interviews could not load.",
          );
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, offset, refresh]);
  async function perform(action: () => Promise<Interview>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      setSelected(await action());
    } catch (reason: unknown) {
      setError(
        reason instanceof Error ? reason.message : "Interview request failed.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  function create(config: InterviewConfig) {
    void perform(async () => {
      const signature = JSON.stringify(config);
      if (start.current?.signature !== signature)
        start.current = {
          signature,
          key: crypto.randomUUID(),
          session: null,
          startKey: crypto.randomUUID(),
        };
      const attempt = start.current;
      if (!attempt.session)
        attempt.session = await api.create(config, attempt.key);
      const session = await api.command(attempt.session.id, "start", {
        command_key: attempt.startKey,
        revision: attempt.session.revision,
      });
      start.current = null;
      return session;
    });
  }
  return (
    <>
      <SectionHeader
        title="Mock interviews"
        eyebrow="One question at a time"
        description="Practice typed answers, save your progress, ask optional follow-ups and review your work. Feedback is simulated by default."
      />
      {selected ? (
        <InterviewSession
          key={selected.id}
          initial={selected}
          api={api}
          onBack={back}
        />
      ) : (
        <>
          {error && (
            <ErrorDisplay
              message={error}
              onRetry={() => setRefresh((v) => v + 1)}
              busy={busy}
            />
          )}
          {!state && !error && (
            <WorkspaceSkeleton label="Loading interviews…" />
          )}
          {state && (
            <>
              <InterviewConfigure
                options={state.options}
                busy={busy}
                onCreate={create}
              />
              <h2 className="section-title mb-4">Saved interviews</h2>
              <div className="space-y-3">
                {state.history.items.map((s) => (
                  <div
                    key={s.id}
                    className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-line p-5"
                  >
                    <div>
                      <h3 className="font-medium">
                        {s.configuration
                          ? interviewLabel(
                              s.configuration.interview_type ?? "mixed",
                            )
                          : "Historical interview example"}
                      </h3>
                      <p className="mt-1 text-sm text-muted">
                        {s.status} · {s.progress.resolved} /{" "}
                        {s.progress.requested} main questions ·{" "}
                        {s.provider.kind}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={() => void perform(() => api.read(s.id))}
                    >
                      {s.allowed_actions.includes("review")
                        ? "Review interview"
                        : "Open saved interview"}
                    </Button>
                  </div>
                ))}
              </div>
              {!state.history.total && (
                <p className="text-sm text-muted">
                  No interviews yet. Start a session above.
                </p>
              )}
              <div className="mt-5 flex items-center justify-between">
                <p className="text-sm text-muted">
                  {state.history.total} saved interviews
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
                    disabled={busy || offset + 10 >= state.history.total}
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
