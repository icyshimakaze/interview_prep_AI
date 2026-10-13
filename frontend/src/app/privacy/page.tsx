import type { Metadata } from "next";
import { PublicShell } from "@/components/public/public-shell";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Privacy & data" };

export default function PrivacyPage() {
  return (
    <PublicShell>
      <article className="public-width py-16 sm:py-20">
        <div className="max-w-3xl">
          <p className="eyebrow">Privacy & data</p>
          <h1 className="editorial-title mt-5">Know what you’re sharing.</h1>
          <p className="mt-6 text-lg leading-8 text-muted">
            This development preview keeps fictional demo data separate from
            account data. Here is what the current product does.
          </p>
          <p className="mt-4 text-xs text-muted">Updated 13 October 2026</p>
          {[
            [
              "The interactive demo",
              "Each visitor gets a separate workspace with a fictional candidate and simulated history. No real resume, repository, or job description is requested. The demo uses a session cookie and a security cookie to save your sample task changes. Workspaces expire within 24 hours; an hourly cleanup removes expired data. “Exit and delete demo” removes your workspace immediately.",
            ],
            [
              "Your account and profile",
              "When account access is configured, Clerk handles sign-in. The app stores your optional display name, target role, experience band, timezone, and weekly study budget in its database, associated with your account. This preparation data is retained until an explicit deletion process is implemented; there is no automatic account retention period in this preview.",
            ],
            [
              "Files and AI services",
              "Real resume uploads, repository imports, and AI evaluation are not enabled. The demo’s authored feedback is a simulation. Your profile and sample task changes are not sent to an AI provider by this application.",
            ],
            [
              "Access and storage",
              "Private API requests resolve the account or demo workspace on the server. Another visitor cannot select your workspace by supplying its ID. Account tokens stay in the sign-in SDK’s memory; the app does not write them or your preparation records to browser local storage.",
            ],
            [
              "Controls and current limits",
              "You can edit your preparation profile and sign out from Settings. Demo deletion is available now. Self-service account export, account deletion, and identity-provider deletion reconciliation are not yet available. Avoid adding sensitive information to this development preview.",
            ],
          ].map(([title, text]) => (
            <section key={title} className="section-rule">
              <h2 className="section-title">{title}</h2>
              <p className="mt-3 text-base leading-8 text-muted">{text}</p>
            </section>
          ))}
          <ButtonLink href="/" variant="outline" className="mt-10">
            Back to Interview Prep
          </ButtonLink>
        </div>
      </article>
    </PublicShell>
  );
}
