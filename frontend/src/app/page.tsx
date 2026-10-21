import Link from "next/link";
import { PublicShell } from "@/components/public/public-shell";
import { WorkspacePreview } from "@/components/public/workspace-preview";
import { ButtonLink } from "@/components/ui/button";
import { Icon, type IconName } from "@/components/ui/icon";

const features: {
  icon: IconName;
  title: string;
  description: string;
  status: string;
}[] = [
  {
    icon: "target",
    title: "A role to work toward",
    description:
      "Keep the job requirements and your experience in view, so preparation has a purpose.",
    status: "Target & resume · Account workspace",
  },
  {
    icon: "assessments",
    title: "Practice with context",
    description:
      "Explore how assessment results and interview feedback fit into one preparation history.",
    status: "Assessments & interviews · Demo preview",
  },
  {
    icon: "roadmap",
    title: "A manageable next step",
    description:
      "Generate a plan from your job priorities, evidence and weekly time. Complete, reopen and retain earlier work.",
    status: "Roadmap · Interactive demo",
  },
  {
    icon: "progress",
    title: "A record of the work",
    description:
      "Review recorded assessment accuracy, interview ratings and task completion, with validation limits explained.",
    status: "Progress · Demo preview",
  },
];

export default function Home() {
  return (
    <PublicShell>
      <div className="public-width">
        <section className="grid items-center gap-12 py-16 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:py-24">
          <div>
            <p className="eyebrow">A more deliberate way to prepare</p>
            <h1 className="mt-6 font-serif text-5xl leading-[1.08] tracking-tight sm:text-6xl lg:text-[4.1rem]">
              Walk in with
              <br />a clearer head.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-8 text-muted">
              Bring your target role, experience, and practice into one focused
              workspace. Know where to begin, and what to work on next.
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
              Give your preparation
              <br className="hidden lg:block" /> a place to live.
            </h2>
          </div>
          <div className="space-y-5 text-base leading-8 text-muted">
            <p>
              Interview preparation can get scattered across job tabs, old
              notes, and unfinished question lists. Interview Prep is being
              built to connect that work: the role you want, the experience you
              bring, and the practice you do.
            </p>
            <p>
              Start by exploring the demo or saving your preparation profile.
              The wider practice workflow is in development; each section makes
              its availability clear.
            </p>
            <Link href="#features" className="text-link">
              Explore the workspace <Icon name="arrow" width={17} height={17} />
            </Link>
          </div>
        </section>
        <section id="how-it-works" className="public-section">
          <p className="eyebrow">How it works</p>
          <h2 className="editorial-title mt-5">
            A direction. A practice. A record.
          </h2>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted">
            The preparation flow we’re building, available to explore with
            labeled examples in the demo.
          </p>
          <ol className="mt-12 grid gap-9 md:grid-cols-3">
            {[
              {
                title: "Set your direction",
                text: "Choose your target role, describe your experience level, and decide how much time you can set aside.",
              },
              {
                title: "Work through the gaps",
                text: "Explore sample assessments, interview feedback, and a roadmap of specific practice tasks.",
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
              <h2 className="editorial-title mt-5">The parts, connected.</h2>
            </div>
            <p className="max-w-xs text-sm leading-6 text-muted">
              One place to keep the context behind your preparation.
            </p>
          </div>
          <div className="mt-12 grid md:grid-cols-2">
            {features.map((feature, index) => (
              <article
                key={feature.title}
                className={`border-t border-line py-8 ${index % 2 === 0 ? "md:pr-12" : "md:border-l md:pl-12"}`}
              >
                <Icon
                  name={feature.icon}
                  width={23}
                  height={23}
                  className="text-accent"
                />
                <h3 className="section-title mt-5">{feature.title}</h3>
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
            <Icon name="lock" width={26} height={26} className="text-accent" />
            <h2 className="editorial-title mt-5">
              Your experience.
              <br />
              Handled with care.
            </h2>
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
              Start with a little clarity.
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
