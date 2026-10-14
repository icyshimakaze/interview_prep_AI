"use client";

import { useEffect, useRef, useState } from "react";
import type { QuestionApi, QuestionHistory } from "@/lib/api/questions";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";

export function QuestionAttemptHistory({
  api,
  id,
  refresh,
  onDeleted,
}: {
  api: QuestionApi;
  id: string;
  refresh: number;
  onDeleted: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState<{
    offset: number;
    refresh: number;
    data?: QuestionHistory;
    error?: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const locked = useRef(false);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void api
      .history(id, offset, controller.signal)
      .then((data) => {
        if (active) setState({ offset, refresh, data });
      })
      .catch((reason: unknown) => {
        if (active)
          setState({
            offset,
            refresh,
            error:
              reason instanceof Error
                ? reason.message
                : "History could not load.",
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, id, offset, refresh]);
  const current =
    state?.offset === offset && state.refresh === refresh ? state : null;
  const data = current?.data;
  async function remove(attemptId: string) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      await api.removeAttempt(id, attemptId);
      setOffset(0);
      onDeleted();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The response could not be deleted.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <section className="section-rule">
      <h2 className="section-title">Your submitted attempt history</h2>
      <p className="my-3 text-sm text-muted">
        Includes submitted question-bank, assessment and interview responses
        across content versions. A submitted response alone does not validate
        competence.
      </p>
      {error && <ErrorDisplay message={error} />}
      {!current && <WorkspaceSkeleton label="Loading attempt history…" />}
      {current?.error && (
        <ErrorDisplay message={current.error} onRetry={onDeleted} />
      )}
      {data && (
        <>
          {!data.items.length && (
            <p className="py-4 text-sm text-muted">
              No submitted attempts yet.
            </p>
          )}
          <ol className="divide-y divide-line">
            {data.items.map((item) => (
              <li key={`${item.channel}:${item.id}`} className="py-5">
                <div className="flex flex-wrap justify-between gap-3">
                  <p className="text-sm font-medium">
                    {item.channel.replaceAll("_", " ")} ·{" "}
                    {item.result_kind?.replaceAll("_", " ") ??
                      "Evaluation unavailable"}
                  </p>
                  <time
                    className="text-xs text-muted"
                    dateTime={item.submitted_at}
                  >
                    {item.submitted_at.slice(0, 10)}
                  </time>
                </div>
                <p className="mt-3 text-sm leading-7 break-words whitespace-pre-wrap">
                  {item.response ??
                    "Response recorded in the original workflow."}
                </p>
                <p className="mt-2 text-xs break-all text-muted">
                  Question version: {item.question_version_id}
                </p>
                {item.channel === "question_bank" && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm text-muted">
                      Delete this saved practice response
                    </summary>
                    <p className="mt-2 text-sm text-muted">
                      This removes your response and its attempt record. This
                      cannot be undone.
                    </p>
                    <Button
                      className="mt-3"
                      variant="danger"
                      disabled={busy}
                      onClick={() => void remove(item.id)}
                    >
                      Delete response
                    </Button>
                  </details>
                )}
              </li>
            ))}
          </ol>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              disabled={offset === 0 || busy}
              onClick={() => setOffset(Math.max(0, offset - 10))}
            >
              Previous attempts
            </Button>
            <p className="text-sm text-muted">
              {data.total} submitted attempts
            </p>
            <Button
              variant="outline"
              disabled={offset + data.limit >= data.total || busy}
              onClick={() => setOffset(offset + data.limit)}
            >
              Next attempts
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
