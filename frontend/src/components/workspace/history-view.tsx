"use client";

import { useState } from "react";
import type { Dashboard } from "@/lib/api/workspace";
import { Button, ButtonLink } from "@/components/ui/button";
import { SelectField } from "@/components/ui/field";
import { EmptyState } from "@/components/ui/states";
import { Badge, DataTable } from "@/components/ui/table";
import { sectionHref } from "./navigation";
import { SectionHeader } from "./section-header";

export function displayDate(value: string | null): string {
  if (!value) return "Not completed";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : new Intl.DateTimeFormat("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(date);
}

function ResultKind({ kind }: { kind: string | null }) {
  return (
    <Badge tone={kind === "simulation" ? "amber" : "neutral"}>
      {kind === "simulation"
        ? "Simulated example"
        : (kind?.replaceAll("_", " ") ?? "Recorded activity")}
    </Badge>
  );
}

export function AssessmentsView({ data }: { data: Dashboard }) {
  return (
    <>
      <SectionHeader
        title="Assessments"
        eyebrow="Practice with purpose"
        description="Review attempts with their recorded results and evaluation method."
        unavailable={!data.assessments.length}
      />
      {!data.assessments.length ? (
        <EmptyState
          icon="assessments"
          title="No assessment attempts yet."
          description="Your completed assessments will appear here with the questions answered and how they were evaluated. Starting a real assessment is not available yet."
          action={
            <ButtonLink href="/demo/assessments" variant="outline">
              Explore sample results
            </ButtonLink>
          }
          note="No score is calculated until an assessment has been completed."
        />
      ) : (
        <DataTable
          caption="Assessment history"
          headers={["Assessment", "Result", "Evaluation", "Completed (UTC)"]}
        >
          {data.assessments.map((attempt) => (
            <tr key={attempt.id}>
              <td className="min-w-48 font-medium">{attempt.title}</td>
              <td className="min-w-44">
                {attempt.correct} correct of {attempt.answered} answered
              </td>
              <td>
                <ResultKind kind={attempt.result_kind} />
              </td>
              <td className="whitespace-nowrap">
                {displayDate(attempt.completed_at)}
              </td>
            </tr>
          ))}
        </DataTable>
      )}
    </>
  );
}

export function InterviewsView({ data }: { data: Dashboard }) {
  return (
    <>
      <SectionHeader
        title="Interviews"
        eyebrow="Talk through your thinking"
        description="Keep interview feedback close to the session it came from."
        unavailable={!data.interviews.length}
      />
      {!data.interviews.length ? (
        <EmptyState
          icon="interviews"
          title="Your first conversation is ahead."
          description="No interviews yet. This space will hold your sessions and feedback. Starting an interview is still in development."
          action={
            <ButtonLink href="/demo/interviews" variant="outline">
              Review a sample interview
            </ButtonLink>
          }
        />
      ) : (
        <div className="space-y-6">
          {data.interviews.map((interview, index) => (
            <article
              key={interview.id}
              className="border-y border-line bg-surface p-6 sm:p-8"
            >
              <div className="flex flex-wrap justify-between gap-4">
                <div>
                  <h2 className="section-title">
                    {interview.result_kind === "simulation"
                      ? "Simulated interview"
                      : "Interview"}{" "}
                    {index + 1}
                  </h2>
                  <p className="mt-2 text-xs text-muted">
                    {interview.status.replaceAll("_", " ")} ·{" "}
                    {displayDate(interview.completed_at)} (UTC)
                  </p>
                </div>
                <ResultKind kind={interview.result_kind} />
              </div>
              <h3 className="mt-8 text-sm font-semibold">Recorded feedback</h3>
              <ul className="mt-3 space-y-4">
                {interview.feedback.map((feedback, i) => (
                  <li
                    key={i}
                    className="border-l-2 border-line pl-4 text-sm leading-7 text-muted"
                  >
                    {feedback}
                  </li>
                ))}
              </ul>
              {!interview.feedback.length && (
                <p className="mt-4 text-sm text-muted">
                  No feedback is available for this session.
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export function RoadmapView({
  data,
  busy,
  onComplete,
}: {
  data: Dashboard;
  busy?: boolean;
  onComplete?: (id: string) => void;
}) {
  const [filter, setFilter] = useState("all");
  const items = data.roadmap_items.filter(
    (item) =>
      filter === "all" ||
      (filter === "completed"
        ? item.status === "completed"
        : item.status !== "completed"),
  );
  return (
    <>
      <SectionHeader
        title="Roadmap"
        eyebrow="One step at a time"
        description="Keep specific practice tasks in view and record the work you finish."
        unavailable={!data.roadmap_items.length}
      />
      {!data.roadmap_items.length ? (
        <EmptyState
          icon="roadmap"
          title="A plan starts with your direction."
          description="No roadmap tasks yet. Save your target role and weekly study budget first. Personal roadmap creation is still in development."
          action={
            <ButtonLink href={sectionHref(data.mode, "settings")}>
              Review your study budget
            </ButtonLink>
          }
        />
      ) : (
        <>
          <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
            <p className="text-sm text-muted" role="status">
              {items.length} of {data.roadmap_items.length} tasks shown
              {busy ? " · Saving task…" : ""}
            </p>
            <div className="w-full sm:w-48">
              <SelectField
                label="Task status"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
              >
                <option value="all">All tasks</option>
                <option value="open">To do</option>
                <option value="completed">Completed</option>
              </SelectField>
            </div>
          </div>
          {items.length ? (
            <ul className="divide-y divide-line border-y border-line bg-surface">
              {items.map((item) => (
                <li
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-5 p-5 sm:p-6"
                >
                  <div className="min-w-0 flex-1 basis-56">
                    <h2 className="text-sm font-semibold">{item.title}</h2>
                    <p className="mt-2 text-xs leading-6 text-muted">
                      {item.estimated_minutes} minutes ·{" "}
                      {item.status.replaceAll("_", " ")}
                      {data.mode === "demo" && " · Demo task"}
                    </p>
                  </div>
                  {item.status === "completed" ? (
                    <Badge tone="green">Completed</Badge>
                  ) : onComplete ? (
                    <Button
                      variant="outline"
                      disabled={busy}
                      aria-label={`Mark complete: ${item.title}`}
                      onClick={() => onComplete(item.id)}
                    >
                      Mark complete
                    </Button>
                  ) : (
                    <Badge>{item.status.replaceAll("_", " ")}</Badge>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon="roadmap"
              title="No tasks match this view."
              description="Try another status to see the rest of your roadmap."
              action={
                <Button variant="outline" onClick={() => setFilter("all")}>
                  Show all tasks
                </Button>
              }
            />
          )}
        </>
      )}
    </>
  );
}

export function ProgressView({ data }: { data: Dashboard }) {
  return (
    <>
      <SectionHeader
        title="Progress"
        eyebrow="A record of your work"
        description="Review recorded preparation activity. Every entry keeps its source and evaluation context."
      />
      {!data.progress.length ? (
        <EmptyState
          icon="progress"
          title="Progress starts with practice."
          description="No progress events yet. Completed preparation will appear here. There is no readiness percentage or interview prediction before you have evidence to review."
          action={
            <ButtonLink
              href={sectionHref(data.mode, "settings")}
              variant="outline"
            >
              Set your preparation direction
            </ButtonLink>
          }
        />
      ) : (
        <>
          <h2 className="section-title mb-5">Activity history</h2>
          <DataTable
            caption="Preparation activity"
            headers={["Activity", "Source", "Recorded (UTC)"]}
          >
            {data.progress.map((event, index) => (
              <tr key={`${event.occurred_at}-${index}`}>
                <td className="min-w-48 capitalize">
                  {event.event_type.replaceAll("_", " ")}
                </td>
                <td>
                  <ResultKind kind={event.result_kind} />
                </td>
                <td className="whitespace-nowrap">
                  {displayDate(event.occurred_at)}
                </td>
              </tr>
            ))}
          </DataTable>
          <p className="mt-5 text-xs leading-6 text-muted">
            Recorded activity describes work completed. It is not a prediction
            of hiring outcomes.
          </p>
        </>
      )}
    </>
  );
}
