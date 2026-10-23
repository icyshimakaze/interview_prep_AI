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
tests pass. Hosted public pages pass at all four requested widths. The frontend
now runs CI-approved 7e6bcfd; unchanged backend/deployment Git trees remain on the
existing healthy c5ca23e service. No owned domain/production
Clerk setup exists, so account/live-AI mode remains disabled. A full production
export was rejected by automatic approval review before execution, and the user
chose to defer the drill. Render has no saved payment method, as confirmed by the user.

The hosted suite ran in the normal 21:00 UTC window: one passed, one failed.
Questions/assessments passed; interview creation showed signal timed out and its
answer field never appeared. Render has successful GET logs but no completed
interview POST; Vercel runtime log access is 403. Root cause remains unresolved.
Two-visitor isolation/UI exit and remaining hosted workflows were not completed.
An operator diagnostic-runner stdin error consumed and cleaned the second visitor
without testing interview creation. Final counts are zero workspaces/sessions;
next normal quota window is 22:00 UTC / 03:30 IST. No quota reset or speculative
timeout/security change occurred. Full recruiter readiness remains unverified.
Retention-copy correction, refreshed verification documentation and two inspected
hosted landing screenshots were committed/pushed with explicit authorization.
Release CI 40021576996 passed every job. Vercel deployment
dpl_4CnVhRSUVR3LCk8HwGRhp8s2Nwgq is READY and post-release HTTP checks passed.
