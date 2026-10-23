# Deployment: Vercel + Render Free + Neon

Deployed with explicit user authorization on 24 October 2026 (Asia/Calcutta).
The public mock-only demo is live at
**[interview-prep-ai-icyshimakaze.vercel.app](https://interview-prep-ai-icyshimakaze.vercel.app)**.
Choose **Try Interactive Demo**; no login or AI key is needed. Account sign-in
and live xKiro are disabled in this initial profile.

| Resource        | Existing deployment                                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend        | Vercel Hobby, personal `icyshimakaze` account; project `interview-prep-ai-icyshimakaze`                                                                                 |
| Backend         | [Render service](https://dashboard.render.com/web/srv-dbdrrr9srm7s73cpdt6g), Free Docker, Singapore, My Workspace                                                       |
| Database        | [Existing Free Neon project](https://console.neon.tech/app/projects/autumn-sound-91017993/branches/br-twilight-resonance-b3ukxsc8?database=neondb), Singapore, `neondb` |
| Deployed source | `rebuild/professional-v2` at `c5ca23ea5a8b1d502f6e53d22b32b3bdde73debb`                                                                                                 |
| Release CI      | [Complete successful run](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40012341296)                                                                   |

Neon migrations through `0012_ai_context_reviews`, 29 published questions,
restricted runtime grants, verified TLS and frontend/backend readiness passed.
Render reports `live`; Vercel reports `READY`. HTTPS, security headers, backend
gateway enforcement, canonical/foreign CORS and closed account mode passed.
Hosted Chrome checks exercised candidate edits, questions, assessments, mock
interviews, Project Defense and roadmap. The full hosted suite did **not** pass:
the first run stopped on a 15-second navigation timeout; a bounded follow-up
passed interviews/projects/roadmap but reused a progress assertion that required
objective assessment attempts absent from its fresh session. The page correctly
showed empty objective history and persisted simulated practice. Hosted
two-visitor isolation and the UI exit sequence were not completed. Both test
sessions were deleted through their own authenticated cleanup requests; final
aggregate database checks are recorded in `PROJECT_STATUS.md`.

Render automatic deploys are off. Vercel was deployed from the pinned Git source
without connecting automatic Git deploys. Future pushes require a separate
explicit release. The Render creation connector cannot set `healthCheckPath`;
the current service uses TCP health checks, and both HTTP health endpoints were
verified manually. The Blueprint below specifies `/health` for future imports.
Existing unrelated hosting resources were preserved. No paid services were added.

**No provisioning steps remain for using this demo.** Sections A–S are the
reproducible setup/redeployment reference. Do not import the Blueprint again for
the existing service. Account mode still requires the release work in section H.
Render Free sleeps when idle; the first visit may need time to wake. Demo
creation is limited to two sessions per network per UTC hour; deployment checks
used that allowance on the operator's network. Do not reset quotas to retry tests.

This runbook supersedes the earlier paid Starter/cron proposal in
[ADR 0001](adr/0001-managed-deployment.md). It prepares a small portfolio demo,
not an availability SLA or an unrestricted production service for personal data.

The same application supports two profiles:

| Profile                                           | Backend                                                            | Vercel                                                   | Visitor experience                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------- |
| Mock-only recruiter demo (safe initial Blueprint) | `PUBLIC_DEMO_ONLY=true`, `AUTH_ENABLED=false`, `AI_PROVIDER=mock`  | `PUBLIC_DEMO_ONLY=true`, no Clerk keys                   | Public **Try Interactive Demo**, no account or AI key                  |
| Accounts + xKiro, with recruiter demo alongside   | `PUBLIC_DEMO_ONLY=false`, `AUTH_ENABLED=true`, `AI_PROVIDER=xkiro` | `PUBLIC_DEMO_ONLY=false`, matching Clerk production keys | Accounts use xKiro after disclosure; `/demo` still uses MockAIProvider |

Choose the account profile only after configuring Clerk and resolving the
account-release limitations below. It needs no second backend, database, AI
subscription, or visitor-supplied AI key. There is no silent AI-to-mock fallback.

Browser -> Vercel same-origin `/api/v1/*` -> Render FastAPI -> Neon.
Clerk verifies accounts; only Render sends opted-in content to xKiro/downstream.

## A. Prerequisites and free-tier limits

- Existing GitHub repository, reviewed release commit, Node **24.x**, pinned
  **pnpm 12.8.1**, Docker and a PostgreSQL client. Native backend uses Python 3.12
  and `uv`; the recommended hosted backend uses its Dockerfile.
- Vercel, Render and Neon accounts with access to the repository. Authorizing
  integrations/importing projects can trigger deployments; do so only for an
  authorized release. Keep previews separate from production data/secrets.
- Optional account mode needs a Clerk production instance, matching keys and a
  domain you own/control for DNS. Domain registration is not included in a free
  hosting tier; use the mock-only `vercel.app` demo if that is unavailable.
- Read [Render Free limits](https://render.com/docs/free): idle sleep after 15
  minutes, roughly a minute to wake, 750 instance-hours/workspace/month, ephemeral
  disk, possible restarts/suspension, and no shell/one-off jobs. Bandwidth/build
  overages can bill when payment is enabled. Free is for hobby previews, not SLA
  production. [Free compute](https://render.com/docs/compute-plans) is 0.1 CPU /
  512 MB; uploads/static analysis can be slow or hit resource limits.
- [Render cron](https://render.com/docs/cronjobs) has a minimum monthly charge;
  **this Blueprint creates no cron, worker, disk or Render database**.
- [Neon Free](https://neon.com/docs/introduction/plans) currently includes 100
  CU-hours/project/month, 1 GB storage/project, 5 GB transfer/project and scale to
  zero after five idle minutes. Its restore history is limited; take/export
  recoverable backups before changes. Check actual allowances in your account.
- [Vercel Hobby](https://vercel.com/docs/plans/hobby) is for personal,
  non-commercial use, with usage caps and feature pauses on exhaustion. Confirm
  this portfolio's eligibility. No uptime or commercial-use entitlement is implied.
- [Clerk Hobby](https://clerk.com/pricing) currently includes 50,000 monthly
  retained users/app with feature limits. Check dashboard limits and avoid paid
  add-ons. xKiro free-model availability/allowances are independent and unguaranteed.

Do not use uptime pingers to defeat sleep. DB polling, health checks and real AI
traffic all consume limited resources. Monitor every provider's usage dashboard.

## B. Create the Neon database — after authorization

Create one **Free** Neon project near Render Singapore (or choose matching regions
in both), database `neondb`, PostgreSQL 18 if available. Keep preview/development
in separate projects/branches within free limits. Do not choose a paid plan or
extra paid resources to bypass limits. Do not create a Render database or SQLite.

In Neon Connect select the **direct/unpooled** endpoint (no `-pooler` hostname).
Use a database owner only for explicit migrations/publication; create a restricted
runtime role for Render. The backend uses a bounded SQLAlchemy pool: three
connections plus at most two overflow per process, pre-ping and verified TLS.

Neon pooled endpoints use transaction pooling and have different prepared-statement
semantics. This runbook deliberately uses direct connections; do not substitute a
pooled URL without testing asyncpg/SQLAlchemy compatibility. See
[Neon pooling](https://neon.com/docs/connect/connection-pooling).

## C. Connect PostgreSQL and create the runtime role

Keep the owner's password in a password manager. With PostgreSQL/libpq 18:

```sh
PGSSLMODE=verify-full PGSSLROOTCERT=system psql --host=YOUR-DIRECT-NEON-HOST --username=YOUR-OWNER --dbname=neondb --password
```

PowerShell: set `$env:PGSSLMODE='verify-full'` and
`$env:PGSSLROOTCERT='system'`, then run the same `psql` flags. Use a password
prompt, not a password in command history. If your client needs a CA file, supply
its trusted bundle. The application image's system CA bundle is used by default.

In psql, as the owner:

```sql
CREATE ROLE interview_prep_runtime LOGIN;
\password interview_prep_runtime
```

Enter a generated password privately. No owner/superuser/role-creation membership
for this role. Render must never receive the owner URL, including as an unused
migration variable. Construct separate application URLs for owner and runtime:

```text
postgresql+asyncpg://ROLE:URL_ENCODED_PASSWORD@YOUR-DIRECT-NEON-HOST/neondb
```

Percent-encode reserved password characters. Remove Neon's libpq query options
(`sslmode`, `channel_binding`) from **application** URLs; configure
`DATABASE_SSL_MODE=verify-full` instead. Do not downgrade to `require` or disable
hostname verification. [Neon TLS](https://neon.com/docs/connect/connect-securely).

## D. Create the Render service — after authorization

Import the reviewed branch with **New -> Blueprint**, root `render.yaml`, or
create an equivalent **Web Service / Docker / Free** manually. Importing creates
resources; reviewing the file locally does not. Verify **one free web service**,
no paid cron/worker/disk/database, and automatic deploys **off** before applying.

The default Blueprint is the zero-key mock profile. Its environment group generates
separate gateway/quota keys; service-level prompts ask for database URL/origins.
Use the runtime URL. Render ignores `sync: false` inside environment groups, so
these two prompted settings must remain on the service.
For the combined account profile, change the same service/group using section F
and configure the matching frontend in K. No second paid service is required.

## E. Exact Render root, build, start and health settings

| Setting              | Repository value                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| Service type / plan  | Web Service / **Free** / one instance                                                                    |
| Region               | Singapore by default; match Neon                                                                         |
| Runtime              | Docker                                                                                                   |
| Root Directory       | Repository root; leave blank, **not** `backend/`                                                         |
| Dockerfile           | `./deploy/backend.Dockerfile`                                                                            |
| Docker build context | `.`                                                                                                      |
| Build                | Dockerfile installs uv 0.12.24, then `uv sync --frozen --no-dev --no-editable` against `backend/uv.lock` |
| Python               | 3.12, pinned base image digest                                                                           |
| Application factory  | `interview_prep.main:create_app`                                                                         |
| Start                | Docker CMD `python -m interview_prep.serve` (no dashboard override needed)                               |
| Listener             | `0.0.0.0:$PORT`, platform-assigned; native fallback 8000                                                 |
| Render health check  | **`/health`** (no DB query)                                                                              |
| Database readiness   | **`/api/v1/health/ready`**, manual release smoke                                                         |
| Migration            | Operator-run `alembic upgrade head`, section M; never automatic startup                                  |

Production startup performs a read-only database/schema check with a 15-second
bound and refuses to serve an absent/outdated schema. It never creates tables,
migrates or seeds. Then `/health` checks the running process. Using liveness for
frequent Render probes avoids repeatedly waking Neon. A later database outage
returns safe API/readiness errors; liveness is not a database availability claim.
No debug docs/OpenAPI route, reload mode or raw Uvicorn access logs in production.

## F. Every Render environment variable

Examples: [mock profile](../deploy/backend.env.example),
[account + xKiro profile](../deploy/backend.account.env.example). These contain
placeholders only; never copy them over existing real dotenv files.

| Name read by backend               | Required/value                                                                       |
| ---------------------------------- | ------------------------------------------------------------------------------------ |
| `APP_ENV`                          | **`production`**                                                                     |
| `PUBLIC_DEMO_ONLY`                 | `true` for mock-only; `false` for accounts + demo                                    |
| `AUTH_ENABLED`                     | `false` for mock-only; **`true`** for accounts                                       |
| `DATABASE_URL`                     | Secret restricted-role `postgresql+asyncpg://...` direct Neon URL                    |
| `DATABASE_SSL_MODE`                | **`verify-full`**                                                                    |
| `DATABASE_SSL_CA_FILE`             | Optional trusted CA path; normally omit for Neon/system trust                        |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | `10` (bounded 1-30)                                                                  |
| `ALLOWED_ORIGINS`                  | JSON array of exact canonical HTTPS frontend origins; normally one                   |
| `DEMO_RATE_LIMIT_KEY`              | Secret generated random value, >=32 characters; keep stable                          |
| `BACKEND_PROXY_SECRET`             | Secret generated 32-256 characters; must match Vercel                                |
| `DEMO_TTL_SECONDS`                 | `86400`; access expires within 24 hours                                              |
| `INTERVIEW_WORKER_ENABLED`         | `true`; durable interview work is processed in the API                               |
| `INTERVIEW_POLL_SECONDS`           | `600` for idle free-tier reconciliation; owned reads/mutations wake workers promptly |
| `CLEANUP_ENABLED`                  | **`true`** for Render's in-process startup/hourly-while-awake cleanup                |
| `FILE_WORKER_SLOTS`                | **`1`** for shared PDF/project processing capacity on 512 MB                         |
| `PORT`                             | Render supplies it; do not override with a development-only port                     |
| `AI_PROVIDER`                      | `mock` initial profile; `xkiro` for account profile                                  |
| `XKIRO_API_KEY`                    | Secret, required only when production provider is xKiro                              |
| `XKIRO_BASE_URL`                   | `https://api.xkiro.com/v1`                                                           |
| `XKIRO_MODEL_SMART`                | `qwen/qwen3.8-max:free`                                                              |
| `XKIRO_MODEL_MULTIMODAL`           | `qwen/qwen3.8-omni-flash:free`                                                       |
| `XKIRO_MODEL_ROUTES`               | `{}` unless explicitly reviewed free-model routes are needed                         |
| `XKIRO_ALLOW_PAID_MODELS`          | **`false`**                                                                          |
| `AI_TIMEOUT_SECONDS`               | `60` for account profile; hard limit remains 60                                      |
| `AI_MAX_RETRIES`                   | **`0`** for conservative account profile; no ambiguous timeout replay                |
| `AI_OWNER_HOURLY_CALLS`            | `10` for account profile                                                             |
| `AI_OWNER_DAILY_CALLS`             | `30` for account profile                                                             |
| `AI_GLOBAL_DAILY_CALLS`            | `100` for account profile                                                            |
| `AUTH_ISSUER`                      | Account-only trusted Clerk production HTTPS issuer origin, no slash/path             |
| `AUTH_AUDIENCE`                    | `interview-prep-api`                                                                 |
| `AUTH_JWKS_CACHE_SECONDS`          | Optional `300`; bounded 30-900                                                       |
| `OPENAI_API_KEY`, `OPENAI_MODEL`   | Leave unset/empty in these profiles                                                  |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`  | Leave unset/empty in these profiles                                                  |

There is no custom `LOG_LEVEL` setting. The production entrypoint emits sanitized
INFO request metadata (method, matched route template, status, duration, random
request ID); failures use fixed safe messages. No bodies, headers, raw paths,
query strings, IPs or owner IDs. Configure platform log retention independently.

Missing selected production keys/auth settings, placeholder security values,
insecure TLS/origins or an outdated schema fail clearly without printing secrets.
The backend reads absolute root `.env`, then `backend/.env` during native
work; process environment wins. Both files are excluded from production images.

## G. Enter the xKiro key securely

In Render service/environment-group settings add **`XKIRO_API_KEY`** directly in
the private value field. Do not paste it into chat, tickets, screenshots, a build
command/argument or GitHub Actions. Use only a backend environment secret.
Never put it in Vercel or any `NEXT_PUBLIC_` variable. Do not change the existing
local key. Adding/changing a Render value requires a reviewed restart/redeploy.

Keep both `:free` IDs and `XKIRO_ALLOW_PAID_MODELS=false`. No paid model is
substituted when a quota, timeout or provider error occurs. Free-model suffix
checks do not replace provider-side spending/retention controls.

## H. Configure Clerk production authentication manually

Follow [the existing auth implementation](AUTHENTICATION.md) and the
[Clerk production checklist](https://clerk.com/docs/guides/development/deployment/production).
Do not replace Clerk with Neon Auth or a new login system.

1. Create/select the production instance. Configure its owned domain, DNS and
   certificates using **your dashboard's exact records**. Restrict allowed
   subdomains to the canonical app. No DNS changes were made in this phase.
2. Use matching `pk_live_` and `sk_live_` keys on Vercel; only the publishable key
   is public. The production build refuses missing/development account keys.
3. Configure web paths `/sign-in` and `/sign-up` on the canonical HTTPS origin.
   Both page components force the same-origin `/app/dashboard` after success.
   Sign-out redirects to `/`. Allowlist these exact URLs; no external return URL.
4. Create the **`interview-prep-api`** JWT template in the production instance:
   RS256 instance signing key, audience claim `{ "aud": "interview-prep-api" }`,
   60-second lifetime, 5-second skew. Leave issuer/subject/timestamps/`azp` to Clerk.
   Template name matches `getToken({ template: "interview-prep-api" })` in the app.
5. Set Render `AUTH_ISSUER` to that instance's exact HTTPS issuer origin.
   FastAPI fetches only `ISSUER/.well-known/jwks.json`, validates signatures,
   issuer/audience/times and `azp` against exact allowed frontend origins, then
   resolves the local owner. It never trusts token-supplied key URLs or owner IDs.
6. If social login is enabled, configure your production OAuth application's
   exact Clerk-supplied callback in that provider console. No invented Render
   callback. Keep unneeded social/add-on features off to avoid charges.
7. Start with controlled fictional/test accounts. Verify sign-in/refresh/sign-out,
   expired tokens, wrong audience/origin, protected `/app/*`, and two-account
   isolation. `/demo` stays usable without login or an AI key.

Account self-service export/erasure and Clerk deletion reconciliation remain
unimplemented; profile deletion does not erase all history. The current CSP
blocks objects/base/frame embedding but is not a strict nonce-based script CSP.
Resolve these account/privacy/security release limitations before opening broad
registration or accepting sensitive resumes. This phase does not certify that
public collection of personal data is ready. The mock-only demonstration is
available while these account-dependent steps remain outstanding.

## I. Create the Vercel project — after authorization

Import the same reviewed GitHub monorepo/commit. Framework **Next.js**, Root
Directory **`frontend`**, include source files outside the root (workspace lock).
Use one canonical production origin. Preview URLs must not share production
backend/database/auth credentials; never allowlist `*.vercel.app`.
Disable automatic Git deployments if releases must remain manual. Importing or
pushing a connected branch can deploy; keep release actions explicitly authorized.

## J. Exact Vercel install/build/routing

| Setting            | Value                                                |
| ------------------ | ---------------------------------------------------- |
| Root Directory     | `frontend`                                           |
| Node               | `24.x`                                               |
| Package manager    | pnpm **12.8.1**, root `packageManager`               |
| Lockfile/workspace | root `pnpm-lock.yaml`, `pnpm-workspace.yaml`         |
| Install            | `cd .. && pnpm install --frozen-lockfile`            |
| Build              | `pnpm build` from frontend root                      |
| Framework/output   | Next.js auto detection, default output directory     |
| Config             | `frontend/vercel.json` and `frontend/next.config.ts` |

Set `ENABLE_EXPERIMENTAL_COREPACK=1` per
[Vercel package-manager selection](https://vercel.com/docs/package-managers) to
honor the repository pin. Current app is Next.js 16.4.1 / App Router / React 19.3.
No static export: server rendering, Clerk and API gateway need the Next runtime.

Browser API calls stay relative. The server-only `BACKEND_INTERNAL_URL` builds an
external `/api/v1/*` rewrite to Render; it must be its public HTTPS origin.
No `NEXT_PUBLIC_API_BASE_URL` is read or needed. Production rejects missing or
insecure gateway/origin configuration; localhost defaults are native-only.

## K. Every required Vercel environment variable

Use [mock example](../deploy/frontend.env.example) or
[account example](../deploy/frontend.account.env.example), Production scope only.

| Variable                            | Value / visibility                                              |
| ----------------------------------- | --------------------------------------------------------------- |
| `BACKEND_INTERNAL_URL`              | `https://YOUR-BACKEND.onrender.com`, server/build only          |
| `FRONTEND_ORIGIN`                   | Exact canonical HTTPS frontend origin, server/build             |
| `BACKEND_PROXY_SECRET`              | Same private 32-256 character gateway secret as Render          |
| `PUBLIC_DEMO_ONLY`                  | `true` mock-only, `false` accounts + demo                       |
| `ENABLE_EXPERIMENTAL_COREPACK`      | `1`, platform build-tool flag                                   |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Account mode only: matching `pk_live_...`; intentionally public |
| `CLERK_SECRET_KEY`                  | Account mode only: matching `sk_live_...`; server secret        |

Vercel supplies `VERCEL=1` and `VERCEL_ENV=production`; do not set them in local
dev. Never add AI keys, database URLs/passwords, quota key, backend bearer tokens
or service-role keys to Vercel/browser variables. Next config does not copy backend
secrets into `env`/public runtime configuration. Rebuild after origin, backend URL,
public Clerk key or profile changes; rewrites/public values are compiled at build.

## L. CORS, gateway and canonical public URLs

Render `ALLOWED_ORIGINS=["https://YOUR-CANONICAL-FRONTEND"]`, with no trailing
slash, wildcard, path or credentials; Vercel `FRONTEND_ORIGIN` must match exactly.
Redirect alternate/custom/deployment origins to that canonical host. Keep auth
issuer, app origin and backend origin distinct; the API URL is not a Clerk issuer.

Vercel overwrites [client-IP metadata](https://vercel.com/docs/headers/request-headers).
The gateway strips incoming spoofed app headers, sets its secret only on forwarded
requests, and sends a validated IP for hashed quotas. FastAPI trusts that address
only after secret verification, with proxy-header trust disabled. Direct protected
Render calls return 403; health endpoints stay readable. No secret is returned to
the browser. Secure HttpOnly demo cookies remain host-only on the frontend origin;
CSRF/exact Origin checks and bearer ownership checks still apply.

## M. Explicit production migration and safe startup procedure

From the repository root, build the exact reviewed release image locally:

```sh
docker build -f deploy/backend.Dockerfile -t interview-prep-api:release .
```

Create an ignored operator-only `.env.migration.local` from the mock backend
example. Enter **owner** database URL privately, verified TLS, planned HTTPS
origin and generated validation keys. Keep `PUBLIC_DEMO_ONLY=true`, `AI_PROVIDER=mock`,
`AUTH_ENABLED=false`, empty AI keys and `CLEANUP_ENABLED=false`. Do not copy an
actual key file. For existing data first verify a recoverable backup/branch.
Run only after separately authorizing the real database change:

```sh
docker run --rm --env-file .env.migration.local interview-prep-api:release alembic upgrade head
docker run --rm --env-file .env.migration.local interview-prep-api:release alembic current
docker run --rm --env-file .env.migration.local interview-prep-api:release alembic check
docker run --rm --env-file .env.migration.local interview-prep-api:release python -m interview_prep.modules.questions.seed
docker run --rm --env-file .env.migration.local interview-prep-api:release python -m interview_prep.modules.questions.seed --apply
```

Expected head **`0012_ai_context_reviews`**. Dry-run catalogue publication validates
29 reviewed questions; first publication creates 29 versions, repeat publication
creates zero. It does not create users or fictional account history. Startup does
not seed. Development fixtures must never be installed into real accounts.

As table owner in psql, with repository root as the local working directory:

```sql
\i deploy/runtime-grants.sql
SELECT has_schema_privilege('interview_prep_runtime', 'public', 'CREATE');
SELECT has_table_privilege('interview_prep_runtime', 'alembic_version', 'UPDATE');
```

Both checks must be `false`. Reapply grants after every migration/catalogue update.
Use runtime credentials on Render. Free Render has no shell/one-off jobs; do not
turn on a paid plan just to migrate or give the API the owner URL. No auto-destructive
migration, `create_all`, reset, truncation or automatic downgrade is part of startup.

## N. Initialize and verify the isolated recruiter demo

No demo login or shared owner is needed. Clicking **Try Interactive Demo** calls
`POST /api/v1/demo/sessions` and transactionally creates a private fictional
candidate, sample resume/target, skill evidence, assessment/interview history,
roadmap and progress records. Each visitor receives a distinct opaque capability;
CSRF protects mutations. Static Project Defense's illustrative fixture loads on
explicit selection. All sample content/evaluation is labelled simulation.

While xKiro is down, use `/demo` directly. It always selects MockAIProvider; no
visitor supplies a key, and no mock result is attributed to Qwen. Account errors
retain submitted answers/state and report safe failures rather than silently
replacing them. New evaluations/reviews use existing ownership, input/token limits,
shared budgets, deduplication, completed-result reuse and bounded explicit retries.

With `CLEANUP_ENABLED=true`, expired demos/quotas/receipts are deleted at process
start and hourly **while running**. Authorization denies expired demo access even
before physical deletion. **While Render sleeps/is suspended, no cleanup runs**;
physical deletion waits for next successful startup/maintenance. Do not promise
24 hours plus one hour as an unconditional deletion SLA on Free. Existing
standalone cleanup remains available, using a separate ignored runtime env file:

```sh
docker run --rm --env-file .env.runtime.local interview-prep-api:release python -m interview_prep.cleanup
```

There is no public admin/cleanup URL. Operator backups/provider logs have separate
retention. Do not enter private resumes, repository secrets or personal answers in
the recruiter demo. See [privacy/security limits](SECURITY.md).

## O. Verify real xKiro — synthetic input only

After deployment is authorized/configured, sign in with a controlled test account,
create a harmless target such as `Python required; SQL preferred.`, open **Review
job description**, read the disclosure, consent and request once. Inspect returned
provenance for `model_assisted`, `XkiroProvider` and the exact Max `:free` model.
Repeat the same completed review once to verify saved-result reuse, not a second
upstream dispatch. Do not upload a personal resume for the first test.

For a local operator smoke against existing private backend configuration:

```sh
uv run --project backend python scripts/check_xkiro.py --live
```

This deliberately makes one synthetic request, zero retries, 128-token cap and a
60-second deadline, printing only safe status metadata. Phase 23A's one request
passed (HTTP 200); Phase 23B adds **no live inference**. Omni and hosted provider
availability still need account-specific verification. Do not run batches to test
free quotas or remove `:free` if a model is unavailable.

## P. Release smoke, fallback and local quality gates

After actual deployment, check:

```sh
curl --fail https://YOUR-BACKEND.onrender.com/health
curl --fail https://YOUR-BACKEND.onrender.com/api/v1/health/ready
curl --fail https://YOUR-FRONTEND/api/v1/health/ready
```

Readiness must report revision 0012. Then use two separate browser profiles: demo
resume/target/skills, assessment submission/review, interview pause/resume/review,
roadmap completion/progress and illustrative Project Defense. Confirm edits/exit
in one profile cannot change the other. Complete **Exit and delete demo**. For
accounts, verify protected routes, two-account isolation and safe consent errors.

Local checks (no hosted resources, AI always mocked):

```sh
uv run --project backend python scripts/check_backend.py
pnpm lint
pnpm typecheck
pnpm test
pnpm format:check
uv run --project backend python scripts/check_production.py
uv run --project backend python scripts/check_browser.py --api-port 18100 --frontend-port 13100 -- --workers=1
```

The production harness builds the Linux image and Next production gateway, uses
disposable TLS PostgreSQL/restricted grants, a **512 MiB** API, mock AI, temporary
HTTPS origins and generated test credentials, then removes its owned resources.
It does not measure hosted 0.1-CPU latency or prove live Clerk callbacks. The
browser runner builds its own matching API rewrite and tests a mock recruiter
journey on disposable data. Use free ports; existing application services remain
untouched. Exact Phase 23B results are in [PROJECT_STATUS.md](../PROJECT_STATUS.md).

## Q. Troubleshooting

| Symptom                                                    | Check/action                                                                                                                                                     |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| First request slow, HTML/loading response or fetch failure | Render cold start plus Neon wake can exceed browser timeouts. Wait, reload saved state and retry explicitly; never loop new sessions/evaluations.                |
| Production startup rejects schema/DB                       | Apply reviewed migration 0012, verify direct asyncpg URL, TLS trust and runtime grants; never downgrade/reset to fix it.                                         |
| Render /health succeeds but API readiness is 503           | Liveness is not DB availability; check Neon quota/wake/connectivity and readiness.                                                                               |
| `gateway_required` / `gateway_unavailable`                 | Match server-only gateway secret; rebuild with correct backend URL; access via canonical Vercel host.                                                            |
| CORS/CSRF rejection                                        | Exact canonical `ALLOWED_ORIGINS`/`FRONTEND_ORIGIN`, HTTPS, Origin, cookie and CSRF token. No wildcard workaround.                                               |
| Clerk sign-in fails or API 401                             | Matching live keys, correct production instance, issuer/audience/JWT template, DNS, authorized origin and token lifetime.                                        |
| Missing account credentials at Vercel build                | Configure both live keys or explicitly choose mock-only `PUBLIC_DEMO_ONLY=true`.                                                                                 |
| 429 / `ai_rate_limited`                                    | Respect Retry-After and budgets/free quota. Keep saved answers, use labelled demo; no paid substitution.                                                         |
| AI timeout/invalid output                                  | Saved work remains; one bounded explicit retry where allowed. JSON mode is not schema conformity.                                                                |
| Interview work stalled after sleep/restart                 | Open its saved session/review to wake reconciliation; expired/ambiguous work may receive partial/error feedback. No exactly-once inference guarantee.            |
| Upload/import busy or failed                               | Shared worker is occupied, bounded input or 512 MB/CPU limit reached; retry once later or use smaller synthetic material. Never execute imported code.           |
| Quotas affect unrelated visitors                           | Verify Vercel overwrites trusted IP header and gateway validation; do not trust arbitrary forwarded headers or disable quotas.                                   |
| Expired rows remain while inactive                         | Free service cannot run cleanup while stopped; next wake/manual restricted-role cleanup removes them.                                                            |
| Local env change has no effect in Docker                   | Images do not contain local env files. Native loader reads root then backend; Compose with backend-local values needs `--env-file .env --env-file backend/.env`. |
| Free service suspended                                     | Inspect provider usage/limits; do not provision paid resources to bypass limits without approval.                                                                |

Vercel's [external rewrite timeout](https://vercel.com/docs/limits) is finite;
current browser review waits are 75 seconds and ordinary calls can be shorter.
Warm the service manually before a scheduled walkthrough. Large synchronous
assessment batches can exceed these waits; reload the persisted attempt before
retrying so completed evaluation receipts can be reused.

## R. Redeploy updates, backups and recovery

1. Review diff/tests and both configuration profiles. Pin the same reviewed commit
   for frontend/API/migration image. Do not let a push silently deploy a connected
   branch while manual authorization is required.
2. Make and verify a recoverable backup/Neon branch within free limits. Apply only
   reviewed forward migrations and runtime grants; publish reviewed content.
3. Explicitly deploy Render, confirm startup/readiness 0012, then deploy/rebuild
   Vercel for profile/origin/key changes. Coordinate both sides for gateway rotation.
4. Smoke test demo isolation and relevant account/AI flows with synthetic content.
5. Roll back an image only when schema-compatible. Do not downgrade/drop tables or
   erase history as an improvised rollback. Restore a verified backup/branch for
   data recovery. Remove operator-only env files from active use when finished.

The current demo uses provider subdomains and the existing repository source.
Hosted backup/restore drills, custom DNS and Clerk callbacks have not been
verified. Complete the relevant steps before enabling the account profile.

## S. Avoid accidental charges

Keep Render **Free**, no cron/disks/workers/extra services, Neon **Free** and an
eligible Vercel/Clerk Hobby profile. Review the resource preview before applying
any Blueprint. Render workspace plan and individual compute plan are different;
account signup being free does not make paid service plans free.

Set spend controls/alerts where offered and review payment-method/overage behavior.
Do not select automatic upgrades, paid social/security add-ons, production
preview clones or larger compute. Keep AI budgets conservative, retries zero in
the account template, all xKiro IDs `:free`, and paid-model authorization false.
No xKiro key is needed at all for the initial mock-only recruiter release.
Provider terms/quotas can change; revisit the linked primary docs before release.
