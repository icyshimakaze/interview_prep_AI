# Clerk development setup

## Objective and scope

Complete the existing Clerk integration for the dashboard-selected application
`app_3L935GM9Y4AtOVdSfyYKtxgbBm0`, verify the development UI and start the local
application. Preserve pinned `@clerk/nextjs` 7.9.14 (Core 3), account/demo isolation,
existing working keys, and all hosted configuration. Do not run `clerk init`,
create a replacement application, upgrade dependencies, push or deploy.

## Verified starting state

- Working tree clean on `rebuild/professional-v2`; Next.js 16.4.1, Node 26.8.1,
  pnpm 12.8.1, Clerk provider/proxy/routes and backend JWT verification exist.
- Provider currently wraps `<html>`; catch-all auth pages lack Suspense.
- Public navigation has sign-in; the account shell has custom sign-out. Add the
  missing sign-up/profile controls while retaining the existing sign-out cleanup.
- Backend authentication requires a matching issuer, enabled authentication and
  the `interview-prep-api` JWT template (audience of the same name, 60-second
  lifetime and 5-second skew). Hosted account mode remains disabled.
- Existing environment files will not be read or printed. User has been asked to
  authenticate the CLI from their own terminal before application-level access.

## Affected components

Root layout, catch-all sign-in/sign-up routes, public/account navigation, relevant
frontend tests, authentication documentation and project status. Install official
Clerk agent skills if absent. Restore development keys only through the selected
existing application after CLI login, and only if missing; never overwrite working
keys or silently switch applications.

## Database and API

No new schema or API contract. Existing verified issuer/subject ownership,
bearer-token contracts and opaque demo capability remain unchanged. Startup
discovered local schema 0010; existing additive migrations 0011/0012 were reviewed
and applied as described below, preserving existing records. No user records were
created by the agent; first sign-up was completed by the user.

## Frontend, security and privacy

Place the provider inside `<body>`, keep the explicit missing-key fallback, add
Suspense around managed auth screens and adapt the existing navigation with
sign-up and signed-in profile controls. Keep secrets server-side. Do not inspect
environment files, display credentials or store bearer tokens. Keep sign-out
clearing account data. Clerk account access requires user-completed CLI login;
runtime checks must not be mistaken for live sign-in verification.

## Implementation order and checks

1. Inspect existing integration and official Core 3 documentation; obtain CLI
   command help and install missing official skills.
2. Apply the minimal provider/auth-screen/navigation corrections and regression
   checks for configured/unconfigured and signed-in/signed-out controls.
3. Run frontend lint, strict types, unit tests, production build, Clerk doctor,
   and local browser checks. Run relevant backend checks only if backend changes.
4. After confirmed host-terminal login, inspect the existing project link. Link
   to the selected application only when needed and safe; pull missing keys only.
   Configure/verify the development JWT template and backend settings without
   reading existing environment files. If user input is required, document it.
5. Start local services where configuration permits; verify public and managed
   auth controls. Ask the user to complete their first sign-up. Record exact
   check results, remaining configuration and live-flow limitations in status.

## Outcome

Provider placement, auth-screen Suspense, conditional public navigation and the
account profile control are implemented. Existing proxy/token/ownership behavior
is preserved. Added navigation states and a regression for private-state removal
after SDK sign-out. Official Clerk skills (20) are installed in the user's
global skill directories. The installer also attempted PromptScript, which does
not support global skills; the applicable agent installations succeeded.

Lint, strict types and the production build passed. Initial complete frontend
suite: 176 tests passed; the added sign-out regression and navigation tests then
passed (13 tests in two files). Final complete-suite result is recorded in
`PROJECT_STATUS.md`. One focused sandbox run hit `spawn EPERM`; the unchanged
command passed with host subprocess access.

Four existing Chrome checks passed across two runs: public desktop/mobile
navigation/accessibility, keyboard behavior, live backend/PostgreSQL connectivity,
and missing-key auth routes. The updated standalone frontend is running on
`http://localhost:3100` (PID 33984); existing Docker services on 3000/8000 remain
running. Logs are ignored under `.cache/clerk-setup/`.

Host-side Clerk CLI 4.0.0 diagnostics returned exit 1: not logged in, no project
link, and no frontend local environment file. The user requested login help and
was given the exact terminal command and browser-authorization instructions.
No environment files were read, keys pulled, application links changed, users
created, hosted settings changed, commits made, pushes or deployments performed.
Live Clerk verification remains pending user-completed terminal login; next link
the selected app safely, restore missing development keys, configure its JWT
template and matching backend settings, and verify user-completed sign-up.

## Authenticated continuation

The user completed host-terminal login. Host diagnostics confirm valid login;
the selected application is now linked, and its missing development keys were
restored through Clerk to ignored `frontend/.env.local` without reading the file.
Clerk's public domain metadata identifies the trusted development issuer as
`https://square-marlin-4895.clerk.accounts.dev`. No JWT templates existed.

Create the required template after reviewing a CLI dry run: custom audience only,
60-second lifetime, 5-second skew, instance-managed signing. Configure only the
existing local backend using ignored `.cache/clerk-setup/compose.auth.yaml` to
enable authentication and allow the existing 3000 origins plus preview 3100.
The root environment file and hosted configuration remain untouched. Rebuild and
restart only the owned frontend preview at 3100. Undo the backend runtime override
by recreating it with the base Compose file alone. No database/schema changes.

Verify complete Clerk diagnostics, fresh frontend build, actual managed sign-in
and sign-up UI, signed-out protected redirects, backend readiness and token
rejection. First-account creation remains a user action; do not create a user or
claim an authenticated account journey without actual user-completed sign-in.

### Local runtime compatibility discovered during startup

The pre-existing local backend image predates xKiro support and rejected the
current configuration when recreated. Rebuilt the backend image from current
locked source. The API then starts and resolves the trusted Clerk JWKS, but
readiness finds local schema `0010_security_budgets` rather than required `0012`.
Review of existing migrations 0011/0012 confirms that they only create a new
owned AI receipt table, then add nullable references and expand its source
constraint. No pre-existing application rows/tables are rewritten or deleted.

Apply these existing migrations locally before continuing; no new migration or
API change is authored. Existing database data/volume are retained. Older local
services remain compatible with these additive changes. Do not downgrade the
application database or remove stored rows as recovery; retain the schema and
correct configuration/code if startup still fails. Hosted schema is unaffected.

### Local frontend launcher correction

Live signed-out browser checks exposed a pre-existing startup issue that the
missing-key fallback could not expose: NextURL normalizes loopback IPs to
`localhost`, but our native launchers bound `127.0.0.1`. Clerk's same-page internal
rewrite then appeared external to Next and stalled in a self-proxy request.
Matching the listener to `localhost` resolved this in the standalone server;
actual managed forms, protected redirects, backend readiness and malformed-token
rejection now pass. Use `localhost` by default for native dev and standalone
launchers, preserving explicit hostname overrides and Docker configuration.

The standalone launcher must also load the CLI-generated ignored
`frontend/.env.local` through Node's built-in loader, because Next's standalone
artifact does not copy that file. Do not print it or replace injected variables.
Verify the corrected default launcher on a separate disposable local port while
the user keeps the working 3100 app available for first sign-up. No new dependency.
Remove only next dev's generated AGENTS/types changes after stopping that owned
dev process; they are unrelated to the final standalone setup.

## Final outcome

Setup is complete for local development. Clerk doctor exits 0; the selected app,
missing development keys, required JWT template and backend trust are configured.
The live standalone app remains available at `http://localhost:3100` (PID 22988).
The user completed first sign-up and confirmed the workspace/profile icon, then
selected current email/password/Google/Microsoft methods and individual accounts.

Configured production build, final lint/types, launcher syntax and all 177
frontend tests (20 files, 85.16s) passed. Real Chrome form/navigation/mobile/
protected-redirect/readiness/401 checks passed both on the main configured app and
through the corrected default launcher on a temporary port. That temporary server
was removed; the signed-in user app was kept running. Desktop/mobile screenshots
were visually inspected. The targeted 23-client-bundle key-pattern scan had no
matches. No hosted setting, push, deploy or new dependency changed.

Remaining verification: live profile save/sign-out and second-account isolation
were not exercised. The full backend test gate was not rerun because backend
source was unchanged; existing migration execution and actual readiness/JWKS
checks passed. The older preparation-stage pending-login notes above are history,
superseded by this final outcome and `PROJECT_STATUS.md`.

### Missing-asset navigation correction

The final server-log check exposed session lookups on missing static assets:
their fallback page renders the public shell, while the proxy intentionally skips
asset extensions. Keep the server-only configured-key guard and move the public
session display into a small client component using Clerk's provider context.
This avoids a server auth call on an unmatched fallback route, shows a sign-in
loading state, and keeps authenticated data authorization in the existing
proxy/backend. Verify missing-asset 404s produce no Clerk middleware errors in
addition to the existing real-form/redirect checks. Restart only the owned local
preview after rebuilding; preserve user account/session/database state. The final
configured build, lint/types, all 177 tests and live browser checks passed again,
including missing-asset 404s with an empty final server error log.
