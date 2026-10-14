"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { InputField, SelectField } from "@/components/ui/field";
import {
  assessmentTypes,
  assessmentTypeLabel,
  type AssessmentConfig,
  type AssessmentOptions,
} from "@/lib/api/assessments";

export function AssessmentConfigure({
  options,
  busy,
  onStart,
}: {
  options: AssessmentOptions;
  busy: boolean;
  onStart: (config: AssessmentConfig) => void;
}) {
  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState<"" | "easy" | "medium" | "hard">(
    "",
  );
  const [types, setTypes] = useState<AssessmentConfig["question_types"]>([
    ...assessmentTypes,
  ]);
  const [countText, setCount] = useState("3");
  const count = Number(countText);
  const available = options.inventory
    .filter(
      (i) =>
        (!category || i.category === category) &&
        (!difficulty || i.difficulty === difficulty) &&
        types.some((t) => t === i.question_type),
    )
    .reduce((sum, i) => sum + i.count, 0);
  return (
    <section className="mb-10 rounded-xl border border-line bg-surface p-5 sm:p-7">
      <h2 className="section-title">Configure an assessment</h2>
      <p className="mt-2 text-sm leading-6 text-muted">
        Choose published questions by topic, difficulty and format. Drafts stay
        editable for {options.duration_hours} hours. Objective answers are
        graded on the server; conceptual feedback uses{" "}
        {options.conceptual_provider}{" "}
        {options.conceptual_kind === "simulation" ? "simulation" : "evaluation"}
        .
      </p>
      <form
        className="mt-6 space-y-6"
        onSubmit={(e) => {
          e.preventDefault();
          onStart({
            category: category || null,
            difficulty: difficulty || null,
            question_types: types,
            question_count: count,
          });
        }}
      >
        <fieldset disabled={busy} className="grid gap-5 sm:grid-cols-3">
          <legend className="sr-only">Question selection</legend>
          <SelectField
            label="Assessment category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All categories</option>
            {[...new Set(options.inventory.map((i) => i.category))]
              .sort()
              .map((c) => (
                <option key={c}>{c}</option>
              ))}
          </SelectField>
          <SelectField
            label="Assessment difficulty"
            value={difficulty}
            onChange={(e) =>
              setDifficulty(
                e.target.value === "easy" ||
                  e.target.value === "medium" ||
                  e.target.value === "hard"
                  ? e.target.value
                  : "",
              )
            }
          >
            <option value="">All difficulties</option>
            {["easy", "medium", "hard"].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </SelectField>
          <InputField
            label="Number of questions"
            type="number"
            min={1}
            max={options.max_questions}
            required
            value={countText}
            onChange={(e) => setCount(e.target.value)}
          />
        </fieldset>
        <fieldset disabled={busy} className="space-y-3">
          <legend className="mb-3 text-sm font-medium">Question formats</legend>
          {assessmentTypes.map((type) => (
            <label key={type} className="flex items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={types.includes(type)}
                onChange={(e) =>
                  setTypes(
                    e.target.checked
                      ? [...types, type]
                      : types.filter((t) => t !== type),
                  )
                }
                className="accent-primary mt-0.5 size-4 shrink-0"
              />
              {assessmentTypeLabel[type]}
            </label>
          ))}
        </fieldset>
        <p role="status" className="text-sm text-muted">
          {available} published questions match these filters. Request up to{" "}
          {Math.min(available, options.max_questions)}.
        </p>
        <Button
          type="submit"
          disabled={
            busy ||
            !types.length ||
            !Number.isInteger(count) ||
            count < 1 ||
            count > available ||
            count > options.max_questions
          }
        >
          {busy ? "Starting…" : "Start assessment"}
        </Button>
      </form>
    </section>
  );
}
