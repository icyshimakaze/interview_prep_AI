import type { Plan, Roadmap, Progress } from "@/lib/api/planning";

export const at = "2026-10-20T10:00:00Z";
export function plan(): Plan {
  return {
    id: "plan",
    revision: 2,
    title: "Preparation plan",
    status: "active",
    policy_version: "personal-roadmap-v1",
    created_at: at,
    weekly_minutes: 120,
    interview_date: null,
    starts_on: "2026-10-20",
    target_id: null,
    target_priority: null,
    notices: [],
    items: [
      {
        id: "task",
        topic: "SQL",
        reason: "A reviewed response needs practice.",
        priority: "high",
        objective: "Correct one gap.",
        activity: "Work an example and take a fresh assessment.",
        estimated_minutes: 60,
        scheduled_on: "2026-10-20",
        status: "planned",
        completed_at: null,
      },
    ],
  };
}
export function roadmap(): Roadmap {
  return {
    mode: "account",
    current: plan(),
    history: [],
    targets: [],
    weekly_minutes: 120,
    interview_date: null,
    notices: [],
  };
}
export function progress(): Progress {
  return {
    policy_version: "progress-analytics-v1",
    mode: "account",
    generated_at: at,
    assessment_chart_available: false,
    assessments: [],
    categories: [],
    interview_series: [],
    excluded_interview_evaluations: 0,
    frequently_missed: [],
    roadmap: {
      current_total: 1,
      current_completed: 0,
      historical_items: 0,
      historical_completed: 0,
      completion_events: 0,
    },
    recent_sessions: [],
    validated_strengths: [],
    requires_validation: [],
    notices: [],
  };
}
