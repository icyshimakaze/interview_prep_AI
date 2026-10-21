import { EvaluationFeedback } from "./evaluation-feedback";
import type { Assessment } from "@/lib/api/assessments";
import { Badge, DataTable } from "@/components/ui/table";

export function AssessmentReview({ attempt }: { attempt: Assessment }) {
  return (
    <div className="space-y-8">
      <section>
        <h2 className="section-title">Category performance</h2>
        <p className="mt-2 mb-5 text-sm leading-6 text-muted">
          Counts come from this attempt’s actual responses. Objective totals
          include skipped questions. Conceptual points cover answered conceptual
          questions only and remain separate from objective correctness. Mock
          points summarize word overlap; AI-assisted points summarize rubric
          judgments. Read the per-answer explanations below; these totals do not
          measure readiness.
        </p>
        <DataTable
          caption="Category performance"
          headers={[
            "Category",
            "Responses",
            "Objective results",
            "Conceptual feedback",
          ]}
        >
          {attempt.categories.map((c) => (
            <tr key={c.category}>
              <td>{c.category}</td>
              <td>
                {c.answered} answered · {c.skipped} skipped
              </td>
              <td>
                {c.objective_total
                  ? `${c.objective_correct} correct of ${c.objective_total}`
                  : "No deterministic score"}
              </td>
              <td>
                {c.conceptual_max
                  ? `${c.conceptual_score} of ${c.conceptual_max} · ${c.conceptual_kind === "simulation" ? "Mock simulation" : c.conceptual_kind?.replaceAll("_", " ")}`
                  : "No conceptual score"}
              </td>
            </tr>
          ))}
        </DataTable>
      </section>
      <section className="space-y-5" aria-label="Assessment review">
        <h2 className="section-title">Question review</h2>
        {attempt.questions.map((q) => (
          <article
            key={q.id}
            className="min-w-0 rounded-xl border border-line bg-surface p-5"
          >
            <p className="mb-2 text-xs text-muted">
              {q.category} · {q.difficulty}
            </p>
            <h3 className="font-semibold">
              {q.position}. {q.title}
            </h3>
            <p className="mt-3 text-sm leading-7 whitespace-pre-wrap">
              {q.prompt}
            </p>
            <p className="mt-4 text-sm font-medium">Your response</p>
            <p className="mt-2 text-sm break-words whitespace-pre-wrap">
              {q.skipped
                ? "Skipped"
                : q.answer_text ||
                  q.options
                    .filter((o) => q.selected_option_ids.includes(o.id))
                    .map((o) => o.text)
                    .join("; ") ||
                  "No recorded response"}
            </p>
            {q.review && (
              <div className="mt-5 space-y-3 border-t border-line pt-5">
                <Badge
                  tone={
                    q.review.result_kind === "simulation" ? "amber" : "neutral"
                  }
                >
                  {q.skipped
                    ? "Skipped"
                    : q.review.result_kind === "simulation"
                      ? q.review.score === null || q.review.max_score === null
                        ? "Simulated historical record"
                        : `Mock simulation · ${q.review.score} of ${q.review.max_score}`
                      : q.review.is_correct === true
                        ? "Correct"
                        : q.review.is_correct === false
                          ? "Needs practice"
                          : q.review.result_kind?.replaceAll("_", " ") ||
                            "Historical record"}
                </Badge>
                {q.review.metadata?.evaluation && (
                  <EvaluationFeedback
                    evaluation={q.review.metadata.evaluation}
                  />
                )}
                {!q.review.metadata?.evaluation && q.review.feedback && (
                  <p className="text-sm leading-7">{q.review.feedback}</p>
                )}
                {!!q.review.correct_option_ids.length && (
                  <p className="text-sm leading-7">
                    <strong>Expected selections: </strong>
                    {q.options
                      .filter((o) =>
                        q.review?.correct_option_ids.includes(o.id),
                      )
                      .map((o) => o.text)
                      .join("; ")}
                  </p>
                )}
                {!!q.review.accepted_answers.length && (
                  <p className="text-sm">
                    <strong>Accepted answer: </strong>
                    {q.review.accepted_answers.join(" or ")}
                  </p>
                )}
                {!!q.review.expected_concepts.length && (
                  <div>
                    <h4 className="text-sm font-medium">Expected concepts</h4>
                    <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-6">
                      {q.review.expected_concepts.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {q.review.metadata && (
                  <p className="text-xs leading-6 break-words text-muted">
                    {q.review.metadata.provider} ·{" "}
                    {q.review.metadata.provider_version} ·{" "}
                    {q.review.metadata.policy_version} ·{" "}
                    {q.review.metadata.model ?? "No model"} ·{" "}
                    {q.review.metadata.prompt_version ?? "Original prompt"} ·{" "}
                    {q.review.metadata.rubric_version ?? "Original rubric"} ·{" "}
                    {new Date(q.review.metadata.evaluated_at).toLocaleString()}
                  </p>
                )}
              </div>
            )}
          </article>
        ))}
      </section>
    </div>
  );
}
