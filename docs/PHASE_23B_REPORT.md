# Phase 23B — production deployment preparation report

23 October 2026, Asia/Calcutta. No push, hosted deployment, paid provisioning,
application-data migration or change to actual dotenv files occurred.

## Production readiness status

**Preparation complete and locally verified for a small public recruiter demo.**
The prepared topology is Vercel + **one Render Free Docker web service** + Neon,
with the existing Clerk integration for accounts and xKiro for opted-in account AI.
The default Blueprint remains a zero-key mock-only recruiter profile. A documented
account profile enables Clerk + xKiro on the **same app**, while `/demo` stays
deterministic and independent of real-provider outages. No new platform was added.

This is a portfolio preview, not an availability guarantee or clearance to collect
sensitive personal data. Hosted credentials/DNS/auth flows still need manual setup;
existing account export/erasure, Clerk deletion reconciliation and strict script
CSP gaps remain before broad personal-data registration. Use fictional controlled
accounts or the mock-only demonstration while resolving them.

## Changes and files

| Area                          | Files changed in this phase                                                                                                                                                                                                                                                                       | Result                                                                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hosting/profile templates     | `render.yaml`, `deploy/backend.env.example`, new `deploy/backend.account.env.example`, new `deploy/frontend.account.env.example`                                                                                                                                                                  | One free API, no paid cron/worker/disk/DB; complete separate configuration profiles for the same app                                                          |
| Production settings           | `backend/src/interview_prep/core/config.py`                                                                                                                                                                                                                                                       | Selected production provider credentials/auth are mandatory; reject security/database placeholders; real bounded cleanup/poll/file-capacity settings          |
| Startup and readiness         | new `backend/src/interview_prep/db/readiness.py`, `api/health.py`, `main.py`                                                                                                                                                                                                                      | Bounded read-only schema check before production serves; no startup DDL/seed; public liveness and separate DB readiness; production debug/OpenAPI off         |
| Expiry and work lifecycle     | `cleanup.py`, `modules/interviews/worker.py`, `modules/interviews/router.py`                                                                                                                                                                                                                      | Cleanup at startup/hourly while awake; configurable idle polling, owned-read/mutation wakeups and lost-wakeup regression fix                                  |
| File capacity                 | `modules/resumes/upload.py`, `modules/projects/ingestion.py`, `main.py`                                                                                                                                                                                                                           | Shared bounded PDF/project pool; free profile selects one slot; trusted static parsers remain unchanged                                                       |
| Logging and transport headers | new `core/request_logging.py`, `serve.py`, `main.py`, `frontend/next.config.ts`                                                                                                                                                                                                                   | Content-free route-template request logs, raw access logs off, HSTS in Vercel production, live Clerk keys mandatory for account profile                       |
| Local/CI isolation            | `.env.example`, `compose.yaml`, `.github/workflows/ci.yml`, `scripts/test_support.py`                                                                                                                                                                                                             | Explicit new controls, mock CI with no real AI credentials; Compose retains separate cleanup behavior                                                         |
| Production verification       | `scripts/check_production.py`                                                                                                                                                                                                                                                                     | Free-profile settings and 512 MiB API container in existing TLS/runtime/grants/gateway harness                                                                |
| Tests                         | `backend/tests/test_deployment.py`, new `test_production_lifecycle.py`, new `test_production_accounts.py`, `frontend/tests/deployment-config.test.ts`                                                                                                                                             | Missing config, startup schema failure, privacy-safe logs, cancellation/retry, shared capacity, idle wakeups and signed account/outage/demo boundary coverage |
| Product/privacy copy          | `frontend/src/app/privacy/page.tsx`, `README.md`                                                                                                                                                                                                                                                  | Honest retention wording for sleeping services and both deployment profiles                                                                                   |
| Documentation                 | `docs/DEPLOYMENT.md`, `docs/AUTHENTICATION.md`, `docs/AI_ARCHITECTURE.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/RESUME_PRIVACY.md`, `docs/PROJECT_DEFENSE.md`, `docs/XKIRO.md`, `docs/adr/0001-managed-deployment.md`, this report, `PROJECT_STATUS.md`, `.agent/plans/phase-23b.md` | Complete A–S runbook, free-tier decision amendment, exact config/commands and explicit blockers                                                               |

Paths in the backend rows are relative to `backend/src/interview_prep/` unless
already qualified. Existing uncommitted work was preserved; no unrelated refactor,
dependency change, schema change or new migration. Head stays `0012_ai_context_reviews`.

## Exact verification results

| Check                        | Actual result                                                                                                                                                                                                                                       |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Complete backend gate        | **628 passed in 435.83 seconds**                                                                                                                                                                                                                    |
| Backend lint/format          | Ruff passed; **209 files** formatted                                                                                                                                                                                                                |
| Backend strict types         | mypy passed; **196 source files**                                                                                                                                                                                                                   |
| Migrations                   | Fresh upgrade to 0012, full downgrade/upgrade round-trip and zero schema drift passed on disposable PostgreSQL                                                                                                                                      |
| Contracts/content            | OpenAPI equality, regenerated TypeScript equality and legacy hashes/seeds passed                                                                                                                                                                    |
| Frontend tests               | **166 passed across 18 files**                                                                                                                                                                                                                      |
| Frontend lint/types          | Zero-warning ESLint and strict TypeScript passed                                                                                                                                                                                                    |
| Frontend builds              | Vercel-production gateway build in the TLS harness, production browser build, and final ordinary native production build all passed                                                                                                                 |
| Production image/startup     | Linux Docker image built; non-root API with **512 MiB** container memory started using verified TLS, restricted grants and migration 0012                                                                                                           |
| Local production integration | HTTPS frontend/backend + PostgreSQL TLS, exact origins, secure cookie/CSRF, direct/spoofed gateway rejection, quotas and cleanup passed; 29 catalogue versions published, repeat publication wrote zero                                             |
| Browser suite                | **25 Playwright tests passed**, one Chrome worker; persisted recruiter journey, two-visitor isolation, resume/target/skills, assessments, interviews, roadmap/progress, Project Defense, recovery, desktop/mobile/keyboard and automated axe checks |
| Workflow/config              | Actionlint, Compose config validation with root/backend dotenv inputs, repository Prettier and Git whitespace checks passed                                                                                                                         |
| Credential checks            | Four configured private values absent from **436 checked source files** and **23 browser JS files**; no actual env files tracked now or found by filename in reachable Git history; production image contains no dotenv files                       |

The first full backend run found one new test incorrectly expecting demo bootstrap
HTTP 201; the existing contract is 200. Corrected that assertion, verified the
focused combined account/demo test, then repeated the complete gate successfully.
No tests, types or lint rules were disabled or relaxed.

The production account test uses signed test JWTs/JWKS and mocked xKiro HTTP. It
verifies a real-provider error preserves owned context and leaves the cookie-based
demo available with mock feedback and no extra provider call. Its DB TLS is a
test-only override; the separate container harness exercises real TLS/hostname
verification. No live Clerk/browser login or hosted ingress was claimed.

All verification-owned databases, servers/containers and generated runtime secrets
were removed. Older unrelated local services/data were not stopped or migrated.
Generated ignored test/build artifacts remain local. No real xKiro request was
made in Phase 23B; Phase 23A's one synthetic success is historical evidence only.

## Production configuration still needed

Follow [DEPLOYMENT.md](DEPLOYMENT.md) A–S. It includes exact repository settings:

- **Render:** Docker at repository root; `deploy/backend.Dockerfile`, context `.`,
  `plan: free`, one API, CMD `python -m interview_prep.serve`, `0.0.0.0:$PORT`,
  health `/health`; startup checks database revision read-only. Runtime database
  URL, verified TLS, exact HTTPS origins, stable generated quota/gateway secrets,
  `CLEANUP_ENABLED=true`, `INTERVIEW_POLL_SECONDS=600`, `FILE_WORKER_SLOTS=1`.
- **Vercel:** root `frontend`, allow files outside root, Node 24.x, pinned pnpm,
  install `cd .. && pnpm install --frozen-lockfile`, build `pnpm build`, Corepack
  flag, HTTPS `BACKEND_INTERNAL_URL`, canonical `FRONTEND_ORIGIN`, matching
  server-only gateway secret and explicit profile. No new browser API-base var.
- **Neon:** Free project, nearby region, direct asyncpg URL, CA/hostname verified
  TLS, restricted runtime role, operator-only owner credentials, reviewed forward
  migrations/catalogue publication and repeated runtime grants. No startup seed
  or persistent local filesystem/SQLite.
- **Account profile:** Clerk production domain/DNS/certificates, matching live
  publishable/server keys on Vercel, `AUTH_ENABLED=true` and trusted issuer/audience
  on Render. JWT template `interview-prep-api`, RS256, 60 seconds/5-second leeway;
  canonical paths/redirects/origins. No generic invented OAuth callback URL.
- **xKiro on Render only:** `AI_PROVIDER=xkiro`, secret `XKIRO_API_KEY`, fixed
  base URL, `XKIRO_MODEL_SMART=qwen/qwen3.8-max:free`,
  `XKIRO_MODEL_MULTIMODAL=qwen/qwen3.8-omni-flash:free`, paid flag false. Account
  example uses zero transport retries and owner-hour/day/global-day budgets
  **10 / 30 / 100**, with a maximum 60-second deadline.

Both profiles keep a no-key **Try Interactive Demo**. Its dataset initializes per
visitor, never into real user accounts. The global reviewed question catalogue is
published explicitly and idempotently by the migration operator.

## Expected free-tier limitations

Render Free sleeps/restarts and lacks a free cron/shell/one-off-job facility;
CPU/memory, instance-hours, traffic and build quotas constrain reliability.
[Render Free limits](https://render.com/docs/free),
[compute plans](https://render.com/docs/compute-plans).
The local 512 MiB test is not a hosted 0.1-CPU benchmark or load guarantee.

Expired demo access is denied immediately by authorization, but physical cleanup
and interview progress cannot run while a service is stopped. Expired rows can
remain until a subsequent successful startup/maintenance or explicit operator
cleanup. The privacy page and runbook now say this. Never advertise an unconditional
hourly deletion SLA. Long synchronous evaluations/cold starts can exceed browser
or gateway waits; reload persisted work before an explicit bounded retry.

Neon compute/storage/transfer and restore limits require monitoring; Vercel Hobby
has personal/non-commercial eligibility and usage caps. Clerk production requires
an owned domain/DNS, which may be a separate cost if unavailable. xKiro free models
may be throttled/unavailable. None of these limits triggers paid provisioning or
paid-model fallback in this preparation. [Neon plans](https://neon.com/docs/introduction/plans),
[Vercel Hobby](https://vercel.com/docs/plans/hobby),
[Clerk production](https://clerk.com/docs/guides/development/deployment/production).

## Personal account interaction and release blockers

1. Choose the canonical frontend domain and profile. If no owned Clerk-capable
   domain is available, use the mock-only demo; no domain purchase was authorized.
2. Authorize GitHub/Vercel/Render connections and review the exact free resource
   preview. Keep automatic Git deployments off until authorized to release.
3. Create/select Neon Free, set role passwords privately, verify backup/recovery,
   authorize and apply actual production migrations/grants from the reviewed image.
4. Enter runtime secrets in the correct provider dashboards; never send them in
   chat. Confirm regional endpoints, origins and provider spending controls.
5. For accounts, complete Clerk production DNS/certificates/JWT/OAuth settings and
   test actual sign-in, refresh, sign-out and two-account isolation. Resolve the
   documented engineering privacy/script-CSP gaps before broad sensitive-data use.
6. Only after separate release authorization: deploy the reviewed commit, verify
   direct/proxied readiness and isolated demo journeys, then one synthetic account
   AI review with disclosure/consent and expected provenance. No batch live tests.

The existing local application still needs the previously documented image and
0012 migration refresh; Phase 23B verification did not update its running stack.
No public URL, hosted auth callback, backup restore or cloud dashboard setting was
verified. Nothing was pushed, deployed or provisioned on a paid plan.
