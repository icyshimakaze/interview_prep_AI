import type { Dashboard } from "@/lib/api/workspace";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/states";
import { Badge } from "@/components/ui/table";
import { sectionHref } from "./navigation";
import { SectionHeader } from "./section-header";

export function EvidenceView({
  data,
  section,
}: {
  data: Dashboard;
  section: "targets" | "resume";
}) {
  const targets = section === "targets";
  const empty = targets ? !data.targets.length : !data.resumes.length;
  return (
    <>
      <SectionHeader
        title={targets ? "Target Job" : "Resume"}
        eyebrow="Set the context"
        description={
          targets
            ? "Keep the role and its requirements at the center of your preparation."
            : "A place for the experience, projects, and claims you want to be ready to discuss."
        }
        unavailable={empty}
      />
      {empty ? (
        <EmptyState
          icon={targets ? "target" : "resume"}
          title={
            targets
              ? "Start with the role you want."
              : "Your experience belongs here."
          }
          description={
            targets
              ? "No target job has been added. You can already save your target role in your preparation profile. Job descriptions and requirement review are coming next."
              : "No resume evidence is available here. Signed-in accounts can upload and review PDF resumes; the demo uses a fictional resume."
          }
          action={
            <ButtonLink
              href={
                targets ? sectionHref(data.mode, "settings") : "/demo/resume"
              }
              variant="outline"
            >
              {targets ? "Review preparation profile" : "View sample resume"}
            </ButtonLink>
          }
          note={
            targets
              ? "Job description entry is not available in this preview."
              : "The fictional demo does not accept resume uploads."
          }
        />
      ) : (
        <div className="space-y-7">
          {targets
            ? data.targets.map((target) => (
                <article
                  key={target.id}
                  className="border-y border-line bg-surface p-6 sm:p-8"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h2 className="section-title">{target.title}</h2>
                      <p className="mt-2 text-sm text-muted">
                        {target.organization ?? "Organization not provided"}
                      </p>
                    </div>
                    {data.mode === "demo" && (
                      <Badge tone="amber">Fictional target</Badge>
                    )}
                  </div>
                  <div className="section-rule">
                    <h3 className="text-sm font-semibold">Role context</h3>
                    <p className="mt-3 text-sm leading-8 whitespace-pre-wrap text-muted">
                      {target.description ??
                        "No description has been provided."}
                    </p>
                  </div>
                </article>
              ))
            : data.resumes.map((resume) => (
                <article
                  key={resume.id}
                  className="border-y border-line bg-surface p-6 sm:p-8"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <h2 className="section-title">{resume.label}</h2>
                    {data.mode === "demo" && (
                      <Badge tone="amber">Fictional resume</Badge>
                    )}
                  </div>
                  <h3 className="mt-8 text-xs font-semibold tracking-wider text-muted uppercase">
                    Recorded evidence
                  </h3>
                  <ul className="mt-3 divide-y divide-line">
                    {resume.evidence.map((excerpt, index) => (
                      <li
                        key={index}
                        className="py-4 text-sm leading-8 text-muted"
                      >
                        {excerpt}
                      </li>
                    ))}
                  </ul>
                  {!resume.evidence.length && (
                    <p className="mt-4 text-sm text-muted">
                      No evidence has been recorded for this resume.
                    </p>
                  )}
                  <p className="mt-6 border-t border-line pt-5 text-xs leading-6 text-muted">
                    Resume claims are preparation context, not verified proof of
                    competence.
                  </p>
                </article>
              ))}
        </div>
      )}
      <section className="section-rule">
        <h2 className="section-title">
          {targets
            ? "A useful target is specific."
            : "Prepare to explain the details."}
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">
          {targets
            ? "Look for the responsibilities you would own, the skills the role calls for, and the examples from your work that connect to them."
            : "Think about what you built, the decisions you made, the alternatives you considered, and what you would change. A concrete explanation is more useful than a long list of tools."}
        </p>
      </section>
    </>
  );
}
