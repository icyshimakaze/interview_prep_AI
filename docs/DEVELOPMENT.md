# Development and verification

## Prerequisites and configuration

Use Node 24 LTS (24.15+; Node 26 is also supported for local development), pnpm
12.8.1, Python 3.12, uv 0.12.24, and running Docker Desktop/Engine with Compose.
The container runtime uses Node 24 LTS and Python 3.12. V2 does not use the legacy
root `requirements.txt` or any globally installed Python packages.

Run `python scripts/init_env.py` once. It creates an ignored root `.env` with
random local database credentials and a demo rate-limit key, preserving an existing
file. Commit only `.env.example`. Never print `.env` or use `docker compose config`
without `--quiet` in shared logs, since rendered configuration contains secrets.

The native backend reads root `.env`. Next.js reads `frontend/.env.local` if you
need to change its server-only `BACKEND_INTERNAL_URL`; the default is
`http://127.0.0.1:8000`. Copy `frontend/.env.example` for that override. No secret
belongs in `NEXT_PUBLIC_*`. API/DB port overrides must also match URLs and allowed
origins. PostgreSQL defaults to localhost port **5433**, preserving an existing
local server on 5432. Use URL-safe random database passwords, or URL-encode them
when constructing connection URLs.

## Full Compose stack

```sh
python scripts/init_env.py
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/health/ready
```

Compose starts PostgreSQL, applies Alembic migrations in a one-shot service, starts
FastAPI, and gates Next.js on database/schema readiness. A small cleanup process
uses the backend image and deletes expired demo rows hourly. This is maintenance,
not the future background job worker. API/frontend containers run as non-root.

The frontend's backend destination is resolved at build time. Rebuild its image
when changing that destination. Services are local development configurations;
public HTTPS ingress, verified proxy trust, separate migration/runtime DB roles,
Clerk instance setup, backup/restore, and production CSP are future release work.
The demo creation quota uses the direct peer address; behind an unconfigured
gateway that means a shared gateway quota. Public ingress must establish trusted
client IP handling before a recruiter demo release.

Stop with `docker compose down`. This retains the named database volume. Do not
add `--volumes` during normal shutdown; that would delete stored data.

## Native hot reload with containerized PostgreSQL

```sh
pnpm install --frozen-lockfile
uv sync --project backend --frozen
docker compose up -d postgres
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

Run these in separate terminals from the root:

```sh
uv run --project backend uvicorn interview_prep.main:create_app --factory --reload --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

```sh
pnpm dev
```

If the full Compose API/frontend already use these ports, stop those services
first: `docker compose stop frontend backend cleanup`. Both workflows use the
same persisted application database. After a schema change, apply its migration
before restarting services; the API does not auto-create tables.

## Quality gates

Run from the root with PostgreSQL available:

```sh
uv run --project backend python scripts/check_backend.py
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
```

`pnpm start` runs the generated standalone server with its static/public assets
and binds to localhost. Set `FRONTEND_HOSTNAME` explicitly to change the native
production listener. The container runs that same generated server directly.

The backend script creates a new random `interview_prep_<hex>_test` database, migrates it, and runs Ruff,
formatting, strict mypy, pytest, Alembic metadata drift, migration round-trip,
OpenAPI drift, and legacy preservation checks. It clears domain tables only
in that disposable test database and removes the database afterward. Never point `TEST_DATABASE_URL` at personal or
production data. Names must end `_test` and differ from the configured application
database. Direct pytest intentionally fails rather than skipping DB tests when no
migrated `TEST_DATABASE_URL` is supplied.

Equivalent direct backend commands (working directory `backend/`):

```sh
uv run ruff check . ../scripts
uv run ruff format --check . ../scripts
uv run mypy src tests ../scripts
uv run pytest
uv run alembic check
```

With the API/frontend running, verify real connectivity and browser behavior:

```sh
uv run --project backend python scripts/smoke_stack.py
pnpm --filter @interview-prep/frontend exec playwright install chromium
pnpm test:e2e
```

An already installed Chrome or Edge can be used instead of downloading Chromium:
set `E2E_BROWSER_CHANNEL=chrome` or `msedge` before `pnpm test:e2e`. For PowerShell,
use `$env:E2E_BROWSER_CHANNEL = 'chrome'`. CI uses the default bundled Chromium.

Browser checks cover live frontend-to-API-to-PostgreSQL connectivity, keyboard
navigation/mobile overflow, WCAG A/AA automated checks, and a labeled intercepted
503 failure case. Automated accessibility checks do not establish complete WCAG
conformance. CI installs Chromium with Linux OS dependencies, runs the same gates,
and builds containers; it does not publish or deploy.

For repeatable local browser checks, leave the built native frontend running and
stop the existing API first (`docker compose stop backend cleanup` for Compose).
Then run:

```sh
uv run --project backend python scripts/check_browser.py
```

This creates a fresh disposable PostgreSQL database, migrates it, starts a temporary
API on port 8000, runs the browser suite, then stops only its API process and removes
that database. It refuses an occupied API port. Native frontends must use the default
local backend URL; Clerk keys must be absent for the account setup-state test.
Restart the normal API afterward. No production quota or application data is reset.

To leave existing services running, build with
`BACKEND_INTERNAL_URL=http://127.0.0.1:8100`, start that native frontend with
`PORT=3100`, then run the harness with `--api-port 8100 --frontend-port 3100`.
The harness sets the test API's allowed origin to that frontend, refuses an occupied
API port, and removes only the disposable database/process it created. Stop the
temporary frontend and rebuild without the override afterward to restore the default
API destination. These are process environment variables, not changes to `.env`.
On Windows, use `$env:NAME='value'` to set a process environment variable, and
`$env:E2E_BROWSER_CHANNEL='chrome'` when testing with installed Chrome.

## Contracts and migration discipline

```sh
uv run --project backend python scripts/export_openapi.py
pnpm api:types
uv run --project backend python scripts/export_openapi.py --check
```

Commit both `backend/openapi.json` and the generated TypeScript definitions.
Runtime transport still validates the readiness response instead of trusting a
type assertion. Next.js forwards `/api/v1/*` to FastAPI; authorization/domain rules
remain in the backend. API errors have `code`, `message`, and `request_id` and omit
request bodies/driver exceptions. `/health` does not touch the database;
`/api/v1/health/ready` returns 503 when PostgreSQL is unavailable or migration
revision differs from the required application revision.

Add future schema revisions with `uv run --project backend alembic -c
backend/alembic.ini revision --autogenerate -m "description"` and review the
generated changes. Do not downgrade a populated application database merely to
roll back code. Use compatible changes and backups; migration round-trip checks
run only on disposable test databases.

## Minimal demo identity contract

`POST /api/v1/demo/sessions` accepts only `{}` and an exact allowed `Origin`, sets
an opaque HttpOnly cookie, and returns the current expiring workspace. Subsequent
creation requests reuse that workspace only with its `X-CSRF-Token` from the
non-HttpOnly CSRF cookie. `GET /api/v1/demo/workspace` resolves only the cookie's
workspace and has no owner-ID parameter. Any bearer credentials never become
demo access. Tokens are stored as SHA-256 hashes; creation is limited to two new
workspaces per network identifier/hour. Demo access expires within 24 hours;
cleanup deletes principals, all their private records and credentials with FK
cascade, plus expired hashed rate identifiers. The fictional recruiter workspace
has a dashboard, history and idempotent task completion; it accepts no candidate
uploads, arbitrary content or AI requests. Exit deletes that visitor's records.
Expired credentials can be cleared with a same-origin reset; resetting a live
workspace still requires CSRF and does not bypass creation quotas.

See [the relational model and seeds](DATA_MODEL.md) and
[Clerk setup, account routes and demo isolation](AUTHENTICATION.md). Load the
preserved 15 title drafts after migrations with:

```sh
uv run --project backend python -m interview_prep.seeding
```

The separate recruiter demo seeds only its own fictional private content during
bootstrap. Account workspaces begin empty. Live Clerk account verification needs
real development keys; the browser suite's account setup test assumes keys are absent.

Cookies are secure in production settings; local HTTP uses the explicit
development setting. Production settings reject HTTP origins and placeholder
rate-limit keys. These safeguards do not authorize a public deployment.

## Troubleshooting

- A stopped Docker daemon: start Docker Desktop and rerun `docker version`.
- A 503 readiness response: verify PostgreSQL is healthy, credentials/ports match,
  and `alembic upgrade head` succeeded. No raw connection string is returned.
- A frontend connection failure: inspect the API readiness endpoint, then its
  server-only backend URL. Browser requests use the frontend origin.
- Port conflicts: use the documented override variables and matching URLs instead
  of stopping unrelated services.
- A demo 429: the two-creation hourly quota is working. Reuse a session with its
  CSRF credential rather than creating another workspace.
- Native dependencies blocked by sandbox/network policy: installation may need
  the environment's normal reviewed network permissions; preserve lockfiles and
  rerun frozen installation after access is restored.
