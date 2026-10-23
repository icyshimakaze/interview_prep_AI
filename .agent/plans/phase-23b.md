# Phase 23B — free-tier deployment preparation

## Objective and scope

Prepare, but do not provision, push or deploy, the existing Next.js/FastAPI app
for Vercel + one Render Free web service + Neon. Keep Clerk and account xKiro
support alongside the isolated deterministic demo. Preserve existing work and
actual secret files. No paid cron/service, new platform or additional live AI call.

## Verified gaps and affected components

- Existing render.yaml provisions paid Starter + cron; replace with a free web
  service and in-process expiry maintenance while awake. Document delayed physical
  deletion during sleep, immediate expiry denial, and manual operator cleanup.
- Check production database/schema once at startup; use /health for Render so
  periodic probes do not keep Neon awake. Keep explicit DB readiness endpoint.
- Bound idle interview polling through a real configured interval; mutation and
  owned-read wakeups preserve interactive response and restart recovery. No
  background scheduler can guarantee progress while a free service is stopped.
- Fail safely for missing selected production AI/auth/security configuration.
  Preserve zero-key mock production demo and development defaults.
- Add content-free request metadata logging; no bodies, query strings, raw paths,
  credentials, authorization headers or personal identifiers in application logs.
- Keep exact origins, gateway trust, TLS/direct small DB pool, operator migrations,
  ephemeral raw files, existing provider budgets/validation and frontend same-origin API.
- Refresh Docker/CI/profile examples, production/auth/free-tier runbook and status.

## Database and API

No schema changes or migrations needed; current head remains 0012. Startup must
never migrate, seed or create tables. Run migration verification only on disposable
databases, preserve the existing application database. No public cleanup/admin
endpoint. Public health contracts stay compatible; production docs/OpenAPI UI off.

## Frontend and privacy

Native Vercel monorepo root frontend/, pinned pnpm/workspace lock, explicit HTTPS
server-only backend origin/gateway credential. Account profile requires both Clerk
keys and canonical authorized origin; demo-only profile needs neither. Update
retention wording for sleeping services without claiming scheduled deletion SLA.
Show safe existing cold-start/retry states and retain answers after errors.

## Verification and order

1. Read current code/config/tests and official Render/Vercel/Neon/Clerk docs.
2. Implement small lifecycle/config/logging changes with boundary/failure tests.
3. Replace paid deployment default; document both mock-only and account+xKiro
   profiles, exact variables, dashboard steps, migrations, backups, limits and costs.
4. Run backend full lint/types/tests/migration roundtrip/contracts, frontend
   lint/typecheck/tests/build, production-container TLS/runtime/grants/connectivity
   harness, and Playwright recruiter flow. Mock all AI; no hosted operations.
5. Review secret/build-context/logging checks, clean only owned test resources,
   and record exact results and account-dependent blockers in status/report.

## Outcome

Complete. Replaced paid defaults with one Free web API, added lifecycle/config/
logging controls and both configuration profiles, and completed the A–S runbook.
Backend gate: 628 tests plus strict checks, migration round-trip/drift, contracts
and legacy preservation passed. Frontend: 166 tests, lint/types/build, formatting
and generated-contract equality passed. Production TLS/runtime/grants/gateway
harness passed with a 512 MiB API; 25 Playwright tests passed. Actionlint, Compose,
credential/build-context checks and Git whitespace passed. Owned test resources
were cleaned; no existing application data/services or secret files were changed.

No hosted operation, paid provisioning, push or live AI request. Real production
authentication, domains/DNS, repository integration, secret entry, backup/recovery
and deployment remain user account actions. Existing account export/erasure,
identity deletion reconciliation and strict script CSP remain engineering release
gaps before broad personal-data use. See [the report](../../docs/PHASE_23B_REPORT.md).
