# Secure resume ingestion

Status: implemented and verified; publishing the reviewed changes as authorized.

## Objective and scope

Account users can upload a PDF, review deterministic candidate evidence, correct
or add their own claims, reject/delete incorrect entries, and delete the resume.
Missing mentions never imply missing knowledge. Preserve existing profile, target
job, authentication and fictional demo behavior. Include the preceding verified,
uncommitted candidate context work in the user-authorized GitHub publication.
No OCR, AI, competency scoring, PDF downloads, or application deployment.

## Architecture, API and privacy

- Accept a streamed PDF body with an encoded filename header. Require PDF MIME,
  extension and signature; limit to 5 MiB, 20 pages and bounded extracted text.
  Never use the supplied name as a filesystem path.
- Parse with pinned pypdf in a short-lived subprocess, with memory/time bounds,
  limited concurrency and no inherited application secrets. Raw bytes stay in
  memory; no permanent PDF or full resume text is stored. Suppress parser logs.
- Use the existing owned resumes/version/evidence tables. Add explicit evidence
  category and origin, optional source fields for user additions, root revisions
  and an extraction note in migration 0004. Preserve legacy evidence and refuse
  lossy downgrade. Do not populate the global skill vocabulary or profile fields.
- Owned collection/upload/detail/delete and evidence add/edit/delete APIs use
  existing verified account identity, aggregate locking, revisions and safe errors.
  Bound collection/evidence sizes. Retain only selected excerpts and corrections.
- Deletion removes all resume versions/evidence. History references can prevent
  deletion; disclose this boundary rather than claim complete erasure.

## Frontend and tests

- Resume upload form, parsing/loading/error/empty states, source excerpts with
  categories and proposed/confirmed/rejected status, correction/add/delete forms,
  and confirmed deletion. Keyboard and mobile patterns use the existing UI system.
- Tests: valid/blank/encrypted/corrupt PDF, MIME/extension/signature/size/page
  limits, path names, parser resource failures, deterministic boundaries and
  negation, no competence inference, auth/ownership, review edits, conflicts and
  deletion. Frontend upload/review/error/deletion and desktop/mobile accessibility.

## Order and verification

1. Schema migration and dependency; bounded parser and deterministic extraction.
2. Owned service/API, contracts, backend tests and migration preservation tests.
3. Account UI/API integration, frontend tests and visual accessibility fixtures.
4. Backend lint/types/tests/migration/contract checks; frontend lint/typecheck/tests,
   production build, formatting, browser regression checks and diff review.
5. Privacy/API/status documentation; review staged files for secrets/artifacts,
   commit and push to the existing branch under the user's explicit authorization.

Real Clerk browser verification remains dependent on configured credentials.
Existing application services/database will not be redeployed or migrated.

## Outcome

Implemented bounded streaming/subprocess PDF extraction, categorized proposed
evidence and explicit user-origin additions, owned/revision-checked CRUD, review UI,
safe failures, and privacy/retention documentation. Backend 143 tests and frontend
52 tests passed, along with lint/types/migrations/contracts and production build.
All 21 Chrome browser checks passed; actual static resume forms passed axe/mobile
overflow and screenshots were inspected. Linux non-root/no-network/read-only
container parser checks passed in addition to Windows worker tests. No real Clerk
keys were supplied; live account-browser verification remains a rollout step.

No application database/Compose deployment occurred. The requested publication
includes prior uncommitted candidate context work and migrations 0003/0004.
