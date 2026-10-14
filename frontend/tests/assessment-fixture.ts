import { vi } from "vitest";
import type {
  Assessment,
  AssessmentApi,
  AssessmentOptions,
} from "@/lib/api/assessments";

export const assessmentOptions: AssessmentOptions = {
  max_questions: 12,
  duration_hours: 24,
  conceptual_provider: "MockAIProvider",
  conceptual_kind: "simulation",
  inventory: [
    {
      category: "DBMS",
      difficulty: "easy",
      question_type: "multiple_choice",
      count: 2,
    },
    {
      category: "DBMS",
      difficulty: "medium",
      question_type: "multiple_select",
      count: 1,
    },
    {
      category: "DBMS",
      difficulty: "hard",
      question_type: "written",
      count: 1,
    },
  ],
};
export const assessmentFixture: Assessment = {
  id: "attempt-one",
  title: "DBMS assessment",
  status: "in_progress",
  revision: 1,
  started_at: "2026-10-14T10:00:00Z",
  deadline_at: "2030-01-01T00:00:00Z",
  completed_at: null,
  question_count: 3,
  answered: 0,
  simulated: false,
  configuration: {
    category: "DBMS",
    difficulty: null,
    question_types: ["multiple_choice", "multiple_select", "written"],
    question_count: 3,
  },
  categories: [],
  questions: [
    {
      id: "q1",
      question_version_id: "v1",
      position: 1,
      title: "Index lookup",
      prompt: "Which operation benefits from this index?",
      category: "DBMS",
      difficulty: "easy",
      question_type: "multiple_choice",
      options: [
        { id: "o1", text: "Selective equality lookup" },
        { id: "o2", text: "Every write automatically" },
      ],
      answer_text: null,
      selected_option_ids: [],
      saved_at: null,
      skipped: false,
      review: null,
    },
    {
      id: "q2",
      question_version_id: "v2",
      position: 2,
      title: "Transaction guarantees",
      prompt: "Select every valid transaction guarantee.",
      category: "DBMS",
      difficulty: "medium",
      question_type: "multiple_select",
      options: [
        { id: "o3", text: "Atomic changes" },
        { id: "o4", text: "Durable commits" },
        { id: "o5", text: "Constant-time queries" },
      ],
      answer_text: null,
      selected_option_ids: [],
      saved_at: null,
      skipped: false,
      review: null,
    },
    {
      id: "q3",
      question_version_id: "v3",
      position: 3,
      title: "Explain index tradeoffs",
      prompt: "Explain the cost of maintaining indexes.",
      category: "DBMS",
      difficulty: "hard",
      question_type: "written",
      options: [],
      answer_text: null,
      selected_option_ids: [],
      saved_at: null,
      skipped: false,
      review: null,
    },
  ],
};

export function completedAssessment(attempt: Assessment): Assessment {
  return {
    ...attempt,
    status: "completed",
    completed_at: "2026-10-14T10:10:00Z",
    revision: attempt.revision + 1,
    simulated: true,
    categories: [
      {
        category: "DBMS",
        questions: 3,
        answered: 3,
        skipped: 0,
        objective_correct: 2,
        objective_total: 2,
        conceptual_score: 2,
        conceptual_max: 4,
        conceptual_kind: "simulation",
      },
    ],
    questions: attempt.questions.map((q) => ({
      ...q,
      review: {
        score: q.question_type === "written" ? 2 : 1,
        max_score: q.question_type === "written" ? 4 : 1,
        is_correct: q.question_type === "written" ? null : true,
        result_kind:
          q.question_type === "written" ? "simulation" : "deterministic",
        feedback:
          q.question_type === "written"
            ? "Mock simulation: lexical overlap is not demonstrated competence."
            : "Correct.",
        metadata: {
          provider:
            q.question_type === "written" ? "MockAIProvider" : "deterministic",
          provider_version: "test-v1",
          policy_version: "assessment-scoring-v1",
          rubric_version: "test-v1",
          evaluated_at: "2026-10-14T10:10:00Z",
          matched_concepts: [],
        },
        expected_concepts: ["Maintain index entries during writes"],
        accepted_answers: [],
        correct_option_ids: q.options
          .slice(0, q.question_type === "multiple_select" ? 2 : 1)
          .map((o) => o.id),
      },
    })),
  };
}
export function assessmentApiFixture(): AssessmentApi {
  let current = structuredClone(assessmentFixture);
  return {
    options: vi.fn().mockResolvedValue(assessmentOptions),
    history: vi.fn().mockImplementation(async (offset: number) => ({
      items: offset ? [] : [current],
      offset,
      total: 11,
      limit: 10,
    })),
    start: vi.fn().mockImplementation(async () => current),
    read: vi.fn().mockImplementation(async () => current),
    save: vi.fn().mockImplementation(
      async (
        _id: string,
        q: string,
        input: {
          answer_text?: string | null;
          selected_option_ids?: string[];
        },
      ) => {
        current = {
          ...current,
          revision: current.revision + 1,
          questions: current.questions.map((v) =>
            v.id === q
              ? {
                  ...v,
                  answer_text: input.answer_text || null,
                  selected_option_ids: input.selected_option_ids ?? [],
                  saved_at: "2026-10-14T10:05:00Z",
                }
              : v,
          ),
        };
        current.answered = current.questions.filter(
          (q) => q.answer_text || q.selected_option_ids.length,
        ).length;
        return current;
      },
    ),
    submit: vi.fn().mockImplementation(async () => {
      current = completedAssessment(current);
      return current;
    }),
    abandon: vi.fn().mockImplementation(async () => {
      current = {
        ...current,
        status: "abandoned",
        revision: current.revision + 1,
      };
      return current;
    }),
  };
}
