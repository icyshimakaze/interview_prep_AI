"use client";

import { useEffect, useRef, useState } from "react";
import type {
  PracticeInput,
  QuestionApi,
  QuestionDetail,
} from "@/lib/api/questions";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { Badge } from "@/components/ui/table";
import { QuestionAttemptHistory } from "./question-history";

function PracticeForm({
  question,
  api,
  mode,
  onSubmitted,
}: {
  question: QuestionDetail;
  api: QuestionApi;
  mode: "account" | "demo";
  onSubmitted: () => void;
}) {
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = useRef<PracticeInput | null>(null);
  const locked = useRef(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked.current) return;
    const text = answer.trim();
    if (!text || text.length > 10000) {
      setError("Enter a response of 1 to 10,000 characters.");
      return;
    }
    if (pending.current?.answer_text !== text)
      pending.current = {
        answer_text: text,
        question_version_id: question.version_id,
        submission_key: crypto.randomUUID(),
      };
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      await api.submit(question.id, pending.current);
      pending.current = null;
      setAnswer("");
      onSubmitted();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Submission could not be confirmed. Retry your response.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <form onSubmit={(event) => void submit(event)} className="mt-7 space-y-4">
      <p className="text-sm leading-7 text-muted">
        {mode === "demo"
          ? "Use a fictional response in this expiring demo."
          : "Your response is saved privately until you delete it."}{" "}
        This question-bank practice uses self-review. It does not generate an
        assessment score or validate competence.
      </p>
      {question.options.length ? (
        <fieldset disabled={busy}>
          <legend className="mb-3 text-sm font-medium">
            Your selected response
          </legend>
          <div className="space-y-3">
            {question.options.map((option) => (
              <label
                key={option.id}
                className="flex items-start gap-3 text-sm leading-6"
              >
                <input
                  className="mt-1"
                  type="radio"
                  name="practice-response"
                  checked={answer === option.text}
                  onChange={() => setAnswer(option.text)}
                />
                {option.text}
              </label>
            ))}
          </div>
        </fieldset>
      ) : (
        <label className="block text-sm font-medium">
          Your response
          <textarea
            value={answer}
            disabled={busy}
            onChange={(event) => setAnswer(event.target.value)}
            maxLength={10000}
            rows={6}
            className="mt-2 w-full rounded border border-line bg-surface p-3 font-normal"
            required
          />
        </label>
      )}
      {error && <ErrorDisplay message={error} />}
      <Button type="submit" disabled={busy || !question.active}>
        {busy ? "Saving response…" : "Submit for self-review"}
      </Button>
    </form>
  );
}

export function QuestionDetailView({
  api,
  id,
  mode,
  onBack,
}: {
  api: QuestionApi;
  id: string;
  mode: "account" | "demo";
  onBack: () => void;
}) {
  const [refresh, setRefresh] = useState(0);
  const [state, setState] = useState<{
    refresh: number;
    data?: QuestionDetail;
    error?: string;
  } | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    void api
      .read(id, controller.signal)
      .then((data) => {
        if (active) setState({ refresh, data });
      })
      .catch((reason: unknown) => {
        if (active)
          setState({
            refresh,
            error:
              reason instanceof Error
                ? reason.message
                : "Question could not load.",
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, id, refresh]);
  const current = state?.refresh === refresh ? state : null;
  const question = current?.data;
  function reload() {
    setRefresh((value) => value + 1);
  }
  return (
    <>
      <div className="mb-6 flex flex-wrap gap-3">
        <Button variant="outline" onClick={onBack}>
          Back to question bank
        </Button>
        <Button variant="outline" onClick={reload}>
          Reload question
        </Button>
      </div>
      {saved && (
        <p role="status" className="my-4 text-sm">
          Response saved. Review the expected concepts below.
        </p>
      )}
      {!current && <WorkspaceSkeleton label="Loading question…" />}
      {current?.error && (
        <ErrorDisplay message={current.error} onRetry={reload} />
      )}
      {question && (
        <>
          <article className="border-y border-line bg-surface p-5 sm:p-8">
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge>{question.category}</Badge>
              <Badge>{question.difficulty}</Badge>
              <Badge>{question.question_type.replaceAll("_", " ")}</Badge>
              {!question.active && <Badge tone="amber">Inactive</Badge>}
            </div>
            <h2 className="section-title">{question.title}</h2>
            <p className="mt-5 text-sm leading-7 break-words whitespace-pre-wrap">
              {question.prompt}
            </p>
            <p className="mt-5 text-xs leading-6 text-muted">
              {question.subtopic} ·{" "}
              {question.source_classification.replaceAll("_", " ")} · Version{" "}
              {question.version}
            </p>
            {question.source_file && (
              <p className="text-xs break-all text-muted">
                Source: {question.source_file}
                {question.original_topic
                  ? ` · original topic ${question.original_topic}`
                  : ""}
              </p>
            )}
            {question.active && (
              <PracticeForm
                key={question.version_id}
                question={question}
                api={api}
                mode={mode}
                onSubmitted={() => {
                  setSaved(true);
                  reload();
                }}
              />
            )}
          </article>
          <section className="section-rule">
            <h2 className="section-title">Expected concepts</h2>
            {question.concepts_unlocked ? (
              <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7">
                {question.expected_concepts?.map((concept) => (
                  <li key={concept}>{concept}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-muted">
                Submit a response to this question version to review its
                expected concepts. Your other attempts do not reveal a newer
                version.
              </p>
            )}
          </section>
        </>
      )}
      <QuestionAttemptHistory
        api={api}
        id={id}
        refresh={refresh}
        onDeleted={reload}
      />
    </>
  );
}
