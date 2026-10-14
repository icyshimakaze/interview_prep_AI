# Accounts and recruiter demo

The account routes use Clerk's maintained Next.js integration. FastAPI verifies
every account bearer token independently and resolves a local principal from its
trusted issuer/subject. No password table or client-submitted owner ID is used.
Recruiter demo routes use a separate expiring opaque cookie and fictional records.

## Configure real accounts

No Clerk credentials were provided for this implementation. Until configured,
`/sign-in`, `/sign-up`, and `/app/dashboard` display an explicit unavailable state
with a working **Try Interactive Demo** link. Backend account access stays closed.

1. Create/select a Clerk development application. Enable the desired sign-up and
   sign-in methods through Clerk. Keep email/password/recovery policy there.
2. In its JWT templates settings, create **`interview-prep-api`**, using the
   instance's normal RS256 signing key, a **60-second lifetime** and **5-second
   allowed clock skew**. Set its custom claims to:

   ```json
   { "aud": "interview-prep-api" }
   ```

   Clerk supplies `iss`, `sub`, `azp`, `iat`, `nbf`, and `exp`. Do not replace them,
   use a custom signing key, or put profile/owner/email data in this template.
   The template name must match the frontend's `getToken` call.
   [Clerk JWT templates](https://clerk.com/docs/guides/sessions/jwt-templates)

3. Copy the public key and server secret into ignored local configuration. For
   Compose, use root `.env`:

   ```dotenv
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_instance_key
   CLERK_SECRET_KEY=sk_test_your_server_key
   AUTH_ENABLED=true
   AUTH_ISSUER=https://your-instance.clerk.accounts.dev
   AUTH_AUDIENCE=interview-prep-api
   FRONTEND_ORIGIN=http://localhost:3000
   ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
   ```

   Use the actual issuer origin from that instance, without a trailing slash,
   path, query or embedded credentials. Keys/issuer must belong to the same instance.

4. For native Next.js, place the public/secret keys and `FRONTEND_ORIGIN` in ignored
   `frontend/.env.local`; the native backend reads the `AUTH_*`/origin values from
   root `.env`. Public publishable keys are designed for browser use. Secret keys
   and database/rate-limit secrets must never use a `NEXT_PUBLIC_` name.
5. Rebuild/restart: `docker compose up --build -d`, or restart the native services.
   The public key is compiled into the frontend; a runtime change alone is insufficient.
   Enabled API account mode refuses invalid/missing issuer configuration. Public
   account operation requires both correctly configured services.
6. Open `/sign-up`, complete the managed flow, and check `/app/dashboard`. Create
   a preparation profile, sign out, and confirm dashboard access requires sign-in.
   Repeat with a second account to verify empty isolated state before any real data.

The frontend proxy protects `/app/*` with trusted frontend origins. API requests
use the SDK's API-template token in memory. Sign-out clears visible data before
calling Clerk; no custom bearer localStorage, refresh cookie, or shared account
cache is introduced. Account pages render only data matching the current subject.

## Backend trust and authorization

`verified_identity`, `require_account`, and `require_demo` are reusable FastAPI
dependencies in `modules/identity/dependencies.py`. Each private read/write filters
by that resolved principal; request schemas reject unknown fields such as `user_id`.
Database compound ownership constraints provide an additional integrity boundary.

The API permits RS256 only and requires issuer, single exact audience, subject,
expiry, issued-at, not-before, and an allowed frontend `azp`. Token lifetime is at
most 60 seconds with 5 seconds of verification leeway. Pending session status is
rejected. Signing keys come only from the configured issuer's
`/.well-known/jwks.json`; token-provided key URLs/keys and unexpected algorithms
are rejected. The configured discovery pattern follows
[Clerk's verification guidance](https://clerk.com/docs/guides/sessions/manual-jwt-verification).

Discovery has a 3-second request timeout, 64 KiB budget, bounded RSA key set,
no redirects and no environment-proxy inheritance. Keys cache for 300 seconds
by default. Unknown key IDs trigger a bounded refresh; expired keys and failed
discovery fail closed with a sanitized 503. Invalid/missing tokens return structured
401 with `WWW-Authenticate: Bearer`; inactive/capability-denied identities return 403. Missing or foreign private resources return indistinguishable 404 responses.
All errors contain a request ID, omit raw claims/driver errors, and use `no-store`.

Account bootstrap is explicit `POST /api/v1/account/session` with `{}` after
verification; GET requests do not create principals. Existing suspended principals
stay suspended. `GET /api/v1/account/dashboard` returns bounded owned collections.
`PUT /api/v1/account/profile` uses an expected revision and row lock; stale edits
return 409. Owned resume/target reads demonstrate the same boundary. The backend
does not read Clerk cookies or accept a demo cookie on account routes.

The shared authenticated shell covers all ten `/app/*` sections. The dashboard
leads new accounts to **Settings / Profile** at `/app/settings`; that form saves
through the existing profile endpoint. Loading, validation, save errors and explicit
reload recovery preserve the server revision contract. Subject changes remount
private UI state. See [the UI route map](UI_FOUNDATION.md).

Candidate profile and target-job CRUD now run through the existing account boundary.
Profile edits/deletion include the expected profile ID and revision; target edits/
deletion include revision. Optional background information and user interests are
never inferred or sent to an AI service. Source links are validated and stored,
never fetched. See [candidate context, contracts and retention](CANDIDATE_CONTEXT.md).

Resume upload/review now uses the same account boundary. Every list, detail,
evidence edit/add/delete and resume deletion resolves the verified owner on the
server. Uploads are bounded PDF bodies, never accepted in the fictional demo.
Evidence mutations and deletion include the aggregate revision; foreign IDs are 404. See [resume processing, API and retention](RESUME_PRIVACY.md).

Short-lived custom JWTs can remain valid after managed sign-out until expiry plus
clock leeway. There is no claimed instant token revocation. Signed Clerk lifecycle
webhooks, account export/erasure with provider reconciliation, production CSP,
public ingress, backup/restore and real file ingestion remain later release work.
Local suspension is checked on every protected request. No real upload or AI
operation has been opened by this slice.

## Recruiter demo

The landing page's **Try Interactive Demo** opens `/demo`, without sign-up or an
AI API key. An exact allowed Origin bootstraps a new random capability and a
transactionally seeded private workspace. A returning visitor reuses it with
CSRF protection. No recruiter name/email is collected.

The candidate **Aarav Rao (fictional)**, employer, resume statements, target job,
assessment attempts and interview feedback are authored examples. Disclosure stays
visible on every section and result labels say simulation; they are never described
as platform usage, hiring success, validated ability or actual AI evaluation.
Visitors can explore profile/resume/target, assessment/interview history, roadmap
and progress, mark their own sample tasks complete, reload, and erase their demo.
Sections have deep links under `/demo/`; **Exit and delete demo** opens a keyboard-
accessible confirmation dialog before calling the same owned deletion endpoint.

Demo APIs accept only their cookie and reject any Authorization header. Every
visitor owns a separate principal and distinct records; neither another demo's
UUID nor a real account resource ID grants access. Task completion is idempotent,
requires exact Origin/CSRF, and records one simulated progress event. The allowlist
accepts no arbitrary resume/job/repository input, uploads, external fetches or AI calls.

Cookies are host-only, SameSite=Lax; the session is HttpOnly and scoped to
`/api/v1/demo`. The separate CSRF cookie is readable for request protection. Only
SHA-256 session/CSRF hashes are persisted. Production settings require secure
cookies/HTTPS. Workspaces expire within 24 hours; hourly cleanup erases expired
principals and their private records. **Exit and delete demo** erases immediately.
Expired/invalid cookies can be cleared with **Start a fresh demo**; live-session
reset still requires its CSRF token. No reset selects an owner supplied by the client.

Creation is limited to two workspaces per direct network peer/hour using a rotating
hashed identifier. Reset/exit do not bypass that quota. Public reverse-proxy trust
and client-IP handling must be configured before release; the local Compose stack
deliberately binds to localhost. Browser tests need a clean isolated test database
or an unused hourly quota, as production quota behavior is not disabled for tests.

## Verification limits

Backend tests use actual RSA signatures with a mocked **trusted JWKS transport**,
not an authentication bypass, and real PostgreSQL. They cover invalid claims,
signature/algorithm/key-URL attacks, cache rotation/outage, suspended users,
forged ownership input, foreign IDs, separate account/demo credentials, expiration,
CSRF, repeated seeding/completion and erasure. Browser tests use actual local
services for demo isolation/persistence/deletion and the missing-key account state.
Live Clerk sign-up/sign-in/sign-out requires the configuration above and has not
been exercised without credentials. See [current results](../PROJECT_STATUS.md).

Question-bank account endpoints use the same verified bearer identity. Shared
published questions are readable; private question metadata, bookmarks, response
history and concept access remain owner-scoped. Demo bookmarks and practice
submissions require exact Origin/CSRF; responses are explicitly simulation.
Expected concepts unlock only after an owned submitted response to that version.
See [question-bank API and retention](QUESTION_BANK.md).

Assessment configuration/history/read/save/submit/abandon endpoints retain these
account/demo identity boundaries. Every allocation and response is owner-scoped;
demo mutations require Origin/CSRF. Keys are returned only in an owned completed
review. Principal/attempt locks, revision checks and idempotent final submission
protect retries and concurrent requests. See [assessments](ASSESSMENTS.md).
