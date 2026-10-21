"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  Interview,
  InterviewApi,
  InterviewPayload,
  InterviewReview,
} from "@/lib/api/interviews";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ErrorDisplay } from "@/components/ui/states";
import { InterviewReviewView } from "./interview-review";
import { WorkspaceError } from "@/lib/api/workspace";

type PendingCommand = {
  action: string;
  body: InterviewPayload;
  method: "POST" | "PUT";
};

export function InterviewSession({
  initial,
  api,
  onBack,
}: {
  initial: Interview;
  api: InterviewApi;
  onBack: () => void;
}) {
  const [interview, setInterview] = useState(initial),
    [text, setText] = useState(initial.current_turn?.answer_text ?? ""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null),
    [ending, setEnding] = useState(false),
    [review, setReview] = useState<InterviewReview | null>(null),
    [elapsed, setElapsed] = useState(0),
    [backup, setBackup] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingCommand | null>(null);
  const lock = useRef(false),
    heading = useRef<HTMLHeadingElement>(null),
    mounted = useRef(true);
  const turn = interview.current_turn,
    dirty = text !== (turn?.answer_text ?? ""),
    actions = interview.allowed_actions;
  const reviewing = actions.includes("review");
  const apply = useCallback(
    (next: Interview, replaceText = false) => {
      setInterview(next);
      if (replaceText || next.current_turn?.id !== interview.current_turn?.id) {
        setText(next.current_turn?.answer_text ?? "");
        setTimeout(() => heading.current?.focus(), 0);
      }
    },
    [interview.current_turn?.id],
  );
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const perform = useCallback(
    async (command: PendingCommand, back = false) => {
      if (lock.current) return;
      lock.current = true;
      setPending(command);
      setBusy(true);
      setError(null);
      try {
        let result: Interview;
        let request = command;
        // Claim and completion can each advance a worker revision. Retry only
        // unchanged candidate state, with a hard limit of three total attempts.
        for (let retries = 0; ; retries += 1) {
          try {
            result = await api.command(
              interview.id,
              request.action,
              request.body,
              request.method,
            );
            break;
          } catch (reason: unknown) {
            if (
              retries >= 2 ||
              !(reason instanceof WorkspaceError) ||
              reason.code !== "interview_revision"
            )
              throw reason;
            const latest = await api.read(interview.id);
            if (
              latest.status !== interview.status ||
              latest.current_turn?.id !== interview.current_turn?.id ||
              latest.current_turn?.answer_text !==
                interview.current_turn?.answer_text ||
              latest.followup_decision !== interview.followup_decision
            )
              throw reason;
            request = {
              ...request,
              body: {
                ...request.body,
                revision: latest.revision,
                command_key: crypto.randomUUID(),
              },
            };
            setPending(request);
          }
        }
        if (mounted.current) {
          apply(result);
          setPending(null);
          setEnding(false);
          if (back) onBack();
        }
      } catch (reason: unknown) {
        if (mounted.current)
          setError(
            reason instanceof Error
              ? reason.message
              : "Interview request failed. Your text is retained.",
          );
      } finally {
        lock.current = false;
        if (mounted.current) setBusy(false);
      }
    },
    [api, apply, interview, onBack],
  );

  const command = useCallback(
    (
      action: string,
      extra: Partial<InterviewPayload> = {},
      method: "POST" | "PUT" = "POST",
      back = false,
    ) =>
      perform(
        {
          action,
          body: {
            command_key: crypto.randomUUID(),
            revision: interview.revision,
            ...extra,
          },
          method,
        },
        back,
      ),
    [interview.revision, perform],
  );

  useEffect(() => {
    if (!dirty || !actions.includes("save") || busy || error) return;
    const timer = setTimeout(() => {
      if (!lock.current && turn)
        void command(
          `turns/${turn.id}/draft`,
          { answer_text: text || null },
          "PUT",
        );
    }, 900);
    return () => clearTimeout(timer);
  }, [actions, busy, command, dirty, error, text, turn]);

  useEffect(() => {
    if (!turn) return;
    const base = turn.answering_ms;
    const start = turn.running_since ? Date.parse(turn.running_since) : null;
    const offset = Date.parse(interview.server_time) - Date.now();
    const update = () =>
      setElapsed(
        Math.floor(
          (base + (start ? Math.max(0, Date.now() + offset - start) : 0)) /
            1000,
        ),
      );
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [turn, interview.server_time]);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    async function refresh() {
      if (document.hidden || lock.current) return;
      try {
        if (reviewing) {
          const result = await api.review(interview.id, controller.signal);
          if (active) {
            setReview(result);
            setInterview(result.session);
          }
        } else {
          const result = await api.read(interview.id, controller.signal);
          if (active) {
            if (result.current_turn?.id !== interview.current_turn?.id && dirty)
              setError(
                "This session advanced elsewhere. Copy your unsaved text or reload and reconcile it before continuing.",
              );
            else setInterview(result);
          }
        }
      } catch (reason: unknown) {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Saved interview could not reload.",
          );
      }
    }
    if (reviewing) void refresh();
    const needsPoll =
      (reviewing && interview.status === "finalizing") ||
      (!reviewing &&
        (interview.progress.evaluation_pending > 0 ||
          interview.followup_decision === "pending" ||
          interview.expired));
    const timer = needsPoll ? setInterval(() => void refresh(), 3000) : null;
    return () => {
      active = false;
      controller.abort();
      if (timer) clearInterval(timer);
    };
  }, [
    api,
    dirty,
    interview.current_turn?.id,
    interview.expired,
    interview.followup_decision,
    interview.id,
    interview.progress.evaluation_pending,
    interview.status,
    reviewing,
  ]);

  async function reload() {
    if (lock.current) return;
    setBusy(true);
    try {
      const saved = await api.read(interview.id);
      if (dirty) setBackup(text);
      setPending(null);
      apply(saved, true);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Reload failed.");
    } finally {
      setBusy(false);
    }
  }
  const disabled = busy || !!error;
  const draft =
    turn?.status === "awaiting_answer"
      ? { turn_id: turn.id, answer_text: text || null }
      : null;
  function end(action: "keep_draft" | "submit" | "skip" | "none") {
    void command("end", { draft, current_answer_action: action });
  }
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="outline"
          disabled={busy}
          onClick={() => {
            if (actions.includes("pause") && !interview.expired)
              void command("pause", { draft }, "POST", true);
            else onBack();
          }}
        >
          {actions.includes("pause") && !interview.expired
            ? "Save, pause and return"
            : "Back to interviews"}
        </Button>
        <p className="text-sm text-muted">
          {interview.status} · {interview.progress.resolved} /{" "}
          {interview.progress.requested} main questions resolved
        </p>
      </div>
      {error && (
        <div>
          <ErrorDisplay message={error} />
          <div className="mt-3 flex gap-3">
            {pending && (
              <Button
                disabled={busy}
                onClick={() => {
                  if (pending) void perform(pending);
                }}
              >
                Retry same request
              </Button>
            )}
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => void reload()}
            >
              Reload saved state
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted">
            Your text remains below. Reloading retains an in-memory copy for
            reconciliation.
          </p>
        </div>
      )}
      {backup && (
        <details className="rounded-lg border border-line p-4 text-sm">
          <summary>Retained unsaved text</summary>
          <p className="mt-3 whitespace-pre-wrap">{backup}</p>
          {actions.includes("save") && (
            <Button
              variant="outline"
              className="mt-3"
              disabled={busy}
              onClick={() => {
                setText(backup);
                setBackup(null);
              }}
            >
              Use this draft for the current question
            </Button>
          )}
        </details>
      )}
      <p className="text-sm leading-6 text-muted">
        {interview.provider.disclosure}
      </p>
      {reviewing ? (
        review ? (
          <InterviewReviewView review={review} />
        ) : (
          <p role="status">Loading review…</p>
        )
      ) : (
        <>
          {interview.expired && (
            <p role="status">
              This interview expired. Saved work is retained; the server will
              prepare its partial review.
            </p>
          )}
          {interview.status === "draft" && (
            <Button disabled={disabled} onClick={() => void command("start")}>
              Begin saved interview
            </Button>
          )}
          {turn && (
            <section className="rounded-xl border border-line bg-surface p-5 sm:p-7">
              <p className="text-xs font-medium text-muted">
                {turn.parent_id
                  ? `Follow-up to main ${turn.main_ordinal}`
                  : `Main question ${turn.main_ordinal ?? turn.sequence}`}{" "}
                · {turn.category}
                {turn.difficulty ? ` · ${turn.difficulty}` : ""}
              </p>
              <h2
                ref={heading}
                tabIndex={-1}
                className="mt-4 text-lg leading-8 font-semibold"
              >
                {turn.prompt}
              </h2>
              {turn.context_excerpt && (
                <blockquote className="mt-4 border-l-2 border-line pl-4 text-sm leading-6">
                  Your earlier response: “{turn.context_excerpt}”
                </blockquote>
              )}
              <p className="mt-3 text-xs text-muted">
                Answering time: {Math.floor(elapsed / 60)}m {elapsed % 60}s ·
                includes time away unless paused.
              </p>
              <label
                className="mt-5 block text-sm font-medium"
                htmlFor="interview-answer"
              >
                Your answer
              </label>
              <textarea
                id="interview-answer"
                className="field mt-2 min-h-52 w-full"
                maxLength={10000}
                value={text}
                readOnly={!actions.includes("save")}
                disabled={busy}
                onChange={(e) => setText(e.target.value)}
                aria-describedby="interview-save-state"
              />
              <p
                id="interview-save-state"
                role="status"
                className="mt-2 text-xs text-muted"
              >
                {busy
                  ? "Saving or applying request…"
                  : dirty
                    ? "Unsaved changes"
                    : "Saved on server"}{" "}
                · {text.length} / 10000 characters
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                {actions.includes("save") && (
                  <Button
                    variant="outline"
                    disabled={disabled}
                    onClick={() =>
                      void command(
                        `turns/${turn.id}/draft`,
                        { answer_text: text || null },
                        "PUT",
                      )
                    }
                  >
                    Save answer
                  </Button>
                )}
                {actions.includes("submit") && (
                  <Button
                    disabled={disabled || !text.trim()}
                    onClick={() =>
                      void command(`turns/${turn.id}/submit`, {
                        answer_text: text,
                      })
                    }
                  >
                    Submit answer
                  </Button>
                )}
                {actions.includes("skip") && (
                  <Button
                    variant="outline"
                    disabled={disabled}
                    onClick={() =>
                      void command(`turns/${turn.id}/skip`, {
                        answer_text: text || null,
                      })
                    }
                  >
                    Skip question
                  </Button>
                )}
                {actions.includes("followup") && (
                  <Button
                    variant="outline"
                    disabled={disabled}
                    onClick={() => void command(`turns/${turn.id}/followup`)}
                  >
                    Ask a follow-up
                  </Button>
                )}
                {actions.includes("advance_followup") && (
                  <Button
                    disabled={disabled}
                    onClick={() =>
                      void command("advance", {
                        from_turn_id: turn.id,
                        next_kind: "followup",
                      })
                    }
                  >
                    Answer follow-up
                  </Button>
                )}
                {actions.includes("advance_main") && (
                  <Button
                    disabled={disabled}
                    onClick={() =>
                      void command("advance", {
                        from_turn_id: turn.id,
                        next_kind: "main",
                      })
                    }
                  >
                    {interview.followup_decision === "pending" ||
                    interview.followup_decision === "ready"
                      ? "Continue without follow-up"
                      : "Next main question"}
                  </Button>
                )}
                {actions.includes("complete") && (
                  <Button
                    disabled={disabled}
                    onClick={() => void command("complete")}
                  >
                    Complete interview
                  </Button>
                )}
              </div>
              {interview.followup_decision === "pending" && (
                <p role="status" className="mt-4 text-sm">
                  Preparing optional follow-up. You can continue or finish
                  without it.
                </p>
              )}
              {interview.followup_decision === "unavailable" && (
                <p role="status" className="mt-4 text-sm">
                  Follow-up unavailable. Your submitted answer is saved;
                  continue to the next question or finish.
                </p>
              )}
              {interview.phase === "between_questions" && (
                <p className="mt-4 text-xs text-muted">
                  Feedback is held for final review. Follow-ups used:{" "}
                  {interview.progress.followups_reserved} / 3.
                </p>
              )}
            </section>
          )}
          <div className="flex flex-wrap gap-3">
            {actions.includes("retry_evaluation") && turn?.evaluation_id && (
              <Button
                variant="outline"
                disabled={disabled}
                onClick={() =>
                  void command(`turns/${turn.id}/evaluation/retry`, {
                    evaluation_id: turn.evaluation_id ?? undefined,
                  })
                }
              >
                Retry unavailable evaluation once
              </Button>
            )}
            {actions.includes("pause") && (
              <Button
                variant="outline"
                disabled={disabled}
                onClick={() => void command("pause", { draft })}
              >
                Pause interview
              </Button>
            )}
            {actions.includes("resume") && (
              <Button
                disabled={disabled}
                onClick={() => void command("resume")}
              >
                Resume interview
              </Button>
            )}
            {actions.includes("end") && (
              <Button
                variant="outline"
                disabled={disabled}
                onClick={() => setEnding(true)}
              >
                End early
              </Button>
            )}
          </div>
          <details className="text-xs leading-6 text-muted">
            <summary>Selection and timing notes</summary>
            {interview.notices.map((notice) => (
              <p key={notice}>{notice}</p>
            ))}
          </details>
        </>
      )}
      <Dialog
        open={ending}
        onClose={() => setEnding(false)}
        busy={busy}
        title="End this interview?"
      >
        <p className="text-sm leading-6">
          This closes the session and prepares a partial review. Submitted
          answers remain saved.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          {draft ? (
            <>
              <Button disabled={disabled} onClick={() => end("keep_draft")}>
                Keep draft without submitting
              </Button>
              <Button
                variant="outline"
                disabled={disabled || !text.trim()}
                onClick={() => end("submit")}
              >
                Submit current answer and end
              </Button>
              <Button
                variant="outline"
                disabled={disabled}
                onClick={() => end("skip")}
              >
                Skip current question and end
              </Button>
            </>
          ) : (
            <Button disabled={disabled} onClick={() => end("none")}>
              End and review saved work
            </Button>
          )}
        </div>
      </Dialog>
    </div>
  );
}
