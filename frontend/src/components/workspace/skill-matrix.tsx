"use client";

import { useEffect, useState } from "react";
import type { SkillApi, SkillMatrix } from "@/lib/api/skills";
import { Button } from "@/components/ui/button";
import { DataTable, Badge } from "@/components/ui/table";
import {
  EmptyState,
  ErrorDisplay,
  WorkspaceSkeleton,
} from "@/components/ui/states";
import { SectionHeader } from "./section-header";

export function SkillMatrixTable({ matrix }: { matrix: SkillMatrix }) {
  return (
    <>
      <p className="mb-3 text-sm leading-6 text-muted">
        Resume mentions are context. Eligible practice results can validate
        skills only in their tested scope.
      </p>
      <details className="mb-6 text-sm leading-6 text-muted">
        <summary className="min-h-11 py-2 text-accent">
          Evidence rules and preparation order
        </summary>
        <p className="mt-2">
          Preparation order: Required, Preferred, Mentioned, then Low relevance.
          Within each group, practice comes before validation, then maintenance.
          Ties use skill name. Strong evidence covers at least two tested
          concepts; it does not imply mastery.
        </p>
        {matrix.notices?.map((note) => (
          <p key={note} className="mt-2">
            {note}
          </p>
        ))}
      </details>
      {!matrix.rows.length ? (
        <EmptyState
          icon="questions"
          title="No skill evidence yet"
          description="Add profile interests, review a resume, or select a saved target job. Missing evidence does not mean missing ability."
        />
      ) : (
        <DataTable
          caption="Skill evidence matrix, in preparation priority order"
          headers={[
            "Skill / importance",
            "Resume evidence",
            "Demonstrated competence",
            "Next step / sources",
          ]}
        >
          {matrix.rows.map((row) => (
            <tr key={row.key}>
              <th scope="row" className="min-w-36">
                <span className="block font-semibold">{row.name}</span>
                <Badge>{row.importance}</Badge>
              </th>
              <td>
                <p>{row.resume_state}</p>
              </td>
              <td>
                <Badge
                  tone={
                    row.competence_state === "Needs additional practice"
                      ? "amber"
                      : "neutral"
                  }
                >
                  {row.competence_state}
                </Badge>
                {row.assessment_validated && (
                  <p className="mt-2 text-xs">
                    Assessment validated in tested scope.
                  </p>
                )}
              </td>
              <td>
                <p className="font-semibold">{row.action}</p>
                <details className="mt-3 max-w-lg min-w-48 break-words whitespace-normal">
                  <summary className="cursor-pointer text-accent">
                    Why this priority? Sources for {row.name}
                  </summary>
                  <ul className="my-3 list-disc space-y-2 pl-5 text-sm">
                    {row.explanation.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                  <ul className="space-y-4 text-xs leading-6">
                    {row.sources.map((source) => (
                      <li key={source.id} className="border-t border-line pt-3">
                        <p className="font-semibold capitalize">
                          {source.kind} · {source.review}
                        </p>
                        <p>{source.detail}</p>
                        {source.occurred_at && (
                          <p>
                            Recorded:{" "}
                            <time dateTime={source.occurred_at}>
                              {source.occurred_at.slice(0, 10)}
                            </time>
                          </p>
                        )}
                        {source.concept && (
                          <p>Tested concept: {source.concept}</p>
                        )}
                        {(source.kind === "assessment" ||
                          source.kind === "interview") && (
                          <p>
                            {source.eligible
                              ? `Eligible result: ${source.outcome === "met" ? "criteria met" : "practice needed"}. Latest result per channel and concept determines the state.`
                              : "Excluded from validation."}
                          </p>
                        )}
                        <p className="break-all text-muted">
                          Source: {source.id}
                        </p>
                      </li>
                    ))}
                  </ul>
                </details>
              </td>
            </tr>
          ))}
        </DataTable>
      )}
    </>
  );
}

export function SkillMatrixView({ api }: { api: SkillApi }) {
  const [target, setTarget] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{
    target: string | null;
    attempt: number;
    data?: SkillMatrix;
    error?: string;
  } | null>(null);
  const [targets, setTargets] = useState<SkillMatrix["targets"]>([]);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    void api
      .read(target, controller.signal)
      .then((data) => {
        if (active) {
          setState({ target, attempt, data });
          setTargets(data.targets);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setState({
            target,
            attempt,
            error:
              reason instanceof Error
                ? reason.message
                : "Skill evidence could not load.",
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api, target, attempt]);
  const current =
    state?.target === target && state?.attempt === attempt ? state : null;
  return (
    <>
      <SectionHeader
        title="Skill Matrix"
        eyebrow="Evidence, explained"
        description="See what your resume mentions, what practice demonstrates, and what to prepare next. No readiness percentages."
      />
      <div className="mb-6 flex flex-wrap items-end gap-4">
        <label className="flex min-w-0 flex-col gap-2 text-sm font-medium">
          Target job
          <select
            className="input"
            value={target ?? ""}
            onChange={(event) => setTarget(event.target.value || null)}
          >
            <option value="">No target selected</option>
            {targets.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        <Button
          variant="outline"
          onClick={() => setAttempt((value) => value + 1)}
          disabled={!current}
        >
          Refresh evidence
        </Button>
      </div>
      {!current && <WorkspaceSkeleton label="Loading skill evidence…" />}
      {current?.error && (
        <ErrorDisplay
          message={current.error}
          onRetry={() => setAttempt((value) => value + 1)}
        />
      )}
      {current?.data && <SkillMatrixTable matrix={current.data} />}
    </>
  );
}
