import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { PublicShell } from "@/components/public/public-shell";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Terms of Service" };

const sections: readonly (readonly [string, ReactNode])[] = [
  [
    "The service",
    "Interview Prep AI provides preparation profiles, practice, feedback and saved work. It is a development preview: features and availability can change. Fictional demo activity and simulated feedback are labelled. Practice scores and feedback do not establish competence or guarantee interviews, employment or any hiring outcome.",
  ],
  [
    "Accounts and access",
    "Use only an account you control and the sign-in methods offered on this website. You are responsible for keeping access to your sign-in provider secure. Matching email addresses do not automatically connect different sign-in identities. Where account connection is available, both identities must be proven. Public email/password registration, password recovery and verification-email delivery are unavailable in this release. Signing out ends access to the session; it does not delete saved account work.",
  ],
  [
    "Your content",
    "You retain any rights you have in your resumes, answers, job descriptions and other submitted content. Provide only content you have permission to use. By submitting it, you allow the application to process and store it as needed to provide the features you request, as described in the Privacy Policy. Remove passwords, access tokens and information you are not authorized to share before uploading files or importing repositories.",
  ],
  [
    "Responsible use",
    "Use the service lawfully and respect other people's rights. Do not impersonate another person, access another user's workspace, bypass authentication or usage limits, disrupt the service, or submit malicious files or code. Follow the rules of any employer, school or assessment when using preparation material or assistance. Access may be limited or suspended to address abuse or security concerns.",
  ],
  [
    "Feedback and external services",
    "Review feedback before relying on it: it may be incomplete or incorrect. Simulated feedback is not a real AI assessment. Where an optional external AI feature is enabled, the interface identifies its provider and requests the applicable sharing consent. Sign-in and other external providers have their own terms and privacy policies. GitHub sign-in requests identity email access, not repository permissions; repository import is a separate feature.",
  ],
  [
    "Saved work and deletion",
    <>
      Keep your own copies of important work. Unsaved edits and access to a demo
      can be lost if you close the page or lose its cookie. Demo workspaces
      expire within 24 hours; physical cleanup waits until the service runs.
      Available deletion controls remove the records described by that control.
      Deleting your preparation profile does not delete your account or other
      saved history. Self-service account deletion and export are not yet
      available. Active-data deletion does not erase operator backups. Retention
      and feature-specific limits are described in the{" "}
      <Link href="/privacy" className="text-link">
        Privacy Policy
      </Link>
      .
    </>,
  ],
  [
    "Availability",
    "The preview can be interrupted by maintenance, hosting sleep, limits or failures. Continuous availability, uninterrupted sessions and completion of every request are not promised. If an interrupted sign-in session requires you to authenticate again, use the same sign-in identity to return to its saved workspace. Temporary demo access has no email-recovery mechanism.",
  ],
  [
    "Privacy and changes",
    <>
      The{" "}
      <Link href="/privacy" className="text-link">
        Privacy Policy
      </Link>{" "}
      explains what the service stores, sharing with providers, retention and
      current controls. Updates to these terms will be published here with a
      revised date. Check the current terms and privacy information when using a
      new feature.
    </>,
  ],
];

export default function TermsPage() {
  return (
    <PublicShell>
      <article className="public-width py-16 sm:py-20">
        <div className="max-w-3xl">
          <p className="eyebrow">Using Interview Prep AI</p>
          <h1 className="editorial-title mt-5">Terms of Service</h1>
          <p className="mt-6 text-lg leading-8 text-muted">
            These terms apply to Interview Prep AI at
            interviewprepai.webredirect.org. By using the service, you agree to
            these terms. If you do not agree, do not use the service.
          </p>
          <p className="mt-4 text-xs text-muted">Updated 29 October 2026</p>
          {sections.map(([title, content]) => (
            <section key={title} className="section-rule">
              <h2 className="section-title">{title}</h2>
              <p className="mt-3 text-base leading-8 text-muted">{content}</p>
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
