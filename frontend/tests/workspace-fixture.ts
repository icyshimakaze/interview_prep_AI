import type { Dashboard } from "@/lib/api/workspace";

export const emptyAccount: Dashboard = {
  mode: "account",
  data_label: "Your account",
  expires_at: null,
  profile: null,
  resumes: [],
  targets: [],
  assessments: [],
  interviews: [],
  roadmap_items: [],
  progress: [],
};

export const workspaceFixture: Dashboard = {
  mode: "demo",
  data_label: "Fictional demo candidate · simulated history",
  expires_at: "2026-10-13T00:00:00Z",
  profile: {
    id: "00000000-0000-4000-8000-000000000001",
    display_name: "Aarav Rao (fictional)",
    target_role: "Junior Backend Engineer",
    experience_band: "entry",
    timezone: "Asia/Kolkata",
    weekly_minutes: 240,
    revision: 1,
    education: null,
    graduation_year: null,
    interests: [],
    interview_date: null,
  },
  resumes: [
    {
      id: "resume-1",
      label: "Fictional sample resume",
      evidence: ["Fictional library API project"],
    },
  ],
  targets: [
    {
      id: "target-1",
      title: "Backend Engineer",
      organization: "Fictional company",
      description: "A fictional target job",
      source_url: null,
      notes: null,
      priority: "normal",
      status: "saved",
      revision: 1,
    },
  ],
  assessments: [
    {
      id: "attempt-1",
      title: "Simulated diagnostic",
      completed_at: "2026-10-10T00:00:00Z",
      answered: 2,
      correct: 1,
      result_kind: "simulation",
    },
  ],
  interviews: [
    {
      id: "interview-1",
      completed_at: "2026-10-11T00:00:00Z",
      status: "completed",
      feedback: ["Simulated feedback; no AI evaluation."],
      result_kind: "simulation",
    },
  ],
  roadmap_items: [
    {
      id: "task-1",
      title: "Practice SQL joins",
      status: "planned",
      estimated_minutes: 45,
    },
  ],
  progress: [
    {
      event_type: "assessment_completed",
      occurred_at: "2026-10-10T00:00:00Z",
      result_kind: "simulation",
    },
  ],
};
