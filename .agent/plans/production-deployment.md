# Production deployment preparation

## Objective and scope

Prepare, document and locally verify Vercel + Render + Neon deployment with
`AI_PROVIDER=mock`, no OpenAI credential and no remote deployment. Preserve all
existing UI/cleanup work and business behavior. The historical architecture chose
a VM, not Render/Railway; record a superseding managed-hosting ADR selecting Render.

## Verified gaps and affected components

- Next.js already forwards same-origin `/api/v1` requests. Production must require
  explicit HTTPS backend/frontend origins and a server-only gateway credential.
- API quotas currently use the socket peer. Trusting arbitrary forwarded headers
  would permit spoofing; relying on the peer behind Vercel groups every visitor.
  Add an authenticated gateway handoff from Vercel's sanitized client-IP header,
  reject direct private/API calls, and retain normal ownership/CSRF checks.
- SQLAlchemy/asyncpg currently lacks an explicit verified TLS setting. Neon libpq
  URL parameters are not interchangeable with asyncpg arguments. Use direct Neon
  endpoints with a small application pool and an explicit verified SSL context.
- Docker backend context excludes the authored catalogue. Add a production
  Dockerfile containing backend + reviewed content, a `$PORT`-aware entry point,
  explicit migration/seed step and scheduled expiry cleanup.
- Public-demo profile must fail closed if authentication or a remote AI provider
  is enabled. Accounts and optional providers remain separately documented later
  profiles, with existing ownership and provider safeguards preserved.

## Database, API and frontend behavior

No schema or response-contract changes; apply existing migrations through head.
Use separate migration/runtime roles, least-privilege SQL grants, no data reset or
shared demo account. Catalogue publication is explicit and idempotent; fictional
workspaces initialize per visitor. Existing secure cookies remain same-origin
through Vercel. CORS enumerates the canonical HTTPS frontend only; previews use
separate databases/backends and secrets. No wildcard callback/origin exceptions.

## Security and privacy

Secrets remain in platform environment stores and ignored local configuration.
Gateway credential is not user authorization. Only an authenticated gateway may
supply a quota address; never trust generic browser forwarding headers. Health
endpoints remain sanitized and usable by platform checks. Demo expiry cleanup is
required even when no visitors arrive. No real inputs, provider calls, cloud
resource creation, credentials changes, deployment or push.

## Implementation order

1. Verify official hosting/TLS/auth requirements; write ADR and safe configuration.
2. Add narrowly scoped startup/TLS/gateway/public-demo guards and meaningful tests.
3. Add platform manifests, environment examples, role grants and exact runbook.
4. Verify production builds and production-mode HTTPS/secure-cookie/CORS/gateway,
   migrations/seeding/cleanup on disposable local data, with mock AI and empty keys.
5. Run relevant backend/frontend checks, review configuration for secret exposure,
   and update PROJECT_STATUS.md with results, limits and the undeployed next step.

## Acceptance

No AI API credential is required for the public profile. Exact account/resource,
environment, migration, seed, callback and deployment steps are reviewable. Free
account credentials are distinguished from potential hosting charges and optional
AI keys. Production-like local verification actually runs; unverified hosted
behavior is identified. No public deployment takes place.

Outcome: Complete; prepared and locally verified, not deployed.

Render is selected in ADR 0001. Production manifests, a non-root backend image,
verified database TLS, restricted runtime grants, mock-only public-demo guards,
authenticated frontend gateway and exact operator runbook are in place. Existing
schema, response contracts and working business behavior are preserved.

Verification passed: 551 backend tests, 147 frontend tests, 25 browser tests,
backend/frontend lint and types, production builds, manifest schemas, formatting,
and the disposable production-mode TLS/migration/seed/cookie/CORS/quota/cleanup
harness. The ordinary local frontend build target was restored afterward.
Ephemeral credentials were removed. No hosted resources, deployment or push.
Live platform/auth/backup checks remain the documented release procedure after
separate authorization; Render compute costs are distinct from optional AI costs.
