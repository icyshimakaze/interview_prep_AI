# Project Status

Updated: 2026-10-13 (Asia/Calcutta).

## GitHub publication request

On 2026-10-13 the user explicitly authorized committing and pushing the accumulated
V2 foundation, relational model, authentication/recruiter demo and UI work to the
existing `rebuild/professional-v2` branch on `origin`, using the commit message
`feat: add authentication and recruiter demo mode`. The verification results below
record the completed implementation checks. A pre-commit scan of 178 candidate
files found no configured secrets or credential-shaped content; local credentials,
dependencies and runtime/build artifacts remain ignored. Earlier no-commit/no-push
notes describe the state at the end of those implementation phases.

## Public and authenticated UI foundation (current phase)

Implemented the requested public site and ten-section workspace on
`rebuild/professional-v2`, following the [UI plan](.agent/plans/ui-foundation.md).
Existing uncommitted foundation/authentication/data work was preserved. No package,
schema, migration, backend endpoint, or application database changes were needed.
No commit, push, merge, or deployment was performed in this phase.

### Interface and behavior

- Replaced the connectivity-first landing screen with product explanation, how it
  works, feature overview, privacy section, demo/account CTAs and a professional
  footer. Added `/privacy`; preserved the live connection check at `/status`.
- Established warm neutral surfaces, dark ink, muted green, system sans text,
  editorial serif headings, subtle borders and ample spacing. No gradient headings,
  fabricated testimonials/logos/outcomes, decorative animation or external fonts.
- Added deep-linked Dashboard, Target Job, Resume, Assessments, Interviews,
  Question Bank, Roadmap, Project Defense, Progress and Settings/Profile sections.
  Shared desktop sidebar and mobile modal navigation preserve active-route state,
  browser history and main-content focus. Existing `/app/*` auth protection remains.
- New-account dashboards lead with profile onboarding and preparation actions;
  no fabricated scores, progress, completed work or readiness metrics appear.
  Saved profile context and histories come from the existing owned API. Features
  without production workflows have explicit, useful empty/unavailable states.
- Added reusable buttons/link buttons, labeled inputs/selects/form sections,
  tables/badges, line icons, empty states, skeletons, errors and native dialogs.
  Visible focus, skip links, modal focus wrapping/restoration, Escape, mobile table
  scroll regions and associated validation/status messages support keyboard use.
- Profile edits persist through the existing revision-checked endpoint, with
  pending/success/error feedback, retained failed edits, duplicate-submit protection,
  and explicit discard/reload recovery. Account changes remount private state; a
  late token result cannot send an old account's pending profile after unmount.
- Demo now uses the same route-based shell. Fictional/simulation disclosure stays
  visible; sample results, evidence and events are labeled. Task status filtering,
  completion persistence, retry/reset and owned deletion are preserved. Exit uses
  a confirmation dialog with recoverable deletion errors. Demo profiles are read-only.
- Updated authentication/development/README guidance and added the
  [UI foundation guide](docs/UI_FOUNDATION.md) with routes, components and limits.

### Verification for the UI phase

`pnpm format:check` also passed across all matched repository files.

| Check                           | Actual result                                                                                                                                                                                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm lint`                     | Passed; zero warnings.                                                                                                                                                                                                                                |
| `pnpm typecheck`                | Passed; Next route generation and strict TypeScript.                                                                                                                                                                                                  |
| `pnpm test`                     | **29 passed** across four files, including API validation, truthful onboarding/empty states, profile validation/save/conflict/duplicate handling, account isolation and in-flight account changes.                                                    |
| `pnpm build`                    | Passed; production Next build, including final build with the normal backend destination.                                                                                                                                                             |
| Browser verification            | **18 Chrome tests passed** against the production frontend on port 3100, with a fresh migrated disposable PostgreSQL database and temporary API on port 8100.                                                                                         |
| Browser coverage                | Real connectivity, API failure/retry, two-visitor demo isolation/foreign-ID rejection/persistence/deletion, missing-key account behavior, all ten section deep links, mobile overflow, skip navigation, dialog focus/Escape/error recovery.           |
| Accessibility and visual review | Automated axe WCAG A/AA checks found **0 violations** in tested public, privacy, desktop/mobile demo sections and modal states. Desktop/mobile landing, dashboard, settings and table screenshots inspected. This is not complete WCAG certification. |
| Browser harness                 | Added optional bounded API/frontend ports so existing services need not be stopped. Ruff lint/format and strict mypy passed for the modified script (with `MYPYPATH=backend/src`).                                                                    |
| Preservation                    | Original `app.py`, `questions.json`, `requirements.txt` have no Git diff; no dependencies or lockfiles changed in this UI phase.                                                                                                                      |

Initial Windows sandbox worker restrictions were resolved with reviewed local
execution. Browser verification found and fixed modal focus wrapping. An aggregate
ten-screen sweep was split into independent per-section checks, with three workers
to avoid local resource contention; assertions and coverage were retained. Temporary
API/database resources were removed by the harness; the temporary native frontend
was stopped. Existing Compose services were not rebuilt or replaced, so their UI
remains the earlier version until an explicitly authorized local update.

### Limits and next task

- Real Clerk credentials remain absent. Live sign-up/sign-in/profile-save/sign-out
  against Clerk was **not run**; account UI integration tests use mocked SDK/transport.
  No production authentication bypass or fake signed-in preview was added.
- Real resume/job/repository ingestion, published question browsing, assessment and
  interview creation, roadmap generation, AI evaluation, exports and account erasure
  remain later workflows. The UI communicates these boundaries explicitly.
- The existing Compose cleanup container was already restarting when inspected;
  investigate that operational issue separately before relying on scheduled erasure.
  This UI phase did not change that service or claim to reverify its operation.
- Next: configure/test live Clerk with two accounts, then implement the reviewed
  deterministic assessment slice with authored questions, durable drafts and grading.
  Public deployment/security gates from the preceding phases still apply.

## Relational and account implementation (preceding phases)

The relational data model, account authentication/authorization and separate
recruiter demo are implemented on `rebuild/professional-v2`. The earlier V2
foundation remains intact. No commit, push, merge or public deployment occurred.
The final frontend, backend, PostgreSQL and hourly cleanup run through Docker
Compose on localhost; the migration service exited with code 0. Temporary native
verification services were stopped.
Clerk keys were not supplied; real managed sign-up/sign-in/sign-out requires the
documented configuration and was not exercised against a live Clerk instance.

Read the repository rules, architecture, status and affected code before these
phases. Work followed the [relational plan](.agent/plans/relational-data-model.md)
and [account/demo plan](.agent/plans/authentication-demo.md). The explicit user
request advances the schema and account/demo slice ahead of the architecture's
original incremental phase order; broader product workflows remain outside scope.

### Relational persistence

- Added 36 normalized domain tables in revision `0002_relational_model`, alongside
  the three existing demo infrastructure tables. All requested User/Profile,
  TargetJob, Resume, Skill/evidence/requirements, Question/Bookmark, assessment,
  interview/evaluation, roadmap/progress and project entities are represented.
  Versioned content, grading criteria/options, source files/facts/citations and
  evaluation dimensions use relational rows, not application-state JSON blobs.
- UUID identities, UTC server timestamps, constrained enums, meaningful bounds,
  deliberate foreign-key cascades/restrictions, owner-first indexes and compound
  ownership/aggregate foreign keys enforce integrity. Published grading/content,
  final answers, terminal evaluations and historical contexts have database guards.
  Progress facts are append-only and reference completed owned work.
- Preserved existing demo UUIDs and hashed credentials with a principal backfill.
  Migration SQL is frozen independently of live models. Populated domain rollback
  refuses destructive changes; empty rollback/re-upgrade and compatibility demo
  backfill/recovery are tested. The application database was upgraded, never downgraded.
- Installed an idempotent validated development loader and actually loaded
  **15** legacy title-only drafts, **six** skills and **seven** aliases into the
  application database. A second import returned the same count without duplicates.
  Original `app.py`, `questions.json` and `requirements.txt` remain unchanged.
  No missing prompt, answer, rubric, user history or large question count is invented.
- Documented table mappings, history/erasure rules, migration recovery and seeds in
  [DATA_MODEL.md](docs/DATA_MODEL.md); updated architecture/development/legacy notes.

### Accounts and recruiter demo

- Installed pinned Clerk Next.js integration and PyJWT/cryptography dependencies;
  updated both lockfiles. Sign-up/sign-in pages, conditional Clerk provider,
  protected account dashboard and SDK sign-out are implemented. Missing keys show
  an explicit account-unavailable state; no simulated account login is accepted.
- FastAPI verifies trusted RS256 signatures, configured issuer/audience, subject,
  expiry/issued-at/not-before, authorized frontend origin and at most 60-second
  token lifetime. Fixed trusted JWKS discovery has bounded caching/rotation,
  response size and timeout; token-provided key URLs are rejected. Verification
  and discovery failures fail closed with safe structured errors.
- Reusable account/demo dependencies resolve the principal server-side. Account
  bootstrap is an explicit authenticated POST. All exposed private reads/writes
  filter by owner; forged ownership input is rejected. Suspension remains effective;
  foreign private IDs return 404. Profile changes use row locks and revision checks.
  Frontend bearer tokens remain in SDK memory and account data is subject-scoped.
- Landing **Try Interactive Demo** opens a separate cookie-owned workspace without
  sign-up or AI keys. Each visitor gets Aarav Rao **(fictional)**, fictional resume
  evidence/target, three authored private questions, two simulated assessment
  attempts, one simulated interview, three roadmap tasks and four initial progress
  events. Persistent disclosure and simulation labels prevent real-usage/AI claims.
- Demo task completion is CSRF/Origin protected, owner-scoped and idempotent.
  Reload preserves edits; exit erases only that visitor's principal/private records.
  Expired cookies can be reset safely; live resets still require CSRF. The two-new-
  workspace/hour quota and 24-hour expiry remain enforced. Hourly cleanup erases
  the entire expired private graph. Account credentials never select demo mode.
- Added [AUTHENTICATION.md](docs/AUTHENTICATION.md) with actual Clerk template,
  issuer/key/origin setup, verification behavior and known release limitations.

### Verification for these phases

| Check                      | Actual result                                                                                                                                                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend lint/format        | Ruff passed; 63 Python files formatted.                                                                                                                                                                                                         |
| Backend strict types       | mypy passed for 60 source/test/script files.                                                                                                                                                                                                    |
| Backend tests              | **86 passed** on fresh real PostgreSQL; no skipped integration cases.                                                                                                                                                                           |
| Clean migrations           | New random database: upgrade → metadata check → tests → downgrade to base → upgrade → metadata check passed; created test database removed afterward.                                                                                           |
| Recovery/backfill          | Separate clean migration tests preserve legacy demo IDs/hashes and refuse populated rollback without losing data.                                                                                                                               |
| Ownership/auth             | Real RSA-signed token tests with trusted mock JWKS; invalid claims/signatures, key rotation/outage, suspension, forged owner input, foreign IDs, account/demo confusion, CSRF/expiry/reset and erasure passed.                                  |
| Seeds/content              | Exact 15-title reconciliation, idempotent reruns, editorial preservation and invalid-manifest rejection passed; application seed ran twice successfully.                                                                                        |
| Frontend lint/format/types | ESLint zero-warning gate, Prettier and strict TypeScript passed.                                                                                                                                                                                |
| Frontend unit/build        | **8 tests passed**; native Next.js production build passed.                                                                                                                                                                                     |
| Browser verification       | **5 Chrome tests passed**, including live connectivity, recovery, keyboard/mobile behavior, isolated persistent demo, deletion and missing-key account state. Used a newly created migrated database; temporary API/database removed afterward. |
| Accessibility/visual       | Automated axe checks found **0 violations** in tested views; recruiter demo and foundation screenshots inspected. This is not complete WCAG certification.                                                                                      |
| Startup/database           | Updated native frontend/API started; actual direct/proxied health/readiness connected to PostgreSQL at `0002_relational_model`. Updated backend/migrate/cleanup containers built and started successfully.                                      |
| Contracts/preservation     | OpenAPI export/drift, generated TypeScript types, source hashes and original-file Git diff checks passed.                                                                                                                                       |
| Live Clerk flow            | **Not run:** user confirmed no development keys; complete required setup is documented.                                                                                                                                                         |

`scripts/check_backend.py` now creates a previously nonexistent random test
database and removes only that created database. `scripts/check_browser.py`
provides an isolated repeatable browser check without modifying application quotas;
it refuses an existing API listener and stops only its own temporary process tree.

Windows sandbox process-spawn restrictions were resolved through reviewed local
execution; tests/type checks were not weakened. Docker registry timeouts required
cached backend downloads and a bounded longer timeout. The frontend container
build passed after registry connectivity recovered, including the final pnpm
configuration. Full Compose startup/health and direct/proxied smoke checks passed.
All five frontend page routes returned 200; unauthenticated account access returned
structured 401 with no-store headers. Moved non-authentication pnpm 12 settings
from `.npmrc` into `pnpm-workspace.yaml`, so strict engine checks, bounded fetch
timeout and request concurrency apply. Configured local secret values were absent
from 97 checked source/static files; this was a targeted check, not a security audit.

### Remaining work and next task

- Configure Clerk development keys/issuer and the named 60-second API JWT template,
  then exercise live sign-up, sign-in, profile save and sign-out with two accounts.
  Signed JWTs can remain usable until expiry plus leeway; no instant revocation is claimed.
- Implement the next reviewed deterministic assessment slice with genuinely authored
  published questions/rubrics, saved drafts, grading and submission idempotency.
  The schema and fictional demo history do not constitute those production workflows.
- Real resume/repository ingestion, AI providers, adaptive selection, durable jobs,
  exports/account/source erasure, signed Clerk lifecycle webhooks, consent and backup
  recovery remain later tasks. No upload or AI endpoint was opened here.
- Public HTTPS ingress, trusted proxy/client-IP policy, production CSP, separate
  migration/runtime DB roles and release/security review remain required before
  public release. Current Compose services bind to localhost. CI is configured,
  but no GitHub run occurred because nothing was pushed.

Local entry points: [frontend](http://localhost:3000),
[demo](http://localhost:3000/demo), [liveness](http://localhost:8000/health),
[readiness](http://localhost:8000/api/v1/health/ready).

## Foundation verification archive (2026-10-09)

The following records the earlier foundation phase only. Its phase-specific
counts and deferred work are superseded by the current implementation above.

### Foundation phase

V2 foundation implemented and locally verified on `rebuild/professional-v2`.
V1 baseline: `48fcd90`; preceding architecture documentation: `997f27c`.
The frontend, backend, PostgreSQL, and hourly demo cleanup are running through
Docker Compose on localhost. The one-shot migration service exited successfully.
Temporary native processes used for verification were stopped.

No commit, push, merge, or public deployment was performed. Major product features
remain outside this foundation request.

### Foundation completed work

- Read `AGENTS.md`, the preceding status, `.agent/PLANS.md`, the complete
  [approved architecture](docs/V2_ARCHITECTURE.md), and existing source/data;
  inspected Git status before implementation. Followed the
  [foundation plan](.agent/plans/v2-foundation.md).
- Created the explicitly requested `frontend/`, `backend/`, `docs/`,
  `scripts/`, and `.github/` structure, plus `content/` for preserved editorial
  seeds. These paths replace the architecture's proposed `apps/web/` and
  `apps/api/`; the modular-monolith topology is unchanged.
- Installed pinned frontend dependencies with pnpm 12.8.1 and Python dependencies
  with uv 0.12.24. Both lockfiles are present. Native checks used the existing
  Node 26.8.1/Python 3.12.1 installations; containers use Node 24 LTS/Python 3.12.
- Added Next.js **16.4.0**, React **19.3.0**, App Router, strict TypeScript **5.9.3**
  with unchecked-index checking, Tailwind **4.3.3**, ESLint, Prettier, accessible
  button/card primitives, and a responsive live connectivity screen. No fabricated
  metrics or AI capabilities are displayed.
- Added FastAPI **0.143.0**, Pydantic **2.14.0**, typed pydantic-settings,
  SQLAlchemy **2.1.4** with asyncpg, Alembic **1.20.0**, pytest, Ruff, and strict
  mypy. Configuration and API errors hide secret values; responses have safe
  error envelopes, request IDs, and no-store headers, including unexpected errors.
- Implemented `GET /health` for liveness and `GET /api/v1/health/ready` for real
  PostgreSQL/schema readiness. Next.js forwards `/api/v1/*` to FastAPI.
  Deterministic OpenAPI export and generated frontend types are checked for drift.
- Added the initial versioned migration for expiring demo workspaces, hash-only
  credentials, ownership FK/cascade, and atomic creation limits. Demo requests
  resolve the owner from an opaque HttpOnly cookie; exact Origin checks protect
  bootstrap, CSRF protects reuse, and account bearer credentials never select demo
  mode. No candidate input, upload, or AI operation is accepted.
- Added PostgreSQL **18.6**, persistent Compose storage, localhost-only published
  ports, one-shot migrations, startup health gates, hourly cleanup, and non-root
  application containers. Base images are pinned by digest; builds use frozen
  lockfiles. Only the needed resolver install script is explicitly permitted by
  pnpm's current `allowBuilds` policy.
- Added sanitized configuration examples, random local configuration bootstrap,
  secure ignore rules, CI checks/container builds, dependency-update configuration,
  [development instructions](docs/DEVELOPMENT.md), and
  [legacy migration notes](docs/LEGACY_MIGRATION.md).
- Preserved `app.py`, `questions.json`, and `requirements.txt` byte-for-byte.
  AST/JSON export verifies baseline hashes and retains **15** unique question-title
  drafts and **24** original roadmap suggestions with stable IDs, aliases, and
  provenance. Drafts have no invented prompt, answer, rubric, difficulty, or
  outcome. Unsupported marketing metrics and readiness-tree labels are excluded.

### Foundation verification results

| Check                                    | Actual result                                                                                                                                                                                                  |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend/backend dependency installation | Completed; exact direct pins, lockfiles, frozen reinstall, no peer incompatibilities.                                                                                                                          |
| Frontend startup                         | Native standalone production server and final Compose frontend started successfully.                                                                                                                           |
| Backend startup and liveness             | Native and final container API started; live `GET /health` returned HTTP 200 with the declared JSON contract.                                                                                                  |
| Database connectivity/readiness          | Real PostgreSQL 18.6 connected; native/direct/proxied readiness returned HTTP 200 at revision `0001_demo_foundation`.                                                                                          |
| Frontend lint/types/format               | `pnpm lint`, `pnpm typecheck`, and `pnpm format:check` passed.                                                                                                                                                 |
| Frontend unit tests                      | `pnpm test`: **4 passed**. Covers keyboard activation, valid/malformed responses, API failure, network failure, and retry state.                                                                               |
| Browser checks                           | `pnpm test:e2e`: **3 passed** with installed Chrome 154, including live container connectivity, intercepted 503 recovery, keyboard navigation, and mobile overflow.                                            |
| Accessibility/visual review              | Automated axe WCAG A/AA checks reported **0 violations**; desktop/mobile screenshots inspected. This is not a claim of complete WCAG conformance.                                                              |
| Frontend production builds               | `pnpm build` passed natively; final Docker frontend build passed on Node 24 LTS.                                                                                                                               |
| Backend lint/format/types                | Ruff check/format passed across backend/scripts; strict mypy passed for **28 files**, including tests/scripts.                                                                                                 |
| Backend tests                            | Final `pytest`: **27 passed**, using a migrated disposable real PostgreSQL database for integration cases.                                                                                                     |
| Migrations                               | Application upgrade succeeded. Disposable DB upgrade, downgrade/upgrade round-trip, and metadata drift checks passed; application data was never downgraded.                                                   |
| Live demo identity/persistence           | Two visitors through the frontend received distinct owned workspaces; CSRF reuse returned the same workspace; both survived an API restart.                                                                    |
| Compose                                  | Configuration validation, all image builds, and `up -d --no-build --wait` passed; frontend/backend/PostgreSQL healthy, cleanup running, migration exit code 0.                                                 |
| Contracts/legacy preservation            | OpenAPI drift, generated client regeneration, legacy seed reconciliation/hash checks, and unchanged-original Git diff passed.                                                                                  |
| Credential handling                      | Actual generated local credentials absent from **99** checked source/static-bundle files; local configuration/cache/runtime artifacts remain ignored. This is a targeted check, not a complete security audit. |

The backend verification script runs all backend gates and migration/contract
checks against `interview_prep_test`, guarding against the application database.
Final smoke checks verified frontend HTTP, liveness, real database/schema, and
same-origin forwarding. CI is configured but has not run on GitHub; no push occurred.

### Foundation decisions and fixes

- Use pnpm/uv without an additional workspace orchestration layer. Keep the single
  generated client in the frontend until another consumer needs a shared package.
- Select compatible stable tool versions rather than leave broken peer ranges:
  TypeScript 5.9 matches openapi-typescript's supported range, and ESLint 9 matches
  the plugins currently bundled by eslint-config-next.
- Fixed SQLAlchemy 2.1's missing asyncio/greenlet requirement, pnpm's changed build
  approval configuration, ESLint plugin incompatibilities/config warnings, ESM
  test-tool configuration, and formatting failures without weakening checks.
- Replaced the native `next start` command with the supported standalone entry
  point and static-asset preparation. Verified both that entry point and Docker's
  direct standalone server.
- Keep V1 archival source at the root and outside the V2 runtime. Its dependency
  failures and unsupported claims remain documented in
  [the audit](docs/CURRENT_STATE_AUDIT.md), not ported into V2.

### Foundation limitations at that time

- ESLint 9.39.5 is compatibility-pinned because the bundled React/accessibility/
  import plugins still exclude ESLint 10 in their peer ranges. The registry marks
  ESLint 9 deprecated; review this pin when compatible upstream plugins ship.
  The full configured rules and zero-warning lint gate pass.
- This is a verified local-development foundation. Public HTTPS ingress, trusted
  proxy/client-IP policy, production CSP, separate migration/runtime DB roles,
  account authentication, backup/restore, and release/security review remain
  later work. Behind an unconfigured gateway, the demo creation quota applies to
  the gateway peer address.
- Demo workspaces expire within 24 hours; cleanup runs hourly. There is no learning
  workflow or personal-data ingestion. Accounts, profiles, assessment, grading,
  AI providers, adaptive selection, roadmaps, analytics, jobs, and Project Defense
  are not implemented.
- GitHub-hosted CI, public deployment, performance/load tests, complete manual
  accessibility review, vulnerability audit, and real-model evaluation were not
  performed. Legacy curriculum still needs provenance/license and rubric review.

### Next task proposed at that time

Architecture phase 2: author and review questions/rubrics for one topic, then
implement a durable objective-assessment slice with owned persistence, saved
drafts, deterministic grading, duplicate-submit protection, and minimal results.
Keep accounts, ingestion, AI, and Project Defense within their later phases.

### Foundation local entry points

- Frontend: [http://localhost:3000](http://localhost:3000)
- Liveness: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)

Stop with `docker compose down`; retain the database volume during ordinary
shutdown. Reproduce setup and checks using [README.md](README.md) and the
[development guide](docs/DEVELOPMENT.md).
