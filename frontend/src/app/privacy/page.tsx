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
          <p className="mt-4 text-xs text-muted">Updated 21 October 2026</p>
          {[
            [
              "The interactive demo",
              "Each visitor gets a separate workspace with a fictional candidate and simulated history. Use fictional information in the demo. Project Defense offers an illustrative fixture and optional public GitHub or ZIP imports. The demo uses a session cookie and a security cookie to save your sample task changes. Workspaces expire within 24 hours; an hourly cleanup removes expired data. “Exit and delete demo” removes your workspace immediately.",
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
              "Project repositories and defense answers",
              "You may import a public GitHub repository or source ZIP (10 MiB maximum). GitHub imports send the public repository identifier to GitHub and fetch its default-branch commit archive; no GitHub token is collected. ZIPs stay on this server. Source code is never executed. Archives and source bodies are discarded after bounded analysis. Saved records include paths, file hashes, size/language metadata, cited facts, inferred architecture, generated questions, answer drafts and submitted answers with timestamps. Remove secrets before importing: exclusions do not detect every secret, and paths or static declarations can contain sensitive information. Delete a snapshot to erase its analysis and defense history from active storage. Account snapshots have no automatic expiry; demo snapshots expire with the workspace. Backups follow operator retention policies. Unsaved answers stay in page memory and can be lost on navigation or reload.",
            ],
            [
              "AI and external services",
              "Resume parsing runs on this application's server without OCR, external document services, or AI providers. Uploading a resume does not send it to an AI provider. Project source analysis and defense practice run deterministically without sending repository content or defense answers to an AI service. AI defaults to local deterministic mock simulation; the recruiter demo always uses mock. Optional account evaluation can use an operator-configured Ollama server or OpenAI. Provider credentials remain on the backend.",
            ],
            [
              "Question-bank practice",
              "Bookmarks and submitted practice responses are stored privately with the question version and submission time. Expected concepts become available after you submit a response to that version. Practice uses self-review and sends no responses to an AI service. You can remove bookmarks and delete each question-bank response from its history; other assessment or interview records retain their existing controls. Account responses have no automatic expiry. Demo responses are simulated practice and expire with the demo workspace; use fictional text. Deletion removes active records and does not erase operator backups.",
            ],
            [
              "Assessment responses",
              "Assessments store selected options, written responses, question versions, scores, evaluation provenance and timestamps. Objective grading runs on the server. Conceptual feedback defaults to labelled MockAIProvider simulation with no external sharing. If OpenAI or Ollama is configured, written answer text, the question and review criteria are sent to that provider when you submit; the configuration screen identifies it. No resume, job description or project is sent by the assessment workflow. OpenAI requests disable response storage, but provider retention policies still apply. Validated paid feedback and an input digest are temporarily retained for up to 48 hours plus the hourly cleanup interval, including when another question fails, to avoid duplicate provider calls. A failed evaluation permits one explicit resubmission; interrupted dispatch is not replayed. Unsaved edits stay in page memory. Saved account attempts have no automatic expiry or individual deletion control yet; deleting your profile does not erase preparation history. Demo attempts expire with the workspace or are erased when you exit and delete it. Backups follow operator retention policies.",
            ],
            [
              "Mock interviews",
              "Interview sessions store your typed drafts, submitted answers, skips, timing and final feedback privately. Answers are saved before optional evaluation. Mock is the default and the recruiter demo always uses clearly labelled simulations. If an operator enables OpenAI or Ollama for accounts, the question, submitted answer and authored review criteria go to that provider for evaluation; requesting a follow-up also sends that question and answer with recent interview prompts. Setup discloses the provider before you start. Target-job relevance selection stays local. Sessions expire for interaction after 24 hours; saved account history is retained without an automatic deletion or individual deletion control. Demo data is erased with its workspace. Unsaved text is only in page memory and can be lost on reload. Timing can include time away unless you pause. AI feedback does not establish competence or predict interview outcomes.",
            ],
            [
              "Personal roadmaps and progress analytics",
              "Roadmaps use your selected target and priority, resume context, saved practice results, weekly time and optional interview date. Recommendation versions store concise reasons, source identifiers, budget/date settings and task state. Regeneration keeps prior tasks and completed history. Reopening preserves earlier completion events; completing again records another event. Account roadmap history has no automatic expiry or individual version deletion; deleting a profile, resume or source session does not rewrite saved historical reasons. Demo history expires with its workspace. Progress analytics are calculated from persisted source rows, with objective grades, model ratings and simulations distinguished. These features send no data to an AI provider and do not calculate readiness predictions.",
            ],
            [
              "Access and storage",
              "Private API requests resolve the account or demo workspace on the server. Another visitor cannot select your workspace by supplying its ID. Account tokens stay in the sign-in SDK’s memory; the app does not write them or your preparation records to browser local storage.",
            ],
            [
              "Abuse prevention and logs",
              "Imports and optional AI calls have shared server-side quotas. Short-lived keyed identifiers and counters remain until the next hourly cleanup after their hourly or daily window expires, even if you delete an imported file. They do not contain raw IP addresses, source files or answer text. Unexpected application failures log a random request ID without exception bodies. Hosting and identity-provider logs and backups follow their operator policies.",
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
