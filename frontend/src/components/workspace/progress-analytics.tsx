"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import { DataTable } from "@/components/ui/table";
import type { PlanningApi, Progress } from "@/lib/api/planning";
import { SectionHeader } from "./section-header";
import { displayDate } from "./history-view";

function Trend({
  title,
  points,
  maximum,
}: {
  title: string;
  points: { at: string; value: number }[];
  maximum: number;
}) {
  if (
    points.length < 3 ||
    new Set(points.map((p) => p.at.slice(0, 10))).size < 3
  )
    return null;
  const times = points.map((p) => Date.parse(p.at)),
    first = Math.min(...times),
    span = Math.max(...times) - first;
  if (!Number.isFinite(span) || span <= 0) return null;
  const coordinates = points
    .map(
      (p, i) =>
        `${30 + (((times[i] ?? first) - first) / span) * 400},${120 - (p.value / maximum) * 100}`,
    )
    .join(" ");
  return (
    <figure className="my-4 border-y border-line bg-surface p-4">
      <svg
        viewBox="0 0 460 155"
        role="img"
        aria-label={title}
        className="w-full max-w-2xl"
      >
        <title>{title}</title>
        <path
          d="M30 20V120H430"
          fill="none"
          stroke="currentColor"
          opacity="0.35"
        />
        <text x="2" y="25" fontSize="11" fill="currentColor">
          {maximum}
        </text>
        <text x="10" y="122" fontSize="11" fill="currentColor">
          0
        </text>
        <polyline
          points={coordinates}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
        <text x="30" y="145" fontSize="11" fill="currentColor">
          {points[0]?.at.slice(0, 10)}
        </text>
        <text
          x="430"
          y="145"
          textAnchor="end"
          fontSize="11"
          fill="currentColor"
        >
          {points.at(-1)?.at.slice(0, 10)}
        </text>
      </svg>
      <figcaption className="mt-2 text-sm text-muted">
        {title}. UTC dates; recorded values and sample sizes appear in the table
        below.
      </figcaption>
    </figure>
  );
}

function Evidence({
  items,
  empty,
}: {
  items: Progress["validated_strengths"];
  empty: string;
}) {
  return items.length ? (
    <ul className="divide-y divide-line border-y border-line">
      {items.map((s, i) => (
        <li className="py-4" key={`${s.topic}-${i}`}>
          <h3 className="font-semibold">{s.topic}</h3>
          <p className="mt-2">{s.description}</p>
          <p className="mt-2 text-sm text-muted">
            {s.source_count} eligible result sources in the inspected window.
          </p>
        </li>
      ))}
    </ul>
  ) : (
    <p className="text-muted">{empty}</p>
  );
}

export function ProgressReport({ data }: { data: Progress }) {
  const objective = data.assessments.filter((a) => a.graded > 0);
  return (
    <div className="space-y-8 text-sm leading-7">
      {data.mode === "demo" && (
        <p className="text-muted">
          Simulated history does not establish real strengths.
        </p>
      )}
      <section>
        <h2 className="section-title">Assessment performance over time</h2>
        <p className="mt-2 text-sm text-muted">
          Objective accuracy: correct submitted deterministic responses / graded
          objective responses. Written answers, skips and simulations are
          excluded. Question mix and difficulty may vary.
        </p>
        {!objective.length ? (
          <p className="mt-4">
            No completed assessments with reviewed objective grades yet.
          </p>
        ) : (
          <>
            {data.assessment_chart_available ? (
              <Trend
                title="Recorded objective assessment accuracy (%)"
                maximum={100}
                points={objective.flatMap((p) =>
                  p.percent === null ? [] : [{ at: p.at, value: p.percent }],
                )}
              />
            ) : (
              <p className="my-4 text-sm">
                More history is needed for a chart: at least three comparable
                sessions on three distinct UTC dates.
              </p>
            )}
            <DataTable
              caption="Recorded assessment accuracy"
              headers={[
                "Completed (UTC)",
                "Correct / graded",
                "Accuracy",
                "Excluded responses",
              ]}
            >
              {data.assessments.map((a) => (
                <tr key={a.id}>
                  <td>{displayDate(a.at)}</td>
                  <td>
                    {a.correct} / {a.graded}
                  </td>
                  <td>
                    {a.percent === null ? "Not assessed" : `${a.percent}%`}
                  </td>
                  <td>{a.excluded}</td>
                </tr>
              ))}
            </DataTable>
          </>
        )}
      </section>
      <section>
        <h2 className="section-title mb-4">Category performance</h2>
        {!data.categories.length ? (
          <p>No eligible objective category results yet.</p>
        ) : (
          <DataTable
            caption="Objective responses by category"
            headers={["Category", "Correct / graded", "Recorded accuracy"]}
          >
            {data.categories.map((c) => (
              <tr key={c.category}>
                <td>{c.category}</td>
                <td>
                  {c.correct} / {c.graded}
                </td>
                <td>{c.percent === null ? "Not assessed" : `${c.percent}%`}</td>
              </tr>
            ))}
          </DataTable>
        )}
      </section>
      <section className="space-y-4">
        <h2 className="section-title">Interview evaluation trends</h2>
        <p className="text-sm text-muted">
          Recorded rubric means on a 0–4 scale. Each series uses matching
          provider, model, version, profile and assessed dimensions. Model
          ratings require independent validation.
        </p>
        {!data.interview_series.length && (
          <p>
            No comparable scored rubric evaluations yet. Unscored and simulated
            practice still appears in recent sessions.
          </p>
        )}
        {data.interview_series.map((s) => (
          <article className="border-t border-line py-4" key={s.key}>
            <h3 className="font-semibold">
              {s.provider || s.kind} · {s.model ?? "No model"} · {s.profile}
            </h3>
            <p className="mt-2 text-sm">{s.label}</p>
            <p className="mt-1 text-xs text-muted">
              {s.provider_version} · {s.rubric_version} ·{" "}
              {s.assessed_dimensions.join(", ")}
            </p>
            {s.chart_available ? (
              <Trend
                title="Recorded interview rubric ratings (0–4)"
                maximum={4}
                points={s.points.map((p) => ({ at: p.at, value: p.mean }))}
              />
            ) : (
              <p className="my-3 text-sm">
                Insufficient comparable history for a chart.
              </p>
            )}
            <DataTable
              caption="Recorded interview ratings"
              headers={["Completed (UTC)", "Mean rating / 4", "Rated answers"]}
            >
              {s.points.map((p) => (
                <tr key={p.session_id}>
                  <td>{displayDate(p.at)}</td>
                  <td>{p.mean}</td>
                  <td>{p.answers}</td>
                </tr>
              ))}
            </DataTable>
          </article>
        ))}
        <p className="text-sm text-muted">
          {data.excluded_interview_evaluations} latest evaluations excluded from
          numeric trends (simulation, unavailable or incompatible scoring).
        </p>
      </section>
      <section className="space-y-3">
        <h2 className="section-title">Roadmap completion</h2>
        <p>
          {data.roadmap.current_completed} of {data.roadmap.current_total}{" "}
          current tasks completed.
        </p>
        <p>
          {data.roadmap.historical_completed} completed of{" "}
          {data.roadmap.historical_items} preserved historical task records.
        </p>
        <p className="text-sm text-muted">
          {data.roadmap.completion_events} recorded completion events, including
          recompletions after reopening. Task completion records preparation
          activity.
        </p>
      </section>
      <section className="space-y-4">
        <h2 className="section-title">Frequently missed concepts</h2>
        <p className="text-sm text-muted">
          Repeated observations in at least two distinct sessions. Model
          suggestions remain separate from objectively incorrect responses.
        </p>
        {!data.frequently_missed.length ? (
          <p>No repeated gaps established by the available history.</p>
        ) : (
          <ul className="space-y-3">
            {data.frequently_missed.map((m) => (
              <li
                className="border-t border-line py-4"
                key={`${m.basis}:${m.concept}`}
              >
                <strong>{m.concept}</strong>
                <p>
                  {m.basis === "model_assisted"
                    ? "Model-suggested gap; verify independently"
                    : "Incorrect objective response"}{" "}
                  · {m.occurrences} observations across {m.sessions} sessions.
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="space-y-4">
        <h2 className="section-title">Validated strengths in tested scope</h2>
        <Evidence
          items={data.validated_strengths}
          empty="No strengths meet the validation policy yet. This does not establish inability."
        />
      </section>
      <section className="space-y-4">
        <h2 className="section-title">Areas requiring further validation</h2>
        <Evidence
          items={data.requires_validation}
          empty="No additional mapped context is available. Add a target, resume evidence or practice results to identify areas to validate."
        />
      </section>
      <section className="space-y-4">
        <h2 className="section-title">Recent sessions</h2>
        {!data.recent_sessions.length ? (
          <p>No saved assessment, interview or Project Defense sessions yet.</p>
        ) : (
          <DataTable
            caption="Recent persisted sessions"
            headers={["Session", "Activity", "Status", "Recorded (UTC)"]}
          >
            {data.recent_sessions.map((s) => (
              <tr key={`${s.channel}:${s.id}`}>
                <td>{s.title}</td>
                <td>{s.channel.replaceAll("_", " ")}</td>
                <td>{s.status.replaceAll("_", " ")}</td>
                <td>{displayDate(s.at)}</td>
              </tr>
            ))}
          </DataTable>
        )}
      </section>
      <details>
        <summary className="cursor-pointer font-medium">
          Data coverage and interpretation
        </summary>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted">
          {data.notices.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
        <p className="mt-3 text-xs">
          {data.policy_version} · Calculated{" "}
          {new Date(data.generated_at).toLocaleString()}
        </p>
      </details>
    </div>
  );
}

export function ProgressAnalytics({ api }: { api: PlanningApi }) {
  const [data, setData] = useState<Progress | null>(null),
    [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    void api
      .progress()
      .then((r) => {
        if (active) {
          setData(r);
          setError("");
        }
      })
      .catch((e: unknown) => {
        if (active)
          setError(e instanceof Error ? e.message : "Progress could not load.");
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [api, refresh]);
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Progress analytics"
        eyebrow="Evidence over time"
        description="Explore recorded performance, preparation activity and areas that still need validation."
      />
      {error && (
        <ErrorDisplay
          message={error}
          busy={busy}
          onRetry={() => {
            setBusy(true);
            setRefresh((n) => n + 1);
          }}
        />
      )}
      {!data && !error && (
        <WorkspaceSkeleton label="Loading persisted progress…" />
      )}
      {data && (
        <>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              setRefresh((n) => n + 1);
            }}
          >
            Refresh progress
          </Button>
          {busy && <p role="status">Refreshing saved results…</p>}
          <ProgressReport data={data} />
        </>
      )}
    </div>
  );
}
