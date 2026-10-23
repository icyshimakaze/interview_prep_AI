# ADR 0001: Vercel, Render and Neon for the public demo

Status: accepted for preparation on 23 October 2026; not deployed.

Phase 23B amendment: the active Blueprint now uses **one Render Free web service**,
not the earlier paid Starter + cron topology described below. Expiry cleanup runs
at startup and hourly while that API process is awake; access expiry is enforced
independently, and physical deletion can be delayed while stopped. Production
startup verifies the schema read-only, with `/health` used for platform probes.
Idle interview polling is 600 seconds in this profile with request wakeups; shared
file-worker capacity is one. No scheduled deletion or background uptime guarantee.

The initial Blueprint remains a zero-key mock-only demo. The same application can
instead enable Clerk-authenticated accounts and xKiro using the documented account
profile; demo sessions still always use mock. No second backend is required.
Current configuration and free-tier limits are in [DEPLOYMENT.md](../DEPLOYMENT.md).
The following text preserves the original paid-hosting decision for context.

The original [V2 deployment proposal](../V2_ARCHITECTURE.md#18-deployment-architecture) selected
a single VM. It did not choose Render or Railway. The current request replaces
that hosting target with Vercel for Next.js and Neon for PostgreSQL. This ADR
selects **Render** for FastAPI; it supersedes only the earlier hosting choice.

Render supports the existing Docker runtime, a schema/database readiness check
and a separate scheduled cleanup job through a reviewable Blueprint. Railway is
a viable alternative, but maintaining a second platform configuration adds no
value to this deployment. Neither choice makes inference necessary. The prepared
public profile enforces `AI_PROVIDER=mock`, `PUBLIC_DEMO_ONLY=true` and disabled
account access. Hosting charges and AI API charges are distinct.

The browser keeps same-origin API URLs. Vercel forwards requests and host-only
secure demo cookies to Render. A server-only shared gateway credential binds the
quota address to Vercel's overwritten client-IP metadata; arbitrary forwarding
headers and direct backend mutations are rejected. This supplements existing
ownership and CSRF checks. No public wildcard CORS or preview-origin allowance.

Use a direct Neon endpoint with verified certificate/hostname TLS and a small
application pool (three connections plus two overflow per API process). This
avoids introducing PgBouncer prepared-statement compatibility concerns. Keep one
API process initially; its existing durable interview runner stays in that
process. Scale only after connection/job/abuse testing.

Migrations and reviewed catalogue publication run explicitly as the database
owner before the release. The API and hourly cleanup use a restricted login
role. Do not give the web service the owner's URL, including through a separate
environment variable: a pre-deploy command shares the web service's environment.
No automatic startup migrations, destructive reseeding or automatic schema
downgrades. No schema change is required for this hosting preparation.

The Blueprint uses paid Starter compute and hourly cleanup. Render's Free web
service sleeps on idle and is unsuitable for continuous workers and scheduled
expiry guarantees; account creation being free does not make this topology free.
Vercel/Neon free-tier availability and limits must be checked before approval.
Provider selection is not a promise of uptime or a completed security review.

See [the deployment runbook](../DEPLOYMENT.md) for exact setup, credential
boundaries, backups/rollback, auth configuration, local checks and references.
