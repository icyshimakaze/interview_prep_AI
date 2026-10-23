import Link from "next/link";
import { PublicShell } from "@/components/public/public-shell";
import { WorkspacePreview } from "@/components/public/workspace-preview";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

const features: {
  title: string;
  description: string;
  status: string;
}[] = [
  {
    title: "Job targets and resume evidence",
    description:
      "Keep the job requirements and your experience in view, so preparation has a purpose.",
    status: "PDF upload and evidence review in accounts",
  },
  {
    title: "Assessments and interviews",
    description:
      "Answer reviewed questions, save drafts, and return to feedback from each attempt.",
    status: "Interactive practice available in the demo",
  },
  {
    title: "A personal practice roadmap",
    description:
      "Generate a plan from your job priorities, evidence and weekly time. Complete, reopen and retain earlier work.",
    status: "Tasks include sources and preparation priorities",
  },
  {
    title: "Progress from saved activity",
    description:
      "Review recorded assessment accuracy, interview ratings and task completion, with validation limits explained.",
    status: "Simulated results stay separate from validated evidence",
  },
];

export default function Home() {
  return (
    <PublicShell>
      <div className="public-width">
        <section className="grid items-center gap-10 py-12 lg:grid-cols-[1.05fr_1fr] lg:gap-14 lg:py-16">
          <div>
            <p className="eyebrow">Technical interview preparation</p>
            <h1 className="mt-5 font-serif text-4xl leading-[1.12] tracking-tight sm:text-5xl lg:text-6xl">
              Prepare for your next interview.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-8 text-muted">
              Turn job requirements and your experience into focused practice.
              Review questions, rehearse interviews, and track the work you
              complete.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/demo">
                Try Interactive Demo{" "}
                <Icon name="arrow" width={17} height={17} />
              </ButtonLink>
              <ButtonLink href="/sign-up" variant="outline">
                Create account
              </ButtonLink>
            </div>
            <p className="mt-4 max-w-sm text-xs leading-6 text-muted">
              No sign-up needed for the demo. Fictional candidate, simulated
              history, no AI key required.
            </p>
          </div>
          <WorkspacePreview />
        </section>
        <section
          id="product"
          className="public-section grid gap-8 md:grid-cols-[1fr_1.3fr]"
        >
          <div>
            <p className="eyebrow">The product</p>
            <h2 className="editorial-title mt-5">
              Your role, evidence, and practice.
            </h2>
          </div>
          <div className="space-y-5 text-base leading-8 text-muted">
            <p>
              Save the requirements of a target job, review the claims in your
              resume, and practice explaining what you know. Each recommendation
              shows the evidence behind it. The demo lets you try the workflow
              with a fictional candidate and simulated history.
            </p>
            <Link href="#features" className="text-link">
              Explore the workspace <Icon name="arrow" width={17} height={17} />
            </Link>
          </div>
        </section>
        <section id="how-it-works" className="public-section">
          <p className="eyebrow">How it works</p>
          <h2 className="editorial-title mt-5">
            From requirements to practice.
          </h2>
          <ol className="mt-8 grid gap-7 md:grid-cols-3">
            {[
              {
                title: "Set your direction",
                text: "Choose your target role, describe your experience level, and decide how much time you can set aside.",
              },
              {
                title: "Work through the gaps",
                text: "Answer assessment questions, rehearse interviews, and explain your project decisions.",
              },
              {
                title: "Return with a next step",
                text: "Review the activity behind your progress and carry your preparation forward.",
              },
            ].map((step, index) => (
              <li key={step.title} className="border-t border-line pt-5">
                <span className="font-mono text-sm text-accent">
                  0{index + 1}
                </span>
                <h3 className="section-title mt-5">{step.title}</h3>
                <p className="mt-3 text-sm leading-7 text-muted">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>
        <section id="features" className="public-section">
          <div className="flex flex-wrap items-end justify-between gap-5">
            <div>
              <p className="eyebrow">Inside the workspace</p>
              <h2 className="editorial-title mt-5">
                Tools for your preparation
              </h2>
            </div>
          </div>
          <div className="mt-8 grid md:grid-cols-2">
            {features.map((feature, index) => (
              <article
                key={feature.title}
                className={`border-t border-line py-8 ${index % 2 === 0 ? "md:pr-12" : "md:border-l md:pl-12"}`}
              >
                <h3 className="section-title">{feature.title}</h3>
                <p className="mt-3 max-w-md text-sm leading-7 text-muted">
                  {feature.description}
                </p>
                <p className="mt-5 text-xs font-medium text-accent">
                  {feature.status}
                </p>
              </article>
            ))}
          </div>
          <p className="border-t border-line pt-6 text-sm leading-7 text-muted">
            Project Defense analyzes public GitHub repositories or source ZIPs
            without executing code. Explore cited facts and practice explaining
            architecture, trade-offs and your contributions.
          </p>
        </section>
        <section
          id="privacy"
          className="public-section grid gap-9 md:grid-cols-[1fr_1.2fr]"
        >
          <div>
            <h2 className="editorial-title">Know what is saved.</h2>
          </div>
          <div>
            <p className="text-base leading-8 text-muted">
              The demo uses fictional information in a separate, temporary
              workspace. Project Defense includes an offline teaching fixture
              and optional repository imports. Defense practice sends no source
              or answers to an AI service.
            </p>
            <ul className="mt-6 space-y-4 text-sm text-ink">
              {[
                "Demo workspaces expire within 24 hours.",
                "Exit and delete removes your demo immediately.",
                "Real account data stays separate from the demo.",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <Icon name="check" className="shrink-0 text-accent" />
                  {item}
                </li>
              ))}
            </ul>
            <Link href="/privacy" className="text-link mt-6">
              Read about privacy & data{" "}
              <Icon name="arrow" width={17} height={17} />
            </Link>
          </div>
        </section>
      </div>
      <section className="border-t border-line bg-tint">
        <div className="public-width flex flex-wrap items-center justify-between gap-8 py-14">
          <div>
            <p className="eyebrow">Take a look around</p>
            <h2 className="mt-3 font-serif text-3xl sm:text-4xl">
              Try a practice session.
            </h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              Explore a fictional preparation journey at your own pace.
            </p>
          </div>
          <ButtonLink href="/demo">
            Explore the demo <Icon name="arrow" width={17} height={17} />
          </ButtonLink>
        </div>
      </section>
    </PublicShell>
  );
}
