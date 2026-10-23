"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorDisplay, WorkspaceSkeleton } from "@/components/ui/states";
import type {
  GeneratePlan,
  Plan,
  PlanningApi,
  Roadmap,
} from "@/lib/api/planning";
import { SectionHeader } from "./section-header";
import { AIReview } from "./ai-review";

function PlanTasks({
  plan,
  busy,
  onChange,
}: {
  plan: Plan;
  busy: boolean;
  onChange: (
    id: string,
    revision: number,
    action: "complete" | "reopen",
  ) => void;
}) {
  return (
    <div className="space-y-4">
      <p>
        {plan.title} · {plan.status} · {plan.weekly_minutes / 60} hours/week ·{" "}
        {plan.policy_version}
      </p>
      <p className="text-sm text-muted">
        Created {new Date(plan.created_at).toLocaleString()}
        {plan.interview_date && ` · Interview date ${plan.interview_date}`}
      </p>
      {plan.notices.length > 0 && (
        <details>
          <summary className="cursor-pointer">Planning assumptions</summary>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-sm">
            {plan.notices.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </details>
      )}
      {!plan.items.length && (
        <p>
          No new tasks for the current evidence. Completed activities remain in
          history; record fresh practice or change your target to generate
          further recommendations.
        </p>
      )}
      <ul className="space-y-4">
        {plan.items.map((i) => (
          <li key={i.id} className="border-t border-line py-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold">{i.topic}</h3>
                <p className="mt-2 text-sm text-muted">
                  {i.priority ? `${i.priority} priority · ` : ""}
                  {i.estimated_minutes} minutes ·{" "}
                  {i.status.replaceAll("_", " ")} ·{" "}
                  {i.scheduled_on
                    ? `Week of ${i.scheduled_on}`
                    : "Queued / not scheduled"}
                </p>
              </div>
              <Button
                disabled={busy}
                variant="outline"
                onClick={() =>
                  onChange(
                    i.id,
                    plan.revision,
                    i.status === "completed" ? "reopen" : "complete",
                  )
                }
              >
                {i.status === "completed" ? "Reopen" : "Mark complete"}:{" "}
                {i.topic}
              </Button>
            </div>
            {i.objective && (
              <p className="mt-4">
                <strong>Objective:</strong> {i.objective}
              </p>
            )}
            {i.activity && (
              <p className="mt-2">
                <strong>Recommended activity:</strong> {i.activity}
              </p>
            )}
            <details className="mt-3">
              <summary className="cursor-pointer font-medium">
                Why this task?
              </summary>
              <p className="mt-2 text-sm leading-6">{i.reason}</p>
            </details>
            {i.completed_at && (
              <p className="mt-2 text-sm text-muted">
                Completed {new Date(i.completed_at).toLocaleString()}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PersonalRoadmap({ api }: { api: PlanningApi }) {
  const [data, setData] = useState<Roadmap | null>(null),
    [error, setError] = useState("");
  const [busy, setBusy] = useState(false),
    [refresh, setRefresh] = useState(0);
  const [target, setTarget] = useState(""),
    [hours, setHours] = useState("4"),
    [date, setDate] = useState("");
  const lock = useRef(false),
    pending = useRef<{ signature: string; body: GeneratePlan } | null>(null);
  useEffect(() => {
    let active = true;
    void api
      .read()
      .then((r) => {
        if (active) {
          setData(r);
          setError("");
          setTarget(
            r.current ? (r.current.target_id ?? "") : (r.targets[0]?.id ?? ""),
          );
          setHours(
            String((r.current?.weekly_minutes ?? r.weekly_minutes) / 60),
          );
          setDate(
            r.current
              ? (r.current.interview_date ?? "")
              : (r.interview_date ?? ""),
          );
        }
      })
      .catch((e: unknown) => {
        if (active)
          setError(e instanceof Error ? e.message : "Roadmap could not load.");
      });
    return () => {
      active = false;
    };
  }, [api, refresh]);
  async function perform(action: () => Promise<Roadmap>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      setData(await action());
      pending.current = null;
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Your saved roadmap could not be updated.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Personal preparation roadmap"
        eyebrow="One step at a time"
        description="Choose a target and time budget. Recommendations explain which saved evidence informed them."
      />
      {error && (
        <ErrorDisplay
          message={error}
          busy={busy}
          onRetry={() => setRefresh((n) => n + 1)}
        />
      )}
      {!data && !error && <WorkspaceSkeleton label="Loading your roadmap…" />}
      {data && (
        <>
          {data.mode === "demo" && (
            <p className="text-sm text-muted">
              Completing a demo task records practice, not verified competence.
            </p>
          )}
          <form
            className="space-y-4 border-y border-line bg-surface p-5 sm:p-6"
            onSubmit={(e) => {
              e.preventDefault();
              const minutes = Number(hours) * 60;
              if (
                !Number.isInteger(minutes) ||
                minutes < 15 ||
                minutes > 10080
              ) {
                setError(
                  "Choose between 0.25 and 168 hours per week, in whole minutes.",
                );
                return;
              }
              const body: GeneratePlan = {
                command_key: "",
                target_id: target || null,
                weekly_minutes: minutes,
                interview_date: date || null,
                expected_id: data.current?.id ?? null,
                expected_revision: data.current?.revision ?? null,
              };
              const signature = JSON.stringify(body);
              if (pending.current?.signature !== signature)
                pending.current = {
                  signature,
                  body: { ...body, command_key: crypto.randomUUID() },
                };
              const request = pending.current.body;
              void perform(() => api.generate(request));
            }}
          >
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="min-w-0 text-sm font-medium">
                Target job
                <select
                  className="input mt-2"
                  value={target}
                  disabled={busy}
                  onChange={(e) => setTarget(e.target.value)}
                >
                  <option value="">General preparation</option>
                  {data.targets.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.title} ({t.priority} priority)
                    </option>
                  ))}
                </select>
              </label>
              <label className="min-w-0 text-sm font-medium">
                Available hours per week
                <input
                  className="input mt-2"
                  type="number"
                  min="0.25"
                  max="168"
                  step="any"
                  required
                  value={hours}
                  disabled={busy}
                  onChange={(e) => setHours(e.target.value)}
                />
              </label>
              <label className="min-w-0 text-sm font-medium">
                Interview date (optional)
                <input
                  className="input mt-2"
                  type="date"
                  value={date}
                  disabled={busy}
                  onChange={(e) => setDate(e.target.value)}
                />
              </label>
            </div>
            <p className="text-sm text-muted">
              Regenerating keeps completed tasks and earlier plans in history.
              Each task explains which saved evidence informed it.
            </p>
            <Button type="submit" disabled={busy}>
              {busy
                ? "Saving roadmap…"
                : data.current
                  ? "Regenerate recommendations"
                  : "Generate roadmap"}
            </Button>
          </form>
          {!data.current && (
            <p>
              No personal roadmap yet. Generate one from your current context
              and time budget.
            </p>
          )}
          {data.current && (
            <section className="space-y-4">
              <h2 className="section-title">Current roadmap</h2>
              {data.mode === "account" && api.ai && (
                <AIReview
                  key={`${data.current.id}:${data.current.revision}`}
                  api={api.ai}
                  resource={`roadmaps/${data.current.id}`}
                  label="Suggest roadmap activities"
                />
              )}
              <PlanTasks
                plan={data.current}
                busy={busy}
                onChange={(...args) => void perform(() => api.change(...args))}
              />
            </section>
          )}
          <section className="space-y-4">
            <h2 className="section-title">Preserved history</h2>
            {!data.history.length && (
              <p>
                Earlier generations will appear here. Regeneration does not
                delete completed work.
              </p>
            )}
            {data.history.map((p) => (
              <details className="border-t border-line py-4" key={p.id}>
                <summary className="cursor-pointer font-medium">
                  {p.title} · {new Date(p.created_at).toLocaleDateString()} ·{" "}
                  {p.items.filter((i) => i.status === "completed").length}{" "}
                  completed
                </summary>
                <div className="mt-4">
                  <PlanTasks
                    plan={p}
                    busy={busy}
                    onChange={(...args) =>
                      void perform(() => api.change(...args))
                    }
                  />
                </div>
              </details>
            ))}
          </section>
          <ul className="space-y-2 text-sm text-muted">
            {data.notices.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
