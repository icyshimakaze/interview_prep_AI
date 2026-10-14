import type {
  QuestionDetail,
  QuestionPage,
  QuestionApi,
} from "@/lib/api/questions";

export const questionFixture: QuestionDetail = {
  id: "question-one",
  version_id: "version-two",
  version: 2,
  title: "Two Sum Problem",
  category: "Algorithms",
  subtopic: "Hash lookup",
  difficulty: "easy",
  question_type: "written",
  prompt:
    "Find indices of two distinct elements with a target sum. Explain duplicate handling.",
  tags: ["arrays", "hashing"],
  roles: ["software-engineer"],
  source_classification: "legacy_adapted",
  active: true,
  bookmarked: false,
  attempted: false,
  options: [],
  concepts_unlocked: false,
  expected_concepts: null,
  source_file: "content/question-bank-v1.json",
  original_topic: "Arrays",
};
export const questionPageFixture: QuestionPage = {
  items: [questionFixture],
  total: 13,
  offset: 0,
  limit: 12,
};
export function questionApiFixture(): QuestionApi {
  return {
    list: async () => questionPageFixture,
    facets: async () => ({
      categories: ["Algorithms"],
      subtopics: ["Hash lookup"],
      roles: ["software-engineer"],
    }),
    read: async () => questionFixture,
    bookmark: async (_, saved) => saved,
    submit: async (_, input) => ({
      id: "attempt-one",
      question_version_id: input.question_version_id,
      answer_text: input.answer_text,
      submitted_at: "2026-10-14T00:00:00Z",
      result_kind: "self_review",
    }),
    history: async () => ({ items: [], total: 0, offset: 0, limit: 10 }),
    removeAttempt: async () => undefined,
  };
}
