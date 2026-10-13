# Authentication and recruiter demo

Date: 2026-10-12 (Asia/Calcutta).

Complete the pending relational model as the prerequisite for this requested
account/demo slice. Preserve existing foundation work and legacy source.

- Clerk owns sign-up, sign-in, and sign-out. FastAPI independently verifies a
  trusted RS256 API-template JWT: issuer, audience, expiry, issued-at, not-before,
  authorized party, bounded lifetime, and configured JWKS. Cache trusted keys
  with bounded refresh and fail closed. Never follow token-provided key URLs.
- Resolve a local account principal from issuer/subject. Reusable account and
  demo dependencies enforce active state; invalid account credentials cannot
  fall back to a demo cookie. All private queries receive the resolved owner.
- Implement an authenticated dashboard with structured 401/403 errors. Reject
  client-supplied ownership fields. Keep bearer tokens in SDK memory; no custom
  passwords or browser token persistence.
- Landing CTA is exactly “Try Interactive Demo”. Bootstrap a separate expiring
  workspace, transactionally seed a fictional candidate and a small amount of
  clearly labeled simulated history, and expose only that visitor's records.
  Demo creation/reuse uses existing Origin/CSRF/quota rules and no inference.
- The user confirmed no Clerk keys are available. Ship complete configuration
  instructions and an explicit account-setup state; do not claim a live Clerk
  sign-up was tested. Demo must work without those credentials.
- Run clean PostgreSQL migration/rollback/upgrade and all backend gates. Test
  signed tokens through mocked trusted JWKS, claim/signature failures, key
  rotation/outage, ownership/foreign IDs, account/demo confusion and expiry.
  Run frontend lint/types/unit/build and browser demo checks with actual services.
- Update architecture, schema/auth/development instructions and project status.
  No push, merge, deployment, paid API calls or external account creation.

Outcome: implemented and locally verified. Reusable verified-token/account/demo
dependencies, owner-scoped account dashboard/profile and resource reads, Clerk UI
integration/sign-out, and isolated fictional recruiter workspaces are complete.
The full PostgreSQL suite passed 86 tests; frontend lint/types/format, eight unit
tests and a native production build passed. Five browser tests against a fresh
database passed, including isolated visitor edits, persistence, foreign-ID rejection,
deletion, connectivity, accessibility and the missing-key setup state. Temporary
test API/database were removed. Live Clerk-managed account flows require the keys
the user confirmed are unavailable; docs/AUTHENTICATION.md gives the exact setup.
See PROJECT_STATUS.md for final service/container verification and release limits.
