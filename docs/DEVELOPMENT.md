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

AI defaults to `AI_PROVIDER=mock`. Keep `OPENAI_API_KEY`, `OPENAI_MODEL`,
`OLLAMA_BASE_URL` and `OLLAMA_MODEL` empty for credential-free local development.
No model download or AI service is required for tests, CI or the recruiter demo.
Optional account providers are configured only on the backend; see
[AI architecture](AI_ARCHITECTURE.md) for configuration, disclosures and failure
behavior. The demo remains mock even when an account provider is configured.

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
uses the backend image and removes expired demo rows, quotas and evaluation
receipts hourly. Interview work runs separately in the API's database-backed
loops described below. API/frontend containers run as non-root.

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

The current application requires migrations through `0010_security_budgets`,
including `0007_mock_interviews` for the interview workflow. The API starts
two bounded database-backed worker loops by default (`INTERVIEW_WORKER_ENABLED=true`).
They evaluate already-saved main answers, prepare optional follow-ups and recover
expired/interrupted work. Default/demo use stays local with `AI_PROVIDER=mock`.
See [interview operations and recovery](MOCK_INTERVIEWS.md).

## Quality gates

Run the actual complete pipeline with PostgreSQL available:

```sh
pnpm --filter @interview-prep/frontend exec playwright install chromium
pnpm check
```

This runs backend Ruff/mypy/pytest/migration/contract checks, frontend
lint/format/types/component tests, generated-contract consistency, the production
build and the live browser suite. MockAIProvider is forced and inherited provider
credentials are cleared. Tests use fresh disposable databases; the application
database is not migrated or truncated. The browser runner owns and stops both
local servers, with no manual fixture preparation or prior Vitest run required.
It refuses occupied ports instead of stopping an existing service.

To keep normal services running, use:

```sh
pnpm check --api-port 8100 --frontend-port 3100
```

Focused gates are `pnpm check:backend`, `pnpm lint`, `pnpm typecheck`, `pnpm test`,
`pnpm format:check`, `pnpm build` and `pnpm check:e2e`. The backend runner accepts
`--phase lint`, `--phase tests` and `--phase migrations`; the default runs all.
`pnpm check:e2e --skip-build` uses a matching existing production build and checks
its compiled API destination before creating the database. `pnpm test:e2e` is the
raw Playwright command for an already prepared isolated stack.

Windows may use installed Chrome or Edge instead of bundled Chromium. Set
`$env:E2E_BROWSER_CHANNEL = 'chrome'` or `msedge`; CI installs bundled Chromium
with `--with-deps`. See [TESTING.md](TESTING.md) for the full coverage map, the
live/intercepted/static browser boundaries, report paths and exact CI gates.
Automated accessibility checks do not establish complete WCAG conformance.

`pnpm start` runs the generated standalone server with static/public assets and
binds to localhost. Set `FRONTEND_HOSTNAME` explicitly to change the listener.
The container runs that same generated server directly. With a normal stack
running, `scripts/smoke_stack.py` verifies liveness, schema readiness and frontend
API forwarding. `docker compose build` verifies image packaging without deployment.

## Contracts and migration discipline

Resume parsing requires the locked pypdf dependency and schema
`0004_resume_evidence`. Run migrations before the updated API; workers enforce
Linux or Windows resource limits and fail closed if those cannot be applied.
See [resume privacy, upload contracts and rollout](RESUME_PRIVACY.md).

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
has a dashboard, saved practice, roadmap and local Project Defense imports.
It accepts fictional user-entered answers and repository data, always uses mock
AI, and does not accept resume PDFs. Exit deletes that visitor's records.
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

Question browsing and assessments require migration `0006_real_assessments` and the explicit catalogue
seed. See [validation/publication and recovery commands](QUESTION_BANK.md).
Readiness requires `0010_security_budgets`. The browser harness seeds only its freshly created
disposable database; existing application services are not automatically replaced.

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
