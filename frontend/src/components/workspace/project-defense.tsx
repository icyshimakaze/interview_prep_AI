"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorDisplay } from "@/components/ui/states";
import type { Defense, DefenseAction, ProjectApi } from "@/lib/api/projects";
import { AIReview } from "./ai-review";

export function ProjectDefense({
  initial,
  api,
  onBack,
}: {
  initial: Defense;
  api: ProjectApi;
  onBack: () => void;
}) {
  const [run, setRun] = useState(initial);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  const current = run.responses.find(
    (r) => r.position === run.current_position,
  );
  const [answer, setAnswer] = useState(current?.answer_text ?? "");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [recoveredDraft, setRecoveredDraft] = useState<string | null>(null);
  const lock = useRef(false);
  async function act(action: DefenseAction | "reload") {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setSaved("");
    try {
      const result =
        action === "reload"
          ? await api.readRun(run.id)
          : await api.command(
              run.id,
              run.revision,
              action,
              run.status === "active" && action !== "resume"
                ? answer
                : undefined,
            );
      setRun(result);
      if (
        action === "reload" &&
        (result.current_position !== run.current_position ||
          result.status === "completed")
      ) {
        if (answer !== (current?.answer_text ?? "")) setRecoveredDraft(answer);
        setAnswer(
          result.responses.find((r) => r.position === result.current_position)
            ?.answer_text ?? "",
        );
      } else if (action !== "reload" && action !== "resume")
        setAnswer(
          result.responses.find((r) => r.position === result.current_position)
            ?.answer_text ?? "",
        );
      setSaved(
        action === "reload"
          ? "Saved session reloaded. Your local draft is retained; review it before saving."
          : "Saved.",
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The request failed. Your local answer is retained.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const dirty = answer !== (current?.answer_text ?? "");
  return (
    <div className="space-y-5">
      <h1 ref={heading} tabIndex={-1} className="page-title">
        Project Defense interview
      </h1>
      <p className="text-sm leading-7 text-muted">
        Deterministic practice · {run.status} ·{" "}
        {api.ai
          ? "Optional AI feedback is available below for submitted answers."
          : "No AI evaluation or numerical score."}{" "}
        Explain decisions, evidence, trade-offs and your own contributions,
        including AI assistance.
      </p>
      {error && (
        <ErrorDisplay
          title="Practice request failed"
          message={`${error} Your local answer is retained.`}
        />
      )}
      {saved && <p role="status">{saved}</p>}
      {recoveredDraft !== null && (
        <label className="block">
          Recovered local draft from the previous question (not submitted)
          <textarea className="input mt-2" readOnly value={recoveredDraft} />
        </label>
      )}
      {run.status !== "completed" && current && (
        <section className="space-y-4 border-y border-line bg-surface p-5">
          <h2 className="section-title">
            Question {current.position} of {run.responses.length}:{" "}
            {current.question.focus}
          </h2>
          <p>{current.question.prompt}</p>
          <p className="text-sm">
            {current.question.inferred ? "Inferred clue" : "Observed clue"}:{" "}
            {current.question.evidence}
          </p>
          <p className="text-sm break-all">
            {current.question.path}:{current.question.line}
          </p>
          <label className="block">
            Your answer
            <textarea
              className="input mt-2 min-h-48"
              maxLength={10000}
              value={answer}
              disabled={busy || run.status !== "active"}
              onChange={(e) => setAnswer(e.target.value)}
            />
          </label>
          <p className="text-sm">
            {answer.length}/10,000 characters ·{" "}
            {dirty ? "Unsaved changes" : "Draft matches saved answer"}
          </p>
          <div className="flex flex-wrap gap-2">
            {run.status === "active" ? (
              <>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => void act("save")}
                >
                  Save draft
                </Button>
                <Button
                  disabled={busy || !answer.trim()}
                  onClick={() => void act("submit")}
                >
                  Submit answer
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => void act("skip")}
                >
                  Skip question
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => void act("pause")}
                >
                  Save and pause
                </Button>
              </>
            ) : (
              <Button disabled={busy} onClick={() => void act("resume")}>
                Resume
              </Button>
            )}
            <Button
              variant="outline"
              disabled={busy || (run.status === "paused" && dirty)}
              onClick={() => void act("end")}
            >
              End practice
            </Button>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => void act("reload")}
            >
              Reload saved session
            </Button>
          </div>
        </section>
      )}
      <details
        className="border-t border-line pt-4"
        open={run.status === "completed"}
      >
        <summary className="cursor-pointer font-semibold">
          Question history and saved answers
        </summary>
        <ol className="mt-4 space-y-5">
          {run.responses.map((r) => (
            <li key={r.position}>
              <h3 className="font-semibold">
                {r.position}. {r.question.focus} · {r.status}
              </h3>
              <p>{r.question.prompt}</p>
              <p className="whitespace-pre-wrap">
                {r.answer_text || "No saved answer."}
              </p>
              {r.submitted_at && (
                <p className="text-sm">
                  {new Date(r.submitted_at).toLocaleString()}
                </p>
              )}
              {api.ai && r.status === "submitted" && (
                <AIReview
                  api={api.ai}
                  resource={`defense/${encodeURIComponent(run.id)}/${r.position}`}
                  label={`Review defense answer ${r.position}`}
                />
              )}
            </li>
          ))}
        </ol>
        <p className="mt-4">
          Reflection: name the evidence behind your explanation, an alternative
          you rejected, a failure case you would test, and what you would change
          next.
        </p>
      </details>
      <Button variant="outline" disabled={busy || dirty} onClick={onBack}>
        Back to repository
      </Button>
      {dirty && <p>Save or pause before leaving to retain your answer.</p>}
    </div>
  );
}
