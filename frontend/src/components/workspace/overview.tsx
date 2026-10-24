import Link from "next/link";
import type { Dashboard } from "@/lib/api/workspace";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Badge } from "@/components/ui/table";
import { sectionHref } from "./navigation";

export function Overview({ data }: { data: Dashboard }) {
  const href = (
    section: "settings" | "targets" | "resume" | "roadmap" | "progress",
  ) => sectionHref(data.mode, section);
  const hasProfile = Boolean(data.profile);
  const demo = data.mode === "demo";
  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Preparation overview</p>
          <h1 className="page-title">
            {demo
              ? (data.profile?.display_name ?? "Demo dashboard")
              : hasProfile
                ? "Dashboard"
                : "Set up your preparation"}
          </h1>
          <p className="page-description">
            {demo
              ? "Explore a sample journey, review the history, and try completing a roadmap task."
              : hasProfile
                ? `Preparing for ${data.profile?.target_role}. Review your context or plan your next practice session.`
                : "Add your target role, experience level, and weekly study budget to begin."}
          </p>
        </div>
        <Badge tone="green">
          {demo
            ? "Demo workspace"
            : hasProfile
              ? "Profile saved"
              : "Let’s get started"}
        </Badge>
      </header>
      <section className="border border-line bg-surface p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-lg">
            <p className="eyebrow">
              {demo ? "Try it in the demo" : "Your next step"}
            </p>
            <h2 className="mt-4 font-serif text-2xl sm:text-3xl">
              {demo
                ? "Try a roadmap task"
                : hasProfile
                  ? "Plan your next practice session"
                  : "Start with your preparation profile."}
            </h2>
            <p className="mt-3 text-sm leading-7 text-muted">
              {demo
                ? "Open the sample roadmap and mark a task complete. Your changes stay in this isolated demo until it expires or you delete it."
                : hasProfile
                  ? "Generate a roadmap from your job priorities, resume evidence, and weekly study budget."
                  : "Tell us the role you’re working toward, your experience level, and the time you want to set aside. You can change these later."}
            </p>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <ButtonLink href={href(demo || hasProfile ? "roadmap" : "settings")}>
            {demo
              ? "Open sample roadmap"
              : hasProfile
                ? "Open roadmap"
                : "Set up your profile"}
            <Icon name="arrow" width={17} height={17} />
          </ButtonLink>
          {demo && (
            <ButtonLink href={href("resume")} variant="outline">
              Upload your resume
            </ButtonLink>
          )}
          {!demo && hasProfile && (
            <ButtonLink href="/demo" variant="outline">
              Explore the demo
            </ButtonLink>
          )}
        </div>
      </section>
      <div className="mt-10 grid gap-10 xl:grid-cols-[1.4fr_1fr]">
        <section>
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="section-title">Your starting point</h2>
            <span className="text-xs text-muted">Preparation checklist</span>
          </div>
          <ol className="border-t border-line">
            {[
              {
                title: "Preparation profile",
                description: hasProfile
                  ? data.profile?.target_role
                  : "Add your role, experience, and study budget.",
                href: href("settings"),
                ready: hasProfile,
                status: hasProfile ? "Saved" : "Start here",
              },
              {
                title: demo
                  ? "Explore your target job"
                  : data.targets.length
                    ? "Review your target jobs"
                    : "Add a target job",
                description: "Keep the role’s requirements in view.",
                href: href("targets"),
                ready: data.targets.length > 0,
                status: data.targets.length ? "Available" : "Next step",
              },
              {
                title: "Resume evidence",
                description: "Review the evidence behind your resume.",
                href: href("resume"),
                ready: data.resumes.length > 0,
                status: data.resumes.length
                  ? "Available"
                  : demo
                    ? "Preview"
                    : "Next step",
              },
            ].map((step, index) => (
              <li key={step.title} className="border-b border-line">
                <Link
                  href={step.href}
                  className="group flex min-h-24 items-center gap-4 py-5"
                >
                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs ${step.ready ? "border-accent bg-tint text-accent" : "border-line text-muted"}`}
                  >
                    {step.ready ? (
                      <Icon name="check" width={16} height={16} />
                    ) : (
                      index + 1
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="text-sm font-semibold group-hover:text-accent">
                      {step.title}
                    </span>
                    <span className="mt-1 block text-xs leading-6 text-muted">
                      {step.description}
                    </span>
                  </span>
                  <span className="text-xs text-muted">{step.status}</span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
        <section>
          <h2 className="section-title">
            {demo ? "Sample activity" : "Practice activity"}
          </h2>
          <div className="mt-5 border-t border-line pt-6">
            <p className="text-sm leading-7 text-muted">
              {data.progress.length
                ? "Your activity history keeps the context behind each recorded step. Demo events are always labeled as simulations."
                : "When you start completing practice, your activity will appear here. There’s no readiness score to guess at before you begin."}
            </p>
            <Link href={href("progress")} className="text-link mt-3">
              {data.progress.length ? "View activity" : "About your progress"}
              <Icon name="arrow" width={16} height={16} />
            </Link>
          </div>
          {data.profile && (
            <dl className="mt-5 border-t border-line pt-5 text-sm">
              <div className="flex justify-between gap-3">
                <dt className="text-muted">Weekly study budget</dt>
                <dd className="font-medium">
                  {data.profile.weekly_minutes} min
                </dd>
              </div>
              <div className="mt-3 flex flex-wrap justify-between gap-3">
                <dt className="text-muted">Timezone</dt>
                <dd>{data.profile.timezone}</dd>
              </div>
            </dl>
          )}
        </section>
      </div>
    </>
  );
}
