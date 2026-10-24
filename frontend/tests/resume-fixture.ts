import type { Resume } from "@/lib/api/resumes";

export const resumeFixture: Resume = {
  id: "owned-resume",
  label: "candidate.pdf",
  revision: 1,
  page_count: 1,
  extraction_note: null,
  is_sample: false,
  evidence: [
    {
      id: "python-mention",
      category: "language",
      origin: "resume",
      claim: "Python",
      user_correction: null,
      source_excerpt: "Interested in learning Python.",
      source_page: 1,
      source_start: 0,
      source_end: 30,
      review_status: "proposed",
    },
  ],
};
