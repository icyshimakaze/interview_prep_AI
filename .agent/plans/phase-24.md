# Phase 24: verify and complete the free hosted release

## Objective and scope

Verify the existing Vercel/Render/Neon deployment against current code and actual
tests. Complete safe deployment configuration and deployment-related fixes while
preserving the credit-free recruiter demo. Enable account/xKiro mode only when
production Clerk configuration and the documented account security/privacy
release requirements are satisfied. No paid resources or automatic billing.

The user authorizes free-tier deployment actions but requires a separate explicit
authorization before any Git push. Preserve existing secret files and unrelated
hosting resources. Never print credentials or create duplicate services.

## Components and boundaries

- Inspect current provider state, environment-variable names, CI and release SHA.
- Inspect tracked files and browser artifacts for credentials without printing
  matching values. Production debug endpoints stay disabled.
- Reuse the existing deployment files, locked dependencies and build scripts.
- Database/API changes: none planned. Verify revision 0012 and runtime ownership
  grants read-only. Do not reapply migrations without an actual schema need.
- Frontend: correct deployment-related copy or behavior found by verification;
  preserve saved data, navigation, accessibility and explicit simulation labels.
- Account export/erasure, Clerk deletion reconciliation and strict script CSP are
  existing release gaps. Record their exact status; do not weaken these gates.
- Real AI requests require the account deployment prerequisites, backend-only
  credentials and explicit synthetic-input consent. Preserve free model IDs,
  bounded budgets, output validation and the demo's unconditional mock provider.

## Order and verification

1. Verify authentication, exact resources/plans, CI, security and environment
   prerequisites. Ask only for missing non-secret account/domain information.
2. Run current backend lint/types/tests/migration checks against disposable local
   PostgreSQL; frontend lint/types/tests/build and production packaging as needed.
3. Probe canonical HTTPS frontend/backend, schema readiness, gateway, CORS and
   closed account behavior. Never reset production quotas.
4. Run one bounded hosted two-visitor journey, responsive/keyboard/console checks
   at 375, 768, 1440 and 1920 pixels, and authenticated deletion of test visitors.
5. Fix relevant issues, rerun affected checks, prepare a reviewed commit. If a
   push is necessary, request authorization for the exact branch/destination
   after all locally verifiable work is ready. No force push or default-branch
   merge.
6. Deploy only a verified available source revision and compatible configuration.
   Verify terminal provider status and real URLs before reporting success.
7. Update README, deployment runbook, PROJECT_STATUS and a Phase 24 report with
   exact results, failures, environment names, revision and remaining manual work.

## Recovery and completion

Do not alter production data as a workaround or run destructive migrations.
Existing data requires a verified recoverable backup before schema changes.
Rollback only to a schema-compatible application version. Report unavailable
account/billing scope honestly and leave the usable demo intact while blocked
account-dependent work remains pending.

## Current outcome

Fresh backend/frontend quality gates, the production harness and 25 local browser
tests pass. Hosted public pages pass at all four requested widths. Both live hosts
still run c5ca23e; inspection-baseline CI is green. No owned domain/production
Clerk setup exists, so account/live-AI mode remains disabled. A full production
export was rejected by automatic approval review before execution and requires
explicit permission. Render has no saved payment method, as confirmed by the user.

The complete hosted journey is waiting for the normal 21:00 UTC quota window.
Retention-copy correction, refreshed verification documentation and two inspected
hosted landing screenshots are ready for review. No push or new deploy yet.
