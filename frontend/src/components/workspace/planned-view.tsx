import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/states";
import { sectionHref } from "./navigation";
import { SectionHeader } from "./section-header";

export function PlannedView({
  section,
  mode,
}: {
  section: "questions" | "projects";
  mode: "account" | "demo";
}) {
  const questions = section === "questions";
  return (
    <>
      <SectionHeader
        title={questions ? "Question Bank" : "Project Defense"}
        eyebrow={questions ? "Build your practice" : "Know your own work"}
        description={
          questions
            ? "A home for reviewed questions, clear prompts, and focused practice."
            : "Prepare to explain the architecture, decisions, and tradeoffs in your projects."
        }
        unavailable
      />
      <EmptyState
        icon={questions ? "questions" : "projects"}
        title={
          questions
            ? "Good questions take careful preparation."
            : "Your project. Your reasoning."
        }
        description={
          questions
            ? "Question browsing and bookmarks are not available yet. The question bank is being prepared; unpublished drafts are not presented as practice-ready content."
            : "Project Defense is in development. Repository import, source review, and project-specific questions are not available yet."
        }
        action={
          <ButtonLink
            href={sectionHref(mode, questions ? "assessments" : "resume")}
            variant="outline"
          >
            {questions ? "Go to assessments" : "Review resume evidence"}
          </ButtonLink>
        }
        note={
          questions
            ? "No published question count is claimed in this preview."
            : "No repository URL, source code, or access token is collected here."
        }
      />
      <section className="section-rule">
        <h2 className="section-title">
          {questions
            ? "What makes a useful practice question?"
            : "You can start with these notes."}
        </h2>
        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          {(questions
            ? [
                [
                  "A clear prompt",
                  "Understand what is being asked and the constraints of the problem.",
                ],
                [
                  "An explicit standard",
                  "Know which concepts and reasoning a strong answer should cover.",
                ],
                [
                  "Room to reflect",
                  "Connect feedback to a specific next step in your practice.",
                ],
              ]
            : [
                [
                  "The problem",
                  "What did the project need to solve, and for whom?",
                ],
                [
                  "The decisions",
                  "Which tradeoffs did you make, and why did they fit the constraints?",
                ],
                [
                  "The learning",
                  "What failed, what changed, and what would you do differently?",
                ],
              ]
          ).map(([title, description]) => (
            <div key={title}>
              <h3 className="text-sm font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-7 text-muted">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
