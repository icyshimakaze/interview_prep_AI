# Contributing

Interview Prep V2 is a portfolio application built with Next.js, FastAPI and
PostgreSQL. Contributions should preserve truthful product claims, private user
ownership and reproducible behavior. Read [PROJECT_STATUS.md](PROJECT_STATUS.md)
and the [engineering rules](AGENTS.md) before substantial work.

## Set up

Use Node 24 LTS (24.15+), pnpm 12.8.1, Python 3.12, uv 0.12.24 and Docker Compose.
From the repository root:

```sh
python scripts/init_env.py
pnpm install --frozen-lockfile
uv sync --project backend --frozen
docker compose up -d postgres
```

The generated `.env` is ignored. Keep local credentials out of commits, screenshots
and issue reports. Application setup and optional Clerk configuration are in
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). No AI account is needed for development
or testing. Do not install the archived V1 `requirements.txt` for V2.

## Verify changes

Install a browser once, then run the complete pipeline:

```sh
pnpm --filter @interview-prep/frontend exec playwright install chromium
pnpm check
```

On Linux CI, browser installation additionally uses `--with-deps`. The full check
runs backend lint/types/tests/migrations, frontend lint/types/tests/contracts,
repository formatting, a production build and live Playwright journeys. PostgreSQL
must be available and ports 8000/3000 free. If normal development services use them:

```sh
pnpm check --api-port 8100 --frontend-port 3100
```

The scripts create and remove randomly named disposable test databases. They
refuse existing databases and occupied server ports; they never migrate or truncate
the application database. They stop only server processes they started. On Windows,
installed Chrome or Edge can be selected with `E2E_BROWSER_CHANNEL=chrome` or
`msedge`. Test commands and coverage boundaries are in [docs/TESTING.md](docs/TESTING.md).

## Make a focused change

- Use strict TypeScript and annotated Python. Keep domain logic separate from
  components, database access and provider integrations.
- Add behavioral tests for important rules, ownership, concurrency and failure
  recovery. Cover invalid input and saved work as well as successful responses.
- Use fictional fixtures and MockAIProvider. Pytest and component tests block real
  HTTP by default; protocol tests use explicit in-memory transports with dummy
  credentials. Do not remove those protections or weaken checks to obtain a pass.
- Review schema changes as versioned Alembic migrations. Preserve existing data,
  check metadata drift, and test safe rollback/refusal against disposable databases.
- After an intentional API change, run `scripts/export_openapi.py` with the backend
  environment and `pnpm api:types`; commit both generated contracts.
- Update relevant documentation, the Unreleased changelog and project status when
  behavior or operational requirements change. Record the exact checks you ran.

Open a pull request with the problem, resulting behavior, evidence and limitations.
The template is a guide, not a request for invented benchmarks or claims. CI does
not publish or deploy. Dependency update PRs require the same review and checks;
there is no automatic merge policy. Report vulnerabilities through
[SECURITY.md](SECURITY.md), without posting credentials or candidate data publicly.
