# Candidate profile and target jobs

Date: 2026-10-13. Status: implemented and verified.

## Objective and scope

Make candidate context and target jobs usable end-to-end in real account mode:
owned persistence, create/read/edit/delete, validated forms, recovery, honest empty
states and tests. Preserve existing authentication, demo isolation and history.
No AI/skill extraction, scraping, resume ingestion or deployment is included.

Profile keeps the existing required role/experience/timezone/study budget contract,
with optional display name, short education description, graduation year, supplied
technologies/interests and interview date. No institution, GPA, birth date, phone,
address or demographic fields. User interests are labels, never inferred skills or
competence evidence. The UI expresses study budget in hours and stores whole minutes.

Targets require title and description, with optional company, source URL and notes,
explicit priority and status. URLs are validated HTTP(S) links, never fetched.

## Data / API

- Add versioned migration 0003 for optional profile fields, normalized owned interest
  rows, target metadata and revision. Preserve existing rows; defaults are neutral.
  Reuse profile target_date as interview_date in the API. Rollback refuses loss of
  populated new fields; empty downgrade/re-upgrade is verified on disposable data.
- Profile GET/PUT/DELETE use resolved account ownership and revision checks. Deleting
  the preparation profile preserves jobs, history and the account.
- Targets list/read/create/update/delete use owner-scoped queries, bounded pagination,
  count limits, validation and revision conflict handling. Description edits append a
  version; old versions/requirements/history remain intact. Deletion of a referenced
  target is refused with an actionable archive option; no history is silently erased.
- Regenerate OpenAPI/client types and maintain runtime response validation. Keep the
  fictional demo read-only for new context CRUD and preserve existing demo operations.

## Frontend / security

Extend Settings/Profile; add a target-job editor, details, status/priority filtering,
pagination and deletion dialogs. Show pending/saved/error feedback; retain failed
drafts and support explicit reload after conflicts. Clear private state on account
changes, keep all tokens in SDK memory, and never accept owner IDs from the client.
Render job text as text, bound all fields, reject unsafe URLs and never infer skills.

## Implementation order / verification

1. Models, frozen migration, validation and owned services/API.
2. Backend tests for persistence, invalid input, ownership, conflicts, history and
   profile/target deletion; migration recovery/backfill/drift checks.
3. Regenerated contracts, account integration, profile and target forms/states.
4. Frontend validation, CRUD/error/isolation tests and browser regression/visual QA.
5. Run backend lint/format/mypy/tests/migrations/contracts and frontend lint,
   typecheck, tests, formatting, production build. Update status with exact results.

No new dependencies expected. Existing Compose services/application data are not
verification fixtures; use disposable databases and separate local ports. Live Clerk
still requires keys; tests use real signed JWTs and trusted mock JWKS, not an auth bypass.

## Outcome

Implemented owned profile context CRUD and target-job CRUD with normalized interests,
version-preserving descriptions, validation, revision conflicts, safe deletion/archive
and responsive forms. Migration 0003 preserves existing data and refuses lossy rollback.
No skills are inferred and source links are never fetched. No dependency was added.

Verified 115 backend, 41 frontend and 20 browser tests; lint, strict types, migrations,
contracts and production build passed. Fixed an observed timeout error path with a
regression. Browser form QA uses explicitly labeled static component fixtures; live
Clerk remains unverified without keys. Existing application data/services were not
updated, committed, pushed or deployed. Rollout/retention and exact results are in
docs/CANDIDATE_CONTEXT.md and PROJECT_STATUS.md.
