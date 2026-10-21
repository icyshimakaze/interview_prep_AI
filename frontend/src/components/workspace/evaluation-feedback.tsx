import {
  dimensionLabels,
  scoreMeanings,
  type AnswerEvaluation,
} from "@/lib/api/evaluation";

export function EvaluationFeedback({
  evaluation: e,
}: {
  evaluation: AnswerEvaluation;
}) {
  const simulated = e.score_basis === "lexical_coverage";
  return (
    <section
      aria-label="Structured answer feedback"
      className="mt-4 space-y-4 text-sm leading-6"
    >
      <p className="font-medium">
        {simulated
          ? "Deterministic demo simulation"
          : "AI-assisted feedback — requires human review"}{" "}
        · {e.rubric_version}
      </p>
      <p>{e.overall_feedback}</p>
      <p>
        {simulated
          ? `Lexical coverage: ${e.score} / 4. This counts word overlap, not correctness.`
          : `Rubric summary: ${e.score} / 4. Rounded-down mean of assessed criteria; not a readiness prediction.`}
      </p>
      {simulated && (
        <p>
          Coverage bands: 0 = below 25%; 1 = 25–49%; 2 = 50–74%; 3 = 75–99%; 4 =
          100%. With no expected concepts, 0 means no coverage evidence. Other
          criteria are not assessed.
        </p>
      )}
      <div>
        <h4 className="font-semibold">Strengths</h4>
        {e.strengths.length ? (
          <ul className="list-disc pl-5">
            {e.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        ) : (
          <p>No supported strengths identified by this evaluator.</p>
        )}
      </div>
      <div>
        <h4 className="font-semibold">Improvements</h4>
        <ul className="list-disc pl-5">
          {e.improvements.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="font-semibold">Missing concepts</h4>
        {e.missing_concepts.length ? (
          <ul className="list-disc pl-5">
            {e.missing_concepts.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        ) : (
          <p>
            No missing concepts flagged. This does not establish correctness.
          </p>
        )}
      </div>
      <div>
        <h4 className="font-semibold">Recommended answer structure</h4>
        <ol className="list-decimal pl-5">
          {e.recommended_answer_structure.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </div>
      <div>
        <h4 className="font-semibold">Potential follow-up</h4>
        <p>{e.potential_followup}</p>
      </div>
      <div>
        <h4 className="font-semibold">Rubric results</h4>
        <dl className="mt-2 space-y-3">
          {e.rubric_results.map((r) => (
            <div key={r.dimension}>
              <dt className="font-medium">
                {dimensionLabels[r.dimension]} ·{" "}
                {r.score === null
                  ? "Not assessed / not applicable"
                  : `${r.score} / 4${simulated ? " · lexical proxy" : ""}`}
              </dt>
              <dd>
                {r.explanation}
                {r.score !== null && !simulated && (
                  <p className="text-muted">{scoreMeanings[r.score]}</p>
                )}
              </dd>
            </div>
          ))}
        </dl>
      </div>
      <details>
        <summary className="cursor-pointer font-medium">
          What each rubric score means
        </summary>
        <ol start={0} className="mt-2 list-decimal pl-5">
          {scoreMeanings.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
        <p>
          Null means not assessed or not applicable, with the reason above.
          These anchors apply to rubric judgments; demo lexical coverage uses
          its own bands above.
        </p>
      </details>
    </section>
  );
}
