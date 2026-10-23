# xKiro: primary real AI provider

xKiro is the recommended real provider; `AI_PROVIDER=mock` remains the safe,
zero-key default and the recruiter demo always uses MockAIProvider. Ollama and
OpenAI remain optional. Automated tests use mocked HTTP responses. An authorized
live resume check also passed; see [PROJECT_STATUS.md](../PROJECT_STATUS.md) for
the observed results and the distinction from a live Clerk/browser account session.

## Secure configuration

Create a key in your own xKiro dashboard. Add it privately in your backend hosting
service's environment store as **`XKIRO_API_KEY`**, or edit the existing ignored
`backend/.env` locally. Never paste the value into Codex chat, commit it, put it in a
frontend environment file, add `NEXT_PUBLIC_`, or use it as a Docker build argument.
Do not run commands that print environment values or expanded Compose configuration.

The native Settings loader resolves absolute paths from the code location: root
`.env` supplies defaults, then `backend/.env` overrides them, regardless of the
shell directory. Backend process variables take precedence over both; use the
hosting platform environment store in production. Missing dotenv files are fine.
Docker Compose normally reads root `.env`. To use an existing `backend/.env` too,
add `--env-file .env --env-file backend/.env` to each `docker compose` command.
AI configuration is passed only to backend services, never the frontend build.
Existing secret-file contents were not printed, copied or modified for this integration.

Keep existing database/auth settings and add:

```dotenv
AI_PROVIDER=xkiro
PUBLIC_DEMO_ONLY=false
XKIRO_API_KEY=
XKIRO_BASE_URL=https://api.xkiro.com/v1
XKIRO_MODEL_SMART=qwen/qwen3.8-max:free
XKIRO_MODEL_MULTIMODAL=qwen/qwen3.8-omni-flash:free
XKIRO_MODEL_ROUTES={}
XKIRO_ALLOW_PAID_MODELS=false
AI_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=1
AI_OWNER_HOURLY_CALLS=60
AI_OWNER_DAILY_CALLS=200
AI_GLOBAL_DAILY_CALLS=2000
```

Fill the empty key **in your private local file/platform environment only**.
The legacy names `XKIRO_REASONING_MODEL` and `XKIRO_MULTIMODAL_MODEL` remain
accepted. Prefer one spelling; new names win when both appear in the same
configuration source. Do not copy an example over an existing secret file.
Restart the native API, or rebuild/recreate the local backend and cleanup services
after reviewing your configuration. Use either the initial mock-only profile or the account + xKiro profile in
[DEPLOYMENT.md](DEPLOYMENT.md). The latter needs the existing [authentication setup](AUTHENTICATION.md) and privacy release
requirements; adding an AI key does not enable account authentication.

Adding a key does not refresh existing Docker images or enable login. Rebuild the
backend/cleanup image, apply the migration, then recreate those services when
updating an existing local Compose installation:

```sh
docker compose build backend cleanup migrate
docker compose run --rm migrate
docker compose up -d --no-deps backend cleanup
```

These commands preserve the database volume. They do not configure Clerk; follow
[AUTHENTICATION.md](AUTHENTICATION.md) before using authenticated browser uploads.
Rebuild/recreate the frontend too when updating its review UI or Clerk publishable
key (`docker compose build frontend`, then `docker compose up -d --no-deps frontend`).
The recruiter demo remains mock in either production profile.

For native development, apply the new migration before starting the updated API:

```sh
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

Run this from the repository root with its existing database environment. The
current head is `0012_ai_context_reviews`. For Compose use `docker compose run --rm migrate`
with the rebuilt backend image. For hosted databases follow the separate owner-role
commands and repeat `deploy/runtime-grants.sql`; never give the API a schema owner
password. The additive migration preserves existing rows. Its downgrade refuses
to discard saved analysis receipts; back up/restore rather than erasing history.

Missing/revoked keys, unsupported models and exhausted free allowances produce
safe errors. Startup does not send a provider request. Recruiter demo creation,
local extraction and objective grading remain usable without a key.

## Model routing and spending authorization

Every text operation defaults to **`qwen/qwen3.8-max:free`**: resume/JD analysis,
answer evaluation, contextual follow-ups, roadmap capability and project questions.
Technical interviews and Project Defense feedback use answer evaluation.
For a specific operation, provide a JSON map in `XKIRO_MODEL_ROUTES`, for example:

```dotenv
XKIRO_MODEL_ROUTES={"generate_followup":"qwen/qwen3.8-max:free","analyze_resume":"qwen/qwen3.8-max:free"}
```

Accepted keys are `analyze_resume`, `analyze_job_description`, `evaluate_answer`,
`generate_followup`, `recommend_roadmap` and `generate_project_questions`. Unknown
keys and malformed IDs fail validation. Routing is server configuration, never
derived from uploaded content or browser parameters. Routing changes alter the
provider version: cached analyses use a new identity, and active interviews refuse
to mix configurations. Provenance records the model actually selected per call.

The image adapter uses **`qwen/qwen3.8-omni-flash:free`**. Its typed `analyze_image`
capability accepts an explicitly supplied inline PNG/JPEG, maximum 64 KiB, and
returns validated summary/observations/limitations. It never fetches an arbitrary
image URL. There is no new public image-upload flow, OCR, audio or video feature.
Any future caller must obtain sharing consent and enforce ownership/budgets first.

By default **every xKiro ID must end in `:free`**. Non-free IDs require both an
explicit operator-selected model and **`XKIRO_ALLOW_PAID_MODELS=true`**. Treat that
flag as spending authorization; keep it false unless you deliberately approve
paid inference. No automatic paid ID, model substitution, web search, tool call
or remote-to-mock fallback exists. A returned different model is rejected.
The existing optional OpenAI provider still requires an explicitly selected model
and a separate key; selecting it deliberately opts into that provider's billing.

The requested free IDs and Chat Completions shape follow the current official
[xKiro API](https://docs.xkiro.com/api/chat-completions/),
[Max free model](https://xkiro.com/models/qwen/qwen3.8-max:free) and
[Omni free model](https://xkiro.com/models/qwen/qwen3.8-omni-flash:free) documentation.
Free-model availability and allowances can change. Use provider account spending
controls as well; an app-side suffix check cannot guarantee upstream billing policy.

## What sends data, and when

- **Resume upload:** parsing/evidence extraction stays local. Raw PDF/text is
  discarded as before. Clicking **Review resume evidence** first shows the
  configured provider and sharing disclosure. Only after your checkbox and
  explicit request are retained non-rejected claims/corrections and excerpts
  sent. Input is bounded to 50,000 characters. This is a retained-evidence review,
  not a full-document review. It never auto-confirms evidence or modifies claims.
- **Assessment:** its setup discloses the provider. Submitting written answers
  sends the question, answer and review criteria. Objective formats remain local.
- **Interview:** setup discloses sharing. Owned submitted answers are saved
  before evaluation; contextual follow-ups also send recent question prompts.
  Target-job selection remains local. Existing durable work prevents replay of
  interrupted dispatches and saves validated feedback/provenance.
- **Project Defense:** imports/static scanning/practice transitions stay local.
  A separate **Review defense answer** action for a submitted saved answer shows
  sharing consent first, then sends only that question, answer and review rubric.
  It does not send a source archive or execute code, change practice state, award
  objective correctness or count as verified performance.
- **Recruiter demo:** always labelled mock/simulation; no xKiro calls or keys.
  Account-only analysis endpoints cannot be used with a demo cookie.
- **Job description review:** explicit consent shares the latest saved description;
  returns grounded required/preferred/mentioned technologies plus summary/notes.
  Does not automatically confirm requirements.
- **Roadmap activity suggestions:** explicit consent shares at most six unfinished
  topics and saved evidence-based reasons, without raw assessment answers. Suggestions
  cover up to 600 minutes and leave the deterministic plan and completions unchanged.
- **Project practice questions:** explicit consent shares up to 30 static facts and
  file/line references. Generates six grounded questions without running source code
  or replacing the questions/answers in an existing defense.

**xKiro is a third party and routes to downstream model providers.** Review their
privacy/retention policies and remove sensitive details before agreeing. The
integration does not promise zero retention or that free inference is private.
Credentials and owner IDs never enter model prompts. Submitted text remains
untrusted data under a separate system message; responses render as text.

Opt-in review results are stored privately for reuse for reuse for up to **30 days, followed by cleanup while the service runs**, bounded to 128 KiB per receipt. Request identity
includes owner/source, resume revision, input, schema, provider routing version and
prompt version. Each dispatch has a unique token so an older in-flight response
cannot overwrite a replacement receipt after invalidation or expiry.
Unchanged completed requests return validated saved results without another call
or budget reservation. Resume evidence edits/deletions invalidate old reviews;
source/owner deletion cascades receipts. No raw input body is added to the receipt.
Generated feedback can quote sensitive source text; review its retention too.

Concurrent duplicate requests do not dispatch twice. Failed work allows at most
one further explicit attempt; cancellation/process loss leaves an ambiguous
`started` receipt that is not automatically replayed. These controls reduce
duplicates, but cannot guarantee exactly-once upstream computation or billing.
Assessment receipt retention remains its existing 48 hours; interview feedback
remains part of saved interview history. Operator backups have separate retention.

## Limits, validation and failures

Shared database budgets apply to each account and globally before real dispatch.
The defaults reserve up to 60 hourly / 200 daily owner units and 2,000 daily global
units. A request reserves **`1 + AI_MAX_RETRIES`** potential transport attempts;
with one retry, that is two units. Simulations use no real AI budget. Cache hits
do not consume one. Budget exhaustion returns 429 with Retry-After.

The adapter uses non-streaming `POST /v1/chat/completions`, a 4096-token cap and
JSON-object mode with an explicit JSON Schema in trusted instructions. Both the
completion envelope and domain payload pass Pydantic validation; source spans,
rubrics, question uniqueness and other existing domain checks still apply. Only
one stopped assistant completion with the requested model is accepted. Refusals,
tool calls, incomplete/token-limited output and malformed JSON are rejected.

On Qwen, [JSON-object mode](https://docs.xkiro.com/guides/structured-output/)
is applied as a prompt instruction, not a hard syntax constraint. Invalid output
is never persisted. Four shared-client slots bound concurrent remote calls per
API process; the total deadline includes waiting for a slot. Global database
budgets also apply across processes.

The total deadline covers connection, reading, retries and backoff. Response bodies
are capped at 256 KiB and domain text at 128 KiB. Retry-After is respected within
the total deadline; a long delay fails safely. Authentication/credit/model errors,
invalid output and ambiguous read/write timeouts are not automatically replayed.
Errors expose safe codes, never provider bodies, headers or credentials. Rate
limits never cause a paid-model fallback or falsely labelled mock feedback.

Resume/JD extraction asks xKiro for short exact evidence quotes, not character
offset arithmetic. The backend locates the first exact occurrence in the source
and calculates Unicode start/end positions locally. Missing or paraphrased quotes,
unexpected model-supplied offset fields and duplicate skill names are rejected.
The resulting public contract still passes the original Pydantic and domain/span
validation. Provider identity is versioned (`xkiro-chat-v2`) for this contract;
cached results and active interview identities cannot silently mix versions.

Free-model latency varies. One live request exceeded the default 30-second
deadline; a subsequent corrected resume review completed in 25.14 seconds with a
60-second diagnostic deadline. If needed, set **`AI_TIMEOUT_SECONDS=60`** in the
backend environment and restart it. This stays within the existing hard limit and
does not increase retries or enable a paid model. The live check did not edit the
user's root `.env`.

## Verification without credentials

```sh
uv run --project backend python scripts/check_backend.py
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The backend check uses an owned disposable database, migrates through head and
checks schema drift/rollback preservation. HTTP tests use `httpx.MockTransport`
with fictional keys, cover success/routing/failures and cached analysis ownership,
and block live HTTP at collection. No real key or paid call is needed. Frontend
tests cover sharing consent, provenance and recoverable errors. Live provider
availability, model quality, allowances and retention remain operator checks.

After mocked provider tests pass, explicitly run one minimal synthetic request:

```sh
uv run --project backend python scripts/check_xkiro.py --live
```

This makes at most one request with zero retries, the exact Max `:free` ID, a
128-token cap and a 60-second deadline. It prints only safe status metadata, not
the key, headers or raw response. The Phase 23A run returned HTTP 200 in 3.86
seconds with accepted model identity and validated JSON. It checks connectivity
and parsing, not the quality or availability of every feature or the Omni model.

## Free-hosting deployment profile

[Phase 23B deployment preparation](DEPLOYMENT.md) supports one Render Free API
with startup/hourly-while-awake cleanup. Expired data can remain physically stored
while the service sleeps, but expired demo access and review reuse stay blocked.
The conservative account example uses 10 hourly / 30 daily owner calls, 100 global
daily calls and zero transport retries. The recruiter demo remains independent
of xKiro outages and credentials. No additional live request was made in 23B.
