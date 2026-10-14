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
          <p className="mt-4 text-xs text-muted">Updated 14 October 2026</p>
          {[
            [
              "The interactive demo",
              "Each visitor gets a separate workspace with a fictional candidate and simulated history. No real resume, repository, or job description is requested. The demo uses a session cookie and a security cookie to save your sample task changes. Workspaces expire within 24 hours; an hourly cleanup removes expired data. “Exit and delete demo” removes your workspace immediately.",
            ],
            [
              "Your account and profile",
              "When account access is configured, Clerk handles sign-in. The app stores your target role, experience level, timezone, and study budget. You may also supply a display name, short education description, graduation year, technologies/interests, and interview date. Those details are optional. Delete your preparation profile in Settings to remove its details; this preserves your account and other saved work.",
            ],
            [
              "Your target jobs",
              "Job titles, descriptions, and your optional company, notes, and source link are stored in your account workspace. Source links are never fetched by the application, and no skills are inferred. Description edits retain prior versions for preparation history. You can delete unreferenced jobs, including their versions; jobs used by retained history can be archived. There is no automatic retention period for account preparation data in this preview.",
            ],
            [
              "Your resume and evidence",
              "Signed-in accounts can upload PDF resumes up to 5 MiB and 20 pages. Remove contact details and other private information before uploading. The server extracts selectable text in memory, then discards the raw PDF and full extracted text after the request. It stores the validated filename as a label, a content checksum, page/size metadata, and selected evidence excerpts and your corrections. No raw PDF download or permanent file storage is provided. Excerpts may still contain personal information from your resume, so review them.",
            ],
            [
              "Review and deletion",
              "Detected mentions are proposed preparation context, not verified competence. You can correct, reject, add, or delete evidence. No evidence detected never means you do not know something. Delete a resume to remove its versions, excerpts, and corrections; retained preparation history may prevent record deletion, but individual evidence can still be deleted. Account evidence has no automatic expiry in this preview. Deletion removes active database records; operator backups, if configured, follow their own retention policy and are not erased by this control.",
            ],
            [
              "AI and external services",
              "Resume parsing runs on this application's server without OCR, external document services, or AI providers. The application does not log full resume text or send it to an AI provider. Repository imports and AI evaluation remain unavailable. The demo’s authored feedback is a simulation.",
            ],
            [
              "Question-bank practice",
              "Bookmarks and submitted practice responses are stored privately with the question version and submission time. Expected concepts become available after you submit a response to that version. Practice uses self-review and sends no responses to an AI service. You can remove bookmarks and delete each question-bank response from its history; other assessment or interview records retain their existing controls. Account responses have no automatic expiry. Demo responses are simulated practice and expire with the demo workspace; use fictional text. Deletion removes active records and does not erase operator backups.",
            ],
            [
              "Assessment responses",
              "Assessments store your selected options, written responses, question versions, scores, evaluation method and timestamps. Objective grading runs on the server. Conceptual feedback currently uses a labelled local MockAIProvider simulation; no response is sent to a cloud AI service. Unsaved edits stay in page memory. Saved account attempts have no automatic expiry or individual deletion control yet; deleting your profile does not erase preparation history. Demo attempts are erased with the expiring workspace or when you exit and delete it. Backups follow operator retention policies.",
            ],
            [
              "Access and storage",
              "Private API requests resolve the account or demo workspace on the server. Another visitor cannot select your workspace by supplying its ID. Account tokens stay in the sign-in SDK’s memory; the app does not write them or your preparation records to browser local storage.",
            ],
            [
              "Controls and current limits",
              "You can edit or delete your preparation profile, manage target jobs and resume evidence, and sign out from Settings. Demo deletion is available now. Self-service account export, account deletion, and identity-provider deletion reconciliation are not yet available. Avoid adding sensitive information to this development preview.",
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
