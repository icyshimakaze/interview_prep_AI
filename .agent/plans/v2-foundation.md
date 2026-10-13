# V2 foundation

Date: 2026-10-09. Scope: architecture phase 1, locally implemented and verified.

## Objective and acceptance

Create a reproducible Next.js/FastAPI/PostgreSQL foundation. Install dependencies,
start the services, verify frontend/API/database connectivity, and pass relevant
lint, formatting, strict typing, tests, migrations, and production builds.

## Scope and affected components

- Use `frontend/` and `backend/` instead of the architecture's proposed
  `apps/web/` and `apps/api/`, following the explicit implementation request.
- pnpm workspace, uv-managed Python package, exact direct versions and lockfiles.
- App Router, Tailwind, accessible UI primitives, health connectivity screen,
  generated OpenAPI types, and focused component/browser checks.
- FastAPI factory, typed settings, async SQLAlchemy 2, Alembic, liveness/readiness,
  consistent safe errors, and minimal isolated expiring demo sessions.
- Compose, local-only ports, one-shot migration service, non-root images, CI,
  scripts, sanitized configuration examples, secure ignore rules and setup docs.
- Preserve original V1 files unchanged. Export 15 question titles and 24 roadmap
  suggestions as unpublished editorial seeds with provenance; preserve baseline
  source through Git history. Do not import the classifier or unsupported metrics.
- No assessments, account auth, uploads, AI, jobs, roadmap engine, or deployment.

## Database and API

One initial versioned migration for demo principals/sessions, with expiry,
hashed opaque credentials, ownership FK/cascade and integrity constraints.
Fresh DB upgrade/downgrade/upgrade and Alembic metadata drift checks use real
PostgreSQL. No legacy durable user database exists. No destructive rollout is
needed; never remove the persistent Compose volume as part of ordinary shutdown.

`GET /health` is process liveness. `GET /api/v1/health/ready` checks DB and schema,
returning 503 with sanitized details on failure. Demo creation/resolution exposes
only the current cookie-owned workspace, never client-selected owners. Exact
Origin checks protect creation; credentials are HttpOnly and production-secure.
No personal content is accepted. Expiry and cleanup are explicit.

## Frontend and security

Small status page with loading, connected, and failure states, keyboard-operable
retry, semantic headings, visible focus and live status announcements. Same-origin
API forwarding uses a server-only backend URL; no browser secrets or wildcard
credentialed CORS. Bound and validate tokens/configuration. Never log credentials
or expose raw DB errors. Account/AI capabilities remain unavailable.

## Implementation order

1. Verify runtimes/official package versions, write scaffolding and configuration.
2. Install frontend and backend dependencies; retain resolved lockfiles.
3. Implement DB/migrations, API contracts and failure/isolation tests.
4. Implement UI/client contracts and meaningful connectivity/error checks.
5. Start PostgreSQL, migrate, start backend/frontend, exercise live endpoints.
6. Run all quality gates and Compose builds/startup; fix issues; review diff.
7. Update status, plan outcome and setup/verification documentation.

## Verification

`pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`, `pnpm build`,
`pnpm test:e2e`; `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy src tests`, `uv run pytest`; Alembic upgrade, round-trip and drift;
OpenAPI drift; live smoke checks; Compose configuration/build/healthy startup.
Preserved legacy hashes and reconciled seed counts are checked. Record exact
results, any environmental limits and remaining work in PROJECT_STATUS.md.

## Outcome

Completed locally. Dependencies installed; native and final Compose services
started; liveness, real PostgreSQL/schema readiness, same-origin connectivity,
and demo isolation/persistence verified. Frontend lint/types/format/build,
4 component tests, and 3 browser/accessibility checks passed. Backend Ruff,
strict mypy (28 files), 27 pytest tests, migration round-trip/drift, and
OpenAPI/legacy checks passed. All final container builds and healthy startup passed.

Fixed the stopped Docker daemon, interrupted downloads, SQLAlchemy asyncio extra,
pnpm build-policy changes, supported ESLint peer version, ESM config/formatting,
standalone startup, and unexpected-error response headers. Verified unchanged
legacy hashes/counts and absence of local generated credentials in checked
source/static bundles. Public release and major product features remain excluded;
CI is configured but was not run on GitHub. Exact evidence and limitations are
recorded in PROJECT_STATUS.md.
