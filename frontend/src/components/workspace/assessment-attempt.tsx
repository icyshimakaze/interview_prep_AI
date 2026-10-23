"use client";

import { useEffect, useRef, useState } from "react";
import type { Assessment, AssessmentApi } from "@/lib/api/assessments";
import { Button } from "@/components/ui/button";
import { TextareaField } from "@/components/ui/field";
import { ErrorDisplay } from "@/components/ui/states";
import { AssessmentReview } from "./assessment-review";

type Draft = { answer_text: string; selected_option_ids: string[] };
export function AssessmentAttemptView({
  initial,
  api,
  onBack,
}: {
  initial: Assessment;
  api: AssessmentApi;
  onBack: () => void;
}) {
  const [attempt, setAttempt] = useState(initial),
    [index, setIndex] = useState(0);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null),
    [message, setMessage] = useState("");
  const lock = useRef(false);
  const q = attempt.questions[index];
  const draft = q
    ? (drafts[q.id] ?? {
        answer_text: q.answer_text ?? "",
        selected_option_ids: q.selected_option_ids,
      })
    : null;
  const dirty = Object.keys(drafts).length > 0;
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  async function perform(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      await action();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The request failed. Your local response is still here. Try again or reload the saved attempt.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function saveCurrent(): Promise<Assessment> {
    if (!q || !draft || !drafts[q.id]) return attempt;
    const saved = await api.save(attempt.id, q.id, {
      revision: attempt.revision,
      ...draft,
    });
    setAttempt(saved);
    setDrafts((values) => {
      const next = { ...values };
      delete next[q.id];
      return next;
    });
    return saved;
  }
  function change(patch: Partial<Draft>) {
    if (q && draft)
      setDrafts((values) => ({ ...values, [q.id]: { ...draft, ...patch } }));
  }
  function navigate(next: number) {
    void perform(async () => {
      await saveCurrent();
      setIndex(next);
    });
  }
  const expired = attempt.status === "expired";
  const editable = attempt.status === "in_progress" && !expired;
  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <Button
          variant="outline"
          disabled={busy}
          onClick={() =>
            void perform(async () => {
              if (editable) await saveCurrent();
              onBack();
            })
          }
        >
          Back to assessments
        </Button>
        <p className="text-sm text-muted">
          {attempt.status.replaceAll("_", " ")} · {attempt.answered} of{" "}
          {attempt.question_count} responses saved
        </p>
      </div>
      <h2 className="section-title mb-3">{attempt.title}</h2>
      {attempt.deadline_at && attempt.status !== "completed" && (
        <p className="mb-5 text-sm text-muted">
          Deadline: {new Date(attempt.deadline_at).toLocaleString()}. Unanswered
          questions will be recorded as skipped.
        </p>
      )}
      {error && (
        <div className="mb-5">
          <ErrorDisplay message={error} />
          <p className="mt-3 text-sm">
            Your unsaved response stays in this page. Reload to resolve a stale
            revision or confirm a submission after a network error.
          </p>
          <Button
            variant="outline"
            disabled={busy}
            className="mt-3"
            onClick={() =>
              void perform(async () => {
                setAttempt(await api.read(attempt.id));
                setMessage(
                  "Saved attempt reloaded. Local edits are retained until saved.",
                );
              })
            }
          >
            Reload saved attempt
          </Button>
        </div>
      )}
      <p role="status" className="mb-4 text-sm text-muted">
        {busy ? "Saving your assessment…" : message}
      </p>
      {attempt.status === "completed" ? (
        <AssessmentReview attempt={attempt} />
      ) : (
        <>
          {expired && (
            <p role="alert" className="mb-5 rounded border border-line p-4">
              This attempt expired. Saved responses are retained. Return to
              assessments to start a new attempt.
            </p>
          )}
          <nav
            aria-label="Assessment questions"
            className="mb-6 flex flex-wrap gap-2"
          >
            {attempt.questions.map((item, i) => (
              <Button
                key={item.id}
                variant={i === index ? "default" : "outline"}
                disabled={busy}
                aria-current={i === index ? "step" : undefined}
                aria-label={`Question ${i + 1}${item.answer_text || item.selected_option_ids.length ? ", saved" : ""}`}
                onClick={() => (editable ? navigate(i) : setIndex(i))}
              >
                {i + 1}
              </Button>
            ))}
          </nav>
          {q && draft && (
            <section className="rounded-xl border border-line bg-surface p-5 sm:p-7">
              <p className="text-xs text-muted">
                Question {index + 1} of {attempt.question_count} · {q.category}{" "}
                · {q.difficulty}
              </p>
              <h3 className="mt-3 text-lg font-semibold">{q.title}</h3>
              <p className="mt-4 text-sm leading-7 whitespace-pre-wrap">
                {q.prompt}
              </p>
              <fieldset disabled={!editable || busy} className="mt-6 min-w-0">
                <legend className="sr-only">Your response to {q.title}</legend>
                {q.options.length ? (
                  <div className="space-y-3">
                    <p className="mb-4 text-sm font-medium">
                      {q.question_type === "multiple_select"
                        ? "Select all that apply. Exact set scoring; no partial credit."
                        : "Choose one answer."}
                    </p>
                    {q.options.map((option) => (
                      <label
                        key={option.id}
                        className="flex cursor-pointer items-start gap-3 rounded border border-line p-4 text-sm leading-6"
                      >
                        <input
                          className="mt-1 size-4 shrink-0 accent-accent"
                          type={
                            q.question_type === "multiple_select"
                              ? "checkbox"
                              : "radio"
                          }
                          name={`response-${q.id}`}
                          checked={draft.selected_option_ids.includes(
                            option.id,
                          )}
                          onChange={(e) =>
                            change({
                              selected_option_ids:
                                q.question_type === "multiple_select"
                                  ? e.target.checked
                                    ? [...draft.selected_option_ids, option.id]
                                    : draft.selected_option_ids.filter(
                                        (id) => id !== option.id,
                                      )
                                  : [option.id],
                            })
                          }
                        />
                        <span>{option.text}</span>
                      </label>
                    ))}
                    <Button
                      variant="ghost"
                      className="mt-3"
                      onClick={() => change({ selected_option_ids: [] })}
                    >
                      Clear selections
                    </Button>
                  </div>
                ) : (
                  <TextareaField
                    label="Your answer"
                    maxLength={10000}
                    value={draft.answer_text}
                    onChange={(e) => change({ answer_text: e.target.value })}
                    hint={
                      q.question_type === "short_answer"
                        ? "Enter a concise exact answer. Surrounding whitespace is ignored."
                        : "Explain your reasoning in a few sentences. The feedback provider and its limitations are disclosed before you start."
                    }
                  />
                )}
              </fieldset>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  disabled={busy || index === 0}
                  onClick={() =>
                    editable ? navigate(index - 1) : setIndex(index - 1)
                  }
                >
                  Previous
                </Button>
                {editable && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void perform(async () => {
                        await saveCurrent();
                        setMessage("Response saved.");
                      })
                    }
                  >
                    Save response
                  </Button>
                )}
                <Button
                  variant="outline"
                  disabled={busy || index === attempt.questions.length - 1}
                  onClick={() =>
                    editable ? navigate(index + 1) : setIndex(index + 1)
                  }
                >
                  Next
                </Button>
              </div>
            </section>
          )}
          {editable && (
            <section className="mt-7 rounded-xl border border-line p-5">
              <h3 className="font-semibold">Finish this attempt</h3>
              <p className="mt-2 mb-5 text-sm leading-6 text-muted">
                Submission saves the current response, records remaining blanks
                as skipped, and locks all responses for review.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button
                  disabled={busy}
                  onClick={() =>
                    void perform(async () => {
                      const saved = await saveCurrent();
                      setAttempt(await api.submit(saved.id, saved.revision));
                    })
                  }
                >
                  Submit assessment
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() =>
                    void perform(async () => {
                      const saved = await saveCurrent();
                      setAttempt(await api.abandon(saved.id, saved.revision));
                    })
                  }
                >
                  Abandon attempt
                </Button>
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}
