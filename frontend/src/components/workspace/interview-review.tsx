import { EvaluationFeedback } from "./evaluation-feedback";
import type { InterviewReview } from "@/lib/api/interviews";

export function InterviewReviewView({ review }: { review: InterviewReview }) {
  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-line bg-surface p-5">
        <h2 className="section-title">
          {review.review_status === "provisional"
            ? "Preparing final review"
            : "Interview review"}
        </h2>
        <p className="mt-3 text-sm leading-6">
          {review.session.end_reason === "full"
            ? "Full session"
            : "Partial session"}{" "}
          · {review.session.progress.answered} answered ·{" "}
          {review.session.progress.skipped} skipped · {review.unasked_main}{" "}
          unasked main questions.
        </p>
        <p className="mt-2 text-sm">
          {review.evaluated_main} of {review.submitted_main} submitted main
          answers evaluated. {review.session.progress.evaluation_failed}{" "}
          evaluations unavailable.
        </p>
        <p className="mt-3 text-sm text-muted">
          {review.session.provider.disclosure}
        </p>
        {review.notices.map((n) => (
          <p className="mt-2 text-xs leading-5 text-muted" key={n}>
            {n}
          </p>
        ))}
      </section>
      {review.turns.map(
        ({ turn, evaluation, expected_concepts, rubric, rationale }) => (
          <article
            className="rounded-xl border border-line bg-surface p-5"
            key={turn.id}
          >
            <h3 className="font-semibold">
              {turn.parent_id
                ? `Follow-up to main ${turn.main_ordinal ?? "question"}`
                : `Main question ${turn.main_ordinal ?? turn.sequence}`}
            </h3>
            <p className="mt-3 text-sm leading-6 whitespace-pre-wrap">
              {turn.prompt}
            </p>
            <p className="mt-2 text-xs text-muted">
              {turn.parent_id && turn.status === "evaluated"
                ? "answered, unscored"
                : turn.status.replaceAll("_", " ")}{" "}
              · {Math.floor(turn.answering_ms / 1000)} seconds recorded
              answering time (may include time away).
            </p>
            <h4 className="mt-4 text-sm font-semibold">
              {turn.status === "unanswered"
                ? "Unsubmitted draft"
                : "Your response"}
            </h4>
            <p className="mt-2 text-sm leading-6 whitespace-pre-wrap">
              {turn.answer_text || "No response."}
            </p>
            {evaluation && (
              <div className="bg-subtle mt-4 rounded-lg p-4 text-sm leading-6">
                <p>
                  {evaluation.evaluation
                    ? "Structured feedback"
                    : evaluation.status === "completed"
                      ? evaluation.score === null ||
                        evaluation.score_scale_max === null
                        ? "Historical feedback; no aggregate score was recorded."
                        : `${evaluation.kind === "simulation" ? "Simulated lexical" : "AI-assisted"} score: ${evaluation.score} / ${evaluation.score_scale_max}`
                      : evaluation.status === "not_evaluable"
                        ? "Not scored"
                        : evaluation.status === "failed"
                          ? `Evaluation unavailable (${evaluation.error_code ?? "unavailable"}). Your answer is retained.`
                          : "Evaluation pending. Your answer is retained."}
                </p>
                {evaluation.evaluation && (
                  <EvaluationFeedback evaluation={evaluation.evaluation} />
                )}
                {!evaluation.evaluation && evaluation.feedback && (
                  <p className="mt-2 whitespace-pre-wrap">
                    {evaluation.feedback}
                  </p>
                )}
                {evaluation.provider && (
                  <p className="mt-2 text-xs text-muted">
                    {evaluation.provider}
                    {evaluation.model ? ` · ${evaluation.model}` : ""} ·{" "}
                    {evaluation.prompt_version ?? "Original prompt version"} ·{" "}
                    {evaluation.provider_version ?? "Original provider version"}
                    {evaluation.evaluated_at &&
                      ` · ${new Date(evaluation.evaluated_at).toLocaleString()}`}
                  </p>
                )}
              </div>
            )}
            {!!expected_concepts.length && (
              <details className="mt-4 text-sm">
                <summary className="cursor-pointer font-medium">
                  Review concepts and criteria
                </summary>
                <ul className="mt-3 list-disc space-y-2 pl-5">
                  {[...expected_concepts, ...rubric].map((c, i) => (
                    <li key={`${i}:${c}`}>{c}</li>
                  ))}
                </ul>
              </details>
            )}
            {rationale && (
              <p className="mt-3 text-xs text-muted">{rationale}</p>
            )}
          </article>
        ),
      )}
    </div>
  );
}
