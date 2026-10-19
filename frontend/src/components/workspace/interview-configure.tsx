"use client";

import { useState, type FormEvent } from "react";
import {
  interviewLabel,
  interviewTypes,
  type InterviewConfig,
  type InterviewOptions,
} from "@/lib/api/interviews";
import { Button } from "@/components/ui/button";

export function InterviewConfigure({
  options,
  busy,
  onCreate,
}: {
  options: InterviewOptions;
  busy: boolean;
  onCreate: (config: InterviewConfig) => void;
}) {
  const [type, setType] = useState<InterviewConfig["interview_type"]>(
      "technical_fundamentals",
    ),
    [difficulty, setDifficulty] =
      useState<InterviewConfig["difficulty"]>("auto"),
    [target, setTarget] = useState(""),
    [count, setCount] = useState(5);
  const available = options.inventory.find(
    (v) => v.interview_type === type && v.difficulty === difficulty,
  );
  const valid =
    !!available &&
    count >= available.min_questions &&
    count <= available.max_questions;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (valid)
      onCreate({
        target_id: target || null,
        interview_type: type,
        difficulty,
        question_count: count,
      });
  }
  return (
    <form
      onSubmit={submit}
      className="mb-8 space-y-5 rounded-xl border border-line bg-surface p-5 sm:p-6"
    >
      <h2 className="section-title">Configure an interview</h2>
      <p className="text-sm leading-6 text-muted">
        {options.provider.disclosure}{" "}
        {options.provider.name === "OpenAIProvider"
          ? "Written answers are sent to OpenAI."
          : options.provider.name === "OllamaProvider"
            ? "Written answers are sent to your configured Ollama server."
            : "No external AI credentials or API calls are needed."}
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium">
          Target job
          <select
            className="field mt-2 w-full"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            disabled={busy}
          >
            <option value="">General practice</option>
            {options.targets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">
          Interview type
          <select
            className="field mt-2 w-full"
            value={type}
            disabled={busy}
            onChange={(e) => {
              const selected = interviewTypes.find((v) => v === e.target.value);
              if (selected) {
                setType(selected);
                const row = options.inventory.find(
                  (v) =>
                    v.interview_type === selected &&
                    v.difficulty === difficulty,
                );
                setCount(
                  Math.max(
                    row?.min_questions ?? 1,
                    Math.min(5, row?.max_questions ?? 0),
                  ),
                );
              }
            }}
          >
            {interviewTypes.map((v) => (
              <option key={v} value={v}>
                {interviewLabel(v)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">
          Interview difficulty
          <select
            className="field mt-2 w-full"
            value={difficulty}
            disabled={busy}
            onChange={(e) => {
              const value = e.target.value;
              if (
                value === "auto" ||
                value === "easy" ||
                value === "medium" ||
                value === "hard"
              )
                setDifficulty(value);
            }}
          >
            <option value="auto">Adaptive starting level</option>
            <option value="easy">Easy only</option>
            <option value="medium">Medium only</option>
            <option value="hard">Hard only</option>
          </select>
        </label>
        <label className="text-sm font-medium">
          Main questions
          <input
            className="field mt-2 w-full"
            type="number"
            min={available?.min_questions ?? 1}
            max={available?.max_questions || 10}
            value={count}
            disabled={busy}
            onChange={(e) => setCount(Number(e.target.value))}
          />
        </label>
      </div>
      <p className="text-sm text-muted">
        {available?.available_count ?? 0} published typed questions match. Up to{" "}
        {available?.max_questions ?? 0} main questions are available with this
        coverage. Follow-ups are optional and do not count as main questions.
      </p>
      {!valid && (
        <p role="status" className="text-sm">
          Choose an available difficulty and question count. Full Stack needs
          both Backend and Frontend coverage.
        </p>
      )}
      <p className="text-xs leading-5 text-muted">
        {options.notices.join(" ")}
      </p>
      <Button type="submit" disabled={busy || !valid}>
        {busy ? "Starting…" : "Start interview"}
      </Button>
    </form>
  );
}
