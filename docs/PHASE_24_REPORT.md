# Phase 24 deployment verification

Verified 24 October 2026 (Asia/Calcutta). The public recruiter demo is deployed
and reachable. Production accounts and real hosted xKiro remain disabled. This
phase does not certify the complete account platform for public personal data.

## Deployment and source

| Item                | Verified state                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Website             | <https://interview-prep-ai-icyshimakaze.vercel.app>                                                              |
| Backend             | <https://interview-prep-api-icyshimakaze.onrender.com>                                                           |
| Repository          | <https://github.com/icyshimakaze/interview_prep_AI>                                                              |
| Branch              | `rebuild/professional-v2`                                                                                        |
| Running source      | `c5ca23ea5a8b1d502f6e53d22b32b3bdde73debb` on both hosts                                                         |
| Inspection baseline | `71d525c80216e4805c3a6ac68d592f01cbd50f15`; documentation-only changes after the deployed source                 |
| Render              | `srv-dbdrrr9srm7s73cpdt6g`, My Workspace, Singapore, Docker, one Free instance, auto-deploy off                  |
| Render deployment   | `dep-dbdrrs9srm7s73cpe00g`, `live`                                                                               |
| Vercel              | `prj_wsxEcvVC17paXs5pco4K9eHwWKgd`, personal Hobby deployment, production, Singapore functions                   |
| Vercel deployment   | `dpl_AprjfXimTGg9oVJ9zP5ich1kYq9L`, `READY`, canonical alias verified                                            |
| Neon                | Existing selected `production` branch, Singapore, `neondb`, ready; no database created or migrated in this phase |

Both the [baseline CI](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40017869418)
and [deployed-release CI](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40012341296)
were read through GitHub's public API and reported completed/success. The local
changes described below are not yet pushed or deployed. The user requires
separate authorization for any Git push; no default-branch merge is planned.

## Security checkpoint and database

- Git was clean at the start. No actual dotenv file is tracked or found by
  filename in reachable Git history. Examples, lockfiles and CI are committed.
- A final scan of 471 tracked/new release files and 23 browser JavaScript files found zero matches
  for five configured private values and the checked credential patterns. No
  `XKIRO_API_KEY` reference exists in frontend application source. This is a
  bounded scan, not a claim of exhaustive secret detection.
- The production image's allowlist excludes dotenv files; production has no
  reload/debug documentation routes. Backend errors/logs omit private request
  content, tested by the current backend suite.
- Hosted Neon read-only SQL and frontend/backend readiness confirm
  `0012_ai_context_reviews`. The runtime role has no schema CREATE, migration
  history UPDATE or `neon_superuser` membership. Runtime connections use verified
  TLS and the existing bounded direct-connection pool.
- Startup performs read-only schema validation. No production migration, seed,
  data reset or role change was needed. Disposable local migration and recovery
  of the migration chain passed independently.
- A full backup/local restore drill was prepared but did not execute: automatic
  approval review rejected exporting the complete production database because
  it could transfer personal data into a local archive. Explicit user approval
  is required before that export. No backup file was created by that action;
  data recovery remains unverified.

## Fresh checks

| Check                                                  | Result                                                       |
| ------------------------------------------------------ | ------------------------------------------------------------ |
| Backend Ruff lint/format                               | Passed; 209 files already formatted                          |
| Backend strict mypy                                    | Passed; 196 sources                                          |
| Backend pytest                                         | 628 passed in 492.79 seconds                                 |
| Fresh migrations, complete downgrade/upgrade and drift | Passed on a disposable local database                        |
| OpenAPI and legacy hashes/seeds                        | Passed                                                       |
| Frontend zero-warning lint and strict types            | Passed                                                       |
| Frontend Vitest                                        | 166 passed across 18 files                                   |
| Ordinary Next.js production build                      | Passed                                                       |
| Production-mode gateway build and container harness    | Passed                                                       |
| Full local browser suite                               | 25 passed in 1.2 minutes; temporary servers/database removed |
| Hosted public pages                                    | 1 passed; Chrome, four requested widths                      |
| Hosted full two-visitor journey                        | Pending the normal production quota window                   |

The first Vitest invocation could not start a Windows subprocess (`spawn EPERM`)
inside the sandbox. Running the unchanged test command with approved subprocess
access passed; no test/configuration was weakened. The production harness used
temporary TLS PostgreSQL, restricted grants, a non-root 512 MiB API and mock AI.
It verified schema 0012, 29 publications with zero repeat writes, cookies/CSRF,
gateway spoof rejection, quotas and cleanup, then removed its owned containers
and ephemeral credentials. Existing local application services were preserved.

Fresh hosted HTTP checks passed for landing HTTPS, backend `/health`, both direct
and proxied readiness, unauthenticated demo rejection, closed accounts, direct
backend rejection, exact canonical CORS and foreign-origin rejection. The 12
JavaScript assets referenced by the landing page returned 200 with no configured
private-value matches. Gateway rejection also prevents anonymous access to backend
debug paths; production route disabling is separately verified in code/tests.

The hosted public Chrome check exercised 375, 768, 1440 and 1920 pixel widths,
without horizontal overflow, with zero axe WCAG 2 A/AA and 2.1 AA violations on
the landing page. Keyboard navigation, the privacy page and unavailable account
routes passed with no console/page errors. These checks used real public pages,
without intercepted API responses or live AI.

## Authentication and real AI

The user confirmed that no owned domain or production Clerk setup exists.
[Clerk's production guide](https://clerk.com/docs/guides/development/deployment/production)
requires an owned domain and DNS access, matching live keys, relevant OAuth
credentials and production certificate deployment. Development keys, fabricated
issuers or disabled ownership verification are not substitutes.

Before enabling accounts:

1. Implement full account export/erasure, Clerk identity deletion reconciliation
   and the reviewed strict script CSP. Profile deletion currently preserves
   preparation history.
2. Configure an owned domain and Clerk production instance, exact authorized
   origin/subdomain policy, `interview-prep-api` JWT template/audience, issuer,
   sign-in/sign-up/sign-out paths and any actual provider OAuth callbacks.
3. Enter keys directly in the hosting dashboards. Rebuild/redeploy both profiles
   together, then verify real sign-in/out, token failures and two-account isolation.
4. Configure backend xKiro, preserving both requested `:free` IDs, zero retries,
   conservative shared budgets and `XKIRO_ALLOW_PAID_MODELS=false`. Keep `/demo`
   pinned to mock.
5. Run bounded synthetic provider/feature tests, including validation, saved-result
   reuse and failure behavior, after account prerequisites are satisfied.

No xKiro key was copied to a host, and no real AI request was made in Phase 24.
The historical Max-free connectivity/resume evidence in PROJECT_STATUS remains
historical. Hosted real-provider authentication, resume/JD reviews, answer and
follow-up generation, roadmap suggestions and project questions are **unverified**.
Live Omni availability is also unverified. Mocked provider/quota/failure and
account-ownership regressions are included in the 628 passing backend tests.

## Environment configuration by name

The current Vercel production API returned exactly:

- `BACKEND_INTERNAL_URL`
- `FRONTEND_ORIGIN`
- `BACKEND_PROXY_SECRET` (sensitive)
- `PUBLIC_DEMO_ONLY`
- `ENABLE_EXPERIMENTAL_COREPACK`

No Clerk variable is configured there. Values were not decrypted or printed.
The Render creation configuration used the following names; its connector does
not expose a read/list operation for the current environment collection:

`APP_ENV`, `PUBLIC_DEMO_ONLY`, `AUTH_ENABLED`, `AI_PROVIDER`, `DATABASE_URL`,
`DATABASE_SSL_MODE`, `DATABASE_CONNECT_TIMEOUT_SECONDS`, `ALLOWED_ORIGINS`,
`BACKEND_PROXY_SECRET`, `DEMO_RATE_LIMIT_KEY`, `DEMO_TTL_SECONDS`,
`INTERVIEW_WORKER_ENABLED`, `INTERVIEW_POLL_SECONDS`, `CLEANUP_ENABLED`,
`FILE_WORKER_SLOTS`. Render supplies `PORT`. Current public account rejection and
production settings validation are consistent with the initial mock-only profile.

Pending account settings are `AUTH_ISSUER`, `AUTH_AUDIENCE`,
`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `XKIRO_API_KEY`,
`XKIRO_BASE_URL`, `XKIRO_MODEL_SMART`, `XKIRO_MODEL_MULTIMODAL`,
`XKIRO_ALLOW_PAID_MODELS`, `AI_TIMEOUT_SECONDS`, `AI_MAX_RETRIES`,
`AI_OWNER_HOURLY_CALLS`, `AI_OWNER_DAILY_CALLS` and `AI_GLOBAL_DAILY_CALLS`, together
with the coordinated profile flags. See [the complete examples/runbook](DEPLOYMENT.md).
No backend database/AI secret belongs in browser configuration.

## Budget, limitations and manual actions

Render's live API reports compute `free`; `buildPlan: starter` names the separate
[default build tier](https://render.com/docs/build-pipeline), not paid web compute.
The user confirmed no Render payment method is saved. [Render documents](https://render.com/docs/free)
that exhausted allowances then suspend services/builds rather than purchasing
overages. No payment method, paid plan, domain, credits or billing feature was added.

Vercel Hobby and the selected existing Neon Free database remain the recorded
plans. Their [Hobby](https://vercel.com/docs/plans/hobby) and
[Neon Free](https://neon.com/docs/introduction/plans) terms were checked. Current
account billing details could not be independently read: Vercel team read returned
403, and its documented authorization-recovery call also returned 403; no fallback
credentials/browser session were available and no bypass was attempted. Neon's
connection is project-scoped and does not expose account-plan/payment inspection.

Free hosting can sleep, restart or suspend; physical expiry cleanup waits until
the process next runs successfully. There is no availability or deletion SLA.
Large synchronous AI batches can exceed browser/gateway waits. Demo creation is
limited to two visitors per network per UTC hour; no quota was reset. Current
Render platform health checks are TCP; set `/health` in its service Settings if
HTTP platform probes are desired. Manual liveness/readiness checks already pass.

The local Settings copy now states that access expires within 24 hours and
physical deletion can be delayed while hosting sleeps. Publishing that change
requires the separately authorized branch push and a verified production release.

## Recruiter readiness

The public mock demo can be shared as a portfolio preview with its explicit
simulation and free-hosting limitations. Complete hosted journey verification is
pending as recorded above. Do not present account registration, hosted real AI,
model accuracy or full data recovery as verified. No new deployment was triggered
in this phase while prerequisites and Git publication remain pending.
