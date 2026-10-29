# Project Status

Updated: 2026-10-30 (Asia/Calcutta).

## Acceptance repair and documentation publication authorized

Read-only evidence confirmed two authorizations in separate tabs; the old runner
tracked the first state and retained the provider tab. Its cleanup sent the
relative logout request to GitHub, where it returned 422. The operator observer
and origin guards are repaired locally; application runtime and all accounts
remain unchanged. Focused checks: 15 correlation/cohort tests, six isolated
browser checks and nine pinned-library/database tests passed. Strict frontend
types, focused ESLint, Python Ruff and strict mypy passed.

The user separately authorized publishing this documentation-only branch and a
reviewable PR. The earlier publication hold is superseded; no merge or settings
change is authorized. Production remains closed/demo. See the
[diagnosis and verification boundary](docs/PRODUCTION_ACCEPTANCE_REPAIR.md).

## GitHub-only launch attempted; closed rollback verified

**Production: ROLLED BACK. Public GitHub signup acceptance: FAILED.** The public
demo remains available at <https://interviewprepai.webredirect.org>. See
[the final launch report](docs/FINAL_LAUNCH_2026_10_30.md). This result
supersedes the preparation GO below.

- Published only the frozen 464-file candidate on temporary branch
  `release/github-only-public-2026-10-30-37bbc9a5`, commit
  `dbbe982186373ccaea1c7a34bd60a3d9f0f5d3a3`. Hosted production build
  `dpl_8m3CbKEnmcD3oLtyd9k2LgJTqYsu` reached READY; all 462 uploaded source
  files matched (Vercel excludes the two root ignore files). All 464 match the
  published commit; no dirty-tree application build.
- Approved bridge/restoration/promotion completed. Physical Android preflight
  passed Terms/Privacy 200, GitHub-only UI, disabled Google/password
  registration/ recovery, public RSA JWKS, anonymous protected denial and
  readiness 200/0013.
- One real callback completed public enrollment and a distinct-email verified
  third account exists, but the callback did not match the runner's fresh state.
  No matching callback arrived within four minutes. Mandatory first step failed;
  saved work, restart, revocation, returning login and new-owner isolation were
  not reached in this attempt. No public signup success or root cause is
  claimed.
- Exact rollback verified: canonical frontend
  `dpl_A5RrDr2ro6Qw52ipZCcvWgyzNBLu`; backend `dep-dbhpqbui0phs73f0jrtg` LIVE,
  reusing compatible artifact `dep-dbh6t7l9fdbs7384h740`. Original five frontend
  bindings and saved closed backend environment restored; rotated credentials,
  0013 and gateway preserved.
- All 399 pre-launch business rows across 52 public tables, existing UUID
  mappings, three auth users and both encrypted backups preserved. Automatic
  signout was 422; cleanup subsequently revoked only the exact
  phone-cookie-proven test session. Final physical closed-route/security and
  demo create/read/dashboard/ delete smoke passed. Only owned ADB forwarding
  removed.
- Portfolio README, source-verified feature/stack overview, architecture,
  reviewer walkthrough, local setup, testing/security/troubleshooting guidance,
  sanitized screenshots/provenance and repository-presentation recommendations
  are prepared on local branch `docs/portfolio-homepage-2026-10-30`. Previous
  technical README retained. Markdownlint: 12 files / zero errors; 259 relative
  references valid; README diagram and six images render at desktop/mobile
  widths. 12 external URLs returned 200 on Windows; the two canonical URLs
  failed transport there and returned 200 on Android. Four public remote tip
  trees: 1,611 entries / 640 unique blobs, zero known-credential matches or
  private artifact paths; not a complete history audit. Documentation PR
  publication is held because the user conditioned it on verified live release.
  No default-branch change, merge, DNS edit, purchase, Google activation or
  second release attempt.

Next: review the prepared local documentation; before any separately authorized
retry, resolve callback correlation and the cleanup 422. The new account is
retained and must not be described as never enrolled in a later test.

## Clerk GitHub/Vercel release — deployed and verified

The user explicitly requested committing/pushing the existing Clerk changes and
updating the Vercel website. See the
[release plan](.agent/plans/clerk-github-vercel-release.md). The GitHub release
branch is `rebuild/professional-v2`; its verified starting head was `d23d276`.
Committed and pushed **`c6dfda14be38fbb85cc9e267a43d2ef510794b51`**, then verified
the remote head. All three jobs in
[CI 40125359511](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40125359511)
passed, including backend tests/migrations and browser/container packaging.
Unauthenticated GitHub API status polling reached its rate limit; the current
public run page independently confirmed all three named jobs completed successfully.

- Isolated the Clerk/frontend/local-launcher/docs changes in a separate
  checkout, preserving unrelated Phase 25 backend/parser/evaluation work. No
  local environment file, account state or private key was copied into that
  checkout.
- Fresh isolated lint, strict types, production build and **177 tests / 20
  files** passed (59.30s). Four Chrome tests passed in **8.3s**: public
  desktop/mobile navigation/axe, keyboard/reduced motion, real backend readiness
  and missing-key account screens. Launcher syntax and whitespace checks passed.
  Windows Git checkout CRLF initially caused formatting failures; normalizing
  only the isolated checkout restored the unchanged whole-repo Prettier gate. No
  unrelated source change was added to the release.
- Live Vercel inspection confirms project `prj_wsxEcvVC17paXs5pco4K9eHwWKgd`,
  account `team_vyOtLBqMjk5sQ9DTmzCcbwiN`, new **READY** production deployment
  **`dpl_53VkStbwKUFnBnoigpBv28hhJNeN`** at **`c6dfda1`**, and canonical alias
  **<https://interview-prep-ai-icyshimakaze.vercel.app**> pointing to that
  deployment. Both deployment-ID and canonical-alias lookups confirm the exact
  source SHA. The existing hosted environment still has no Clerk keys.
  Production account mode is not enabled by a Git push or frontend code release.
  The user confirmed they have only the `vercel.app` address and no owned
  domain. Preserve the hosted demo profile; the new account controls cannot
  become active until production Clerk/domain configuration is available.
- The initial exact-SHA Vercel production deployment request returned **403**:
  the connection must reauthorize access to `icy-shimakaze` / the existing
  account scope. Called Vercel's prescribed `authorize_team_access` recovery and
  presented its one-use, 10-minute consent link to the user. This is service
  authorization, not a new request for permission to deploy. After the user
  completed renewed authorization, the identical pinned request succeeded.
  Vercel's build log reports completion in 10s; the deployment reached READY
  with no alias error.
- **Post-release:** four Chrome checks passed on the canonical website in
  **15.2s**, covering public desktop/mobile/axe, keyboard/reduced motion, actual
  backend readiness and the explicitly unavailable account screens. Inspected
  unedited hosted desktop/mobile screenshots. HTTPS/security headers, missing
  asset 404s, proxied readiness at schema 0012, and account API **403
  `demo_only`** with no-store passed. Thirteen referenced public JavaScript
  assets had zero private Clerk key pattern matches. These read-only checks
  created no accounts, demo visitors or uploaded data.
- Runtime error/fatal counts for the new deployment in the queried 30-minute
  window returned no recorded groups. This does not establish long-term
  monitoring; drains were not inspected. See the
  [release report](docs/CLERK_CODE_RELEASE.md) for scope and verification
  limits.

GitHub publication and the Vercel code update are complete. Render/Neon settings,
schema and the hosted demo profile were unchanged. The previous Vercel deployment
remains available for rollback. Hosted Clerk sign-in still requires an owned
domain, production Clerk keys/instance and matching backend configuration; do not
describe this code-only release as activation of public accounts.

## Clerk development setup — configured and user verified

The user approved Clerk setup, completed host-terminal login, and selected existing
application `app_3L935GM9Y4AtOVdSfyYKtxgbBm0` (`interview_prep_ai`). See the
[setup plan](.agent/plans/clerk-development-setup.md) and updated
[authentication guide](docs/AUTHENTICATION.md).

- Linked that application and restored only its missing development keys to the
  ignored `frontend/.env.local` through the CLI. Created missing JWT template
  `jtmp_3L9EXNVIyVT1LZ6Fe1Ry8KF44NS` after a reviewed dry run: audience
  `interview-prep-api`, 60-second lifetime, 5-second skew, instance-managed RS256.
  Host-side Clerk CLI 4.0.0 diagnostics now return **exit 0**. The sole warning is
  that the optional production instance is not configured.
- Preserved pinned Clerk Core 3 (`@clerk/nextjs` 7.9.14), Next.js 16.4.1 and the
  existing proxy, API-template tokens and server ownership checks. Skipped
  `clerk init` to avoid creating or replacing an application. Moved the provider
  inside `<body>` and wrapped managed sign-in/sign-up screens in Suspense.
- Configured public navigation now offers sign-in/sign-up while signed out,
  and a workspace link/profile control while signed in. Added the managed profile
  control to the account header, preserving explicit sign-out and missing-key
  fallbacks. Regression coverage verifies removal of private state when SDK
  sign-out changes the session, including sign-out through the profile control.
- Installed the 20 official Clerk skills globally. Applicable agent installs
  succeeded; the installer additionally reported that PromptScript does not
  support global installation. No project dependency/lockfile change.
- Enabled only the local backend through ignored
  `.cache/clerk-setup/compose.auth.yaml`: trusted issuer
  `https://square-marlin-4895.clerk.accounts.dev`, matching audience and exact
  local 3000/3100 origins. The cached backend image predated current configuration
  and failed startup on the newer AI provider setting; rebuilding from current
  locked source fixed that. The local database was still at 0010. Reviewed and
  applied existing additive migrations 0011/0012; no new migration, existing-row
  rewrite, deletion or database reset. Readiness now returns **200** at 0012, and
  the actual verifier fetched one trusted public Clerk signing key.
- Fixed native startup: NextURL normalizes loopback IPs to `localhost`, while
  the old `127.0.0.1` listener made Clerk's internal rewrite appear external and
  stall. Native dev/standalone defaults now use `localhost`; explicit hostname
  overrides and Docker configuration remain supported. The standalone launcher
  loads ignored `frontend/.env.local` through Node's built-in loader, preserving
  injected variables. No dependency or lockfile change.
- **Verification:** `pnpm lint`, `pnpm typecheck`, configured `pnpm build`, Node
  launcher syntax and final `pnpm test` passed: **177 tests across 20 files**, in
  **85.16 seconds**. One earlier focused sandbox run hit `spawn EPERM`; the
  unchanged command passed with reviewed host subprocess access. The initial
  configured build hit Windows `EBUSY` because its old preview was running;
  stopping only that owned process allowed the unchanged build to pass.
- Fresh isolated Chrome checks passed real signed-out navigation, managed
  sign-in/sign-up forms, 375px sign-up overflow, signed-out workspace redirect,
  proxied database readiness, missing/malformed-token 401 and no-store headers,
  and zero JavaScript page errors. Repeated successfully on a disposable port
  using the corrected default launcher; stopped only that verification server.
  The final log check exposed server-session lookups in missing-asset fallback
  pages. Moved the configured public session display into a small client
  component under the existing server configuration guard, rebuilt and reran the
  gates. Final missing-asset checks return 404 without Clerk middleware errors.
  Inspected unedited desktop sign-in/mobile sign-up screenshots under
  `.cache/clerk-setup/browser/`. No Clerk user was created by the agent.
- Earlier missing-key verification also passed four existing local Chrome tests
  for public/accessibility/keyboard/connectivity/fallback behavior. The configured
  browser bundle scan found zero private Clerk key pattern matches in 23 files;
  this is a targeted pattern check, not a complete secret/security audit.
- The user completed first sign-up and confirmed **workspace and profile icon
  appeared**. They explicitly chose to keep **email/password, Google, Microsoft**
  and **individual accounts**. Existing methods were retained; Organizations were
  not enabled. Separate live profile-save/sign-out and two-account isolation
  journeys have not been exercised; component/ownership regression coverage is
  preserved. Backend source was unchanged and its full test gate was not rerun.

The configured local app remains at **<http://localhost:3100**>, PID **22988**;
ignored logs and runtime override are in `.cache/clerk-setup/`. Existing Docker
frontend/database/cleanup remain on 3000/5433; backend 8000 now runs current
source with the local auth override. The root environment file was not inspected
or modified; application processes loaded the ignored frontend configuration
normally without printing it. No hosted settings, production account mode,
commit, push or deployment changed. **Next:** continue using the local account
and complete profile-save/sign-out plus a second-account live isolation check
before claiming the full account journey verified. Production prerequisites
remain in the runbook.

## Personal resume uploads and hosted reliability — released

The user requested fixes for hosted failures and support for real resumes, then
explicitly selected private temporary uploads without production sign-in. See the
[plan](.agent/plans/resume-uploads-and-hosted-errors.md).

- Added **Upload your resume** on the landing page and dashboard. `/demo/resume`
  now uses the existing real PDF parser and evidence review/correction/deletion
  screen. Server-derived provenance distinguishes uploads from the fictional
  example. Account authentication remains unchanged and disabled on the hosted
  profile; temporary uploads expose no external AI review.
- New `/api/v1/demo/resume-library` routes derive ownership from the opaque demo
  capability, require allowed Origin/CSRF for mutations and reuse parser bounds,
  revisions and import quotas. Raw PDFs/full text are discarded; retained excerpts
  expire with the workspace or are erased by exit. Upload completion refreshes
  principal state to reject expiry/suspension during parsing. No migration, host
  variable change or new dependency is required.
- Reproduced bootstrap HTTP 502 and measured a **53.66-second Render wakeup**.
  Added a bounded 75-second GET-only readiness wait before one bootstrap POST,
  safe network/timeout recovery and 30-second interview deadlines. A retained
  hosted visitor completed start, pause/resume, follow-up and final review. One
  browser request took **12.367 seconds** versus **178 ms** of Render processing.
  The original Phase 24 creation timeout was not reproduced; its exact cause is
  unproven and Vercel runtime logs remain unavailable (403). Test deletion returned
  204, then dashboard 401; Neon counts are zero workspaces/sessions. No quota reset.
- Verified **173 frontend tests / 19 files**, lint, strict types and production
  builds. **25 local Chrome tests passed in 1.8 minutes**, including the complete
  demo, real synthetic PDF upload/correction/reload, foreign resume rejection,
  erasure, upload layouts at 375/768/1440/1920 and accessibility. The production
  TLS/container harness also passed PDF upload/isolation/deletion in its non-root
  512 MiB Linux backend with restricted DB grants. Owned disposable services and
  ephemeral credentials were removed.
- Ruff (210 files), strict mypy (197 sources), whole-repo Prettier and whitespace
  checks pass. Security scan found no configured-secret/pattern matches in 480
  tracked/new files or 23 browser JS bundles; no actual dotenv paths are tracked
  or in reachable filename history. Initial backend run had 630 passed and two
  new expiry fixtures violating existing DB checks; fixed the fixtures without
  weakening constraints. Final complete backend gate passed: **633 tests in
  490.36 seconds**, disposable migration down/up/drift, matching OpenAPI and
  preserved legacy hashes/seeds. Its disposable database was removed.

The user explicitly authorized this release-branch push and free-tier release.
Published `cf08aa49cc02a311a4637c2ba5770f13056bbb82` to the requested branch and
verified all three jobs in [CI 40099102208](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40099102208)
succeeded before deploying. Render `dep-dbebdotg1s2s73f29oo0` is live at that SHA;
Vercel `dpl_HJMVCGL5ziQK86VkijTAbdnP9sMs` is READY with the canonical alias and
same SHA. Backend health/readiness and new protected library checks passed before
the frontend release. No migration, host variable change or paid resource.

Hosted checks passed personal PDF upload/correction/reload, interview pause/
follow-up/completion/review, questions, assessments, Project Defense, roadmap/
progress and four-width upload overflow checks. Upload accessibility passed;
inspected unedited desktop/mobile synthetic-upload screenshots. A second visitor
could not read foreign uploaded/sample resume, project or assessment records
(404). First UI exit returned 204 and redirected home. The main hosted suite was
**1 passed / 1 failed** in 9.5 minutes: its post-delete Node dashboard read hit
`getaddrinfo ENOTFOUND`; the second UI exit sequence did not run, but authenticated
finally-cleanup erased that visitor (204). A separate **read-only follow-up passed
in 4.7 seconds**: browser dashboard/library/workspace and Node dashboard reads
returned 401, with no capability cookies or JavaScript page errors. No additional
visitor was created or quota reset. Final Neon counts are **0 demo workspaces,
0 sessions, 0 resumes and 0 resume versions**. The first journey captured 126 API
responses with no 5xx or JavaScript page errors; upload returned 201 in 6.558s.

New HTTPS/readiness/gateway/CORS/closed-account checks passed; 12 landing and
16 public-route scripts had zero configured private-value matches. See the
[release report](docs/RESUME_UPLOAD_RELEASE.md) for exact boundaries. Historical
host revisions/failures below are superseded for current state. Production Clerk,
live xKiro and the deferred full-data recovery drill remain outside this release.

## Phase 24 — current hosted verification

See the [phase plan](.agent/plans/phase-24.md) and
[deployment report](docs/PHASE_24_REPORT.md). The user authorized free-tier
deployment work, while requiring separate authorization before any Git push.
The working tree began clean at `71d525c`. With explicit push authorization,
published `7e6bcfd` to `origin/rebuild/professional-v2` and verified its remote SHA.
Complete GitHub Actions run
[40021576996](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40021576996)
passed before deploying that exact frontend revision. Vercel deployment
`dpl_4CnVhRSUVR3LCk8HwGRhp8s2Nwgq` reached READY with the canonical alias; fresh
post-release HTTPS/readiness/gateway/CORS/closed-account/12-asset checks passed.
Render remains Free/live at `c5ca23e`: its backend/deployment Git trees are
identical to the new release, so no backend rebuild was needed. Neon remains 0012.

- Fresh backend gate passed: **628 tests in 492.79 seconds**, Ruff lint/format
  (209 files), strict mypy (196 sources), disposable migration round-trip/drift,
  OpenAPI and legacy hashes/seeds. Its disposable database was removed.
- Frontend lint/strict types, **166 tests across 18 files**, ordinary production
  build, production gateway/container harness and **25 local Chrome tests in
  1.2 minutes** passed. The first Vitest invocation hit sandbox `spawn EPERM`;
  approved subprocess access passed the unchanged command. Production-harness
  TLS/restricted-role/512 MiB/cookie/CSRF/gateway/quota/cleanup checks passed and
  removed only their owned resources; existing application services were preserved.
- Fresh hosted HTTPS/readiness at 0012, direct gateway rejection, exact/foreign
  CORS and closed account APIs passed. Five configured private values had zero
  matches in 471 tracked/new release files and 23 local browser bundles. The 12
  landing scripts also passed, and a later 16-script public-route scan found no
  matches for four applicable private values and confirmed the retention copy.
  No actual dotenv file is tracked or found by filename in history.
- The real public Chrome check passed at **375/768/1440/1920 pixels**, including
  overflow, landing axe, keyboard, privacy and unavailable-account checks with no
  console/page errors. Two inspected hosted landing screenshots are documented.
  The normal **02:30 IST** hosted journey/account-disabled suite returned **1 passed,
  1 failed**: profile/target/resume, questions and assessments passed, then interview
  creation showed **signal timed out** and never displayed the answer field.
  Its 15-second client deadline expired; Playwright waited 30 seconds. Render
  logged successful interview GETs but no completed POST. Root cause remains
  unresolved; Vercel runtime errors/logs both return 403, with no CLI/browser
  fallback. Two-visitor isolation, UI exit and remaining hosted flows did not run.
  The failed visitor was erased with its own authenticated cleanup request.
- An operator diagnostic-runner error closed stdin and erased the remaining
  permitted visitor before the interview action. It consumed the second slot and
  is not verification. Final Neon counts are **0 demo workspaces / 0 demo sessions**;
  creation counters were not reset, with the next normal window at **03:30 IST**.
- The user confirmed **no owned domain/production Clerk setup** and **no saved
  Render payment method**. Production accounts/xKiro stay disabled. No real AI
  request or key transfer to hosting occurred. Account export/erasure, Clerk
  deletion reconciliation and strict script CSP remain release gaps.
- Automatic approval review rejected a prepared full Neon export/local restore
  drill because it could copy personal data into a local archive. It did not run;
  the user chose to defer the drill. Vercel team/billing read and its documented
  authorization recovery both returned 403; no bypass was attempted. Project
  status/deployment/environment-name reads work. Neon account billing remains
  unavailable through its project-scoped connection.

Released the Settings retention correction to acknowledge delayed physical
deletion while free hosting sleeps. README/runbook/report distinguish verified
public demo behavior from disabled account/live-AI flows. No new resource, paid
feature, production migration, default-branch merge or force push occurred.
Next: obtain authorized Vercel runtime-log access and reproduce interview creation
with timing in a retained disposable visitor in a normal quota window. Complete
hosted isolation/exit and remaining flows afterward. Full recruiter-walkthrough
readiness is not established. Account mode remains gated by the listed prerequisites.

## Hosted public demo — 24 October 2026

The user confirmed Render **My Workspace** and the personal Vercel Hobby account
`icyshimakaze`. The authorized Free deployment is live at
**<https://interview-prep-ai-icyshimakaze.vercel.app**>. README and the
deployment runbook now link to the real site. No manual provisioning remains for
this mock-only profile.

- Render: `srv-dbdrrr9srm7s73cpdt6g`, Free Docker in Singapore, automatic deploys
  off, status `live`. It uses the restricted Neon runtime role and private gateway
  configuration. The creation connector cannot configure an HTTP health path;
  current platform checks use TCP. Explicit `/health` and readiness probes passed.
- Vercel: `prj_wsxEcvVC17paXs5pco4K9eHwWKgd`, production deployment
  `dpl_AprjfXimTGg9oVJ9zP5ich1kYq9L`, status `READY`, canonical domain verified.
  Pinned Git source was used without automatic Git linkage. Next.js uses Node
  24.x, pnpm 12.8.1 and production-only configuration, with Singapore functions.
- Both hosts run release `c5ca23ea5a8b1d502f6e53d22b32b3bdde73debb` from
  `rebuild/professional-v2`. Its complete GitHub Actions run
  [40012341296](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40012341296)
  succeeded before deployment. No application code changed in this hosting step.
- HTTPS, frontend/backend readiness at revision 0012, security headers, absence
  of the gateway secret in checked responses, direct-backend rejection, exact
  canonical CORS, foreign-origin rejection and closed account APIs passed.
  All 12 JavaScript assets referenced by the public landing page were checked
  against the generated deployment secrets with zero matches. A scan of all
  467 tracked files also found zero deployment-secret matches; changed Markdown
  passes Prettier and the diff has no whitespace errors.
- Hosted Chrome: original demo suite returned **1 passed, 1 failed**. Candidate
  edits, question practice and assessments passed before a 15-second navigation
  timeout entering Interviews. Account-disabled UI passed. A separate bounded
  follow-up passed mock interview pause/follow-up/completion, illustrative
  Project Defense and roadmap persistence/completion/history. Its overall test
  failed because the reused progress helper expected objective assessment grades
  that the fresh follow-up visitor had not created. Inspection confirmed the
  correct empty objective history and persisted simulated practice. Neither
  failure was hidden or counted as a passing test. Hosted two-visitor isolation
  and the UI exit sequence remain uncompleted; full disposable-browser CI had
  previously passed 25 tests. Do not reset production creation quotas to rerun.
- Both test visitors were removed with their own authenticated cleanup requests;
  final verified counts are **0 demo workspaces and 0 demo sessions**. Final
  frontend/readiness returned 200 and unauthenticated demo dashboard returned 401.
  The operator network consumed its two-per-UTC-hour creation allowance.

Existing unrelated services/projects were preserved. No paid service, custom
domain, public account registration or live AI request was added. Actual dotenv
files remain unchanged; deployment secrets/receipts are ignored local operator
files. Owner credentials were never supplied to the runtime hosts. Vercel project
creation/deployment/configuration/status work; optional team-detail and build-log
reads returned a scope-authorization error and were not bypassed. They were not
required to verify this successful public deployment.

Next task: use the public demo; complete account export/erasure, Clerk deletion
reconciliation, strict script CSP and production Clerk configuration before
opening account mode with real xKiro. Additional hosted isolation/browser checks
can run within a later normal quota window. Backups/restore and live account
callbacks remain unverified. Earlier sections below are historical phase records.

## Hosted Neon initialization — 24 October 2026

All three direct hosting connections are authenticated. Verified account access
through Codex's documented app-server API without starting any model turns;
the current chat still does not expose the remote MCP tools directly.
Release `12daed1` has a green complete GitHub Actions run.

Initialized the user's selected existing Free Neon database after verifying it
had no public tables or runtime role. The first migration attempt exceeded its
180-second operator deadline and rolled back; reinspection confirmed an empty
schema. A bounded retry completed every reviewed migration through
`0012_ai_context_reviews`, and Alembic reported zero schema drift. Catalogue
validation found 29 questions, initial publication added 29 versions and repeat
publication added zero.

Created the restricted runtime role through SQL, applied the reviewed grants and
verified runtime login, no schema CREATE privilege, no migration-history UPDATE
privilege and no `neon_superuser` membership. The application's actual production
readiness function passed using that runtime role and verified TLS. An initial
operator call supplied an engine instead of the required session factory; the
corrected invocation passed. Owner credentials stayed in memory; generated runtime
and gateway credentials are in ignored private deployment configuration. Actual
dotenv files were not edited and no live AI request was made.

The existing Neon region is Singapore (`ap-southeast-1`); aligned the Render
Blueprint/runbook default to Singapore. No Render service or Vercel project has
been created for this app. The unrelated existing student-management service and
existing Vercel projects were preserved. Render's connector explicitly requires
the user to identify a workspace before creation. The user subsequently confirmed
"My Workspace" and the personal Vercel Hobby account; hosting was completed in the
phase recorded above. Account/Clerk release gaps remain as documented below.

## GitHub release publication

Deployment continuation: release `c39d70a` has a green hosted
[quality run](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/39985334206).
The provenance correction also passed the original exporter in a fresh clone
with `core.autocrlf=false` and `core.eol=lf`; source hashes and tests were unchanged.
The user identified an existing Free Neon project and branch. Render/Vercel
plugins are installed but expose no callable account tools; Neon tools were
removed. No direct hosting MCP entries previously existed. Configured official
Render, Vercel and project-scoped Neon MCP entries through Codex CLI; browser
OAuth flows await user completion, then the extension must reload to expose the
tools. No hosted resources or production data have been changed. Details are in
the [hosting-access plan](.agent/plans/hosting-access.md).

The user authorized committing/pushing the prepared changes and completing
available deployment work on 23 October 2026. Release `19999f7` was committed and
pushed to `origin/rebuild/professional-v2`; remote SHA was verified. The index scan
checked 139 release files against three configured private values and credential
patterns with zero findings. Actual dotenv files remain ignored and unchanged.

The first hosted Linux CI run exposed four Windows-only `CREATE_NO_WINDOW`
references that native Windows mypy accepted. Replaced conditional expressions
with statement-level `sys.platform` guards, preserving hidden Windows subprocess
behavior. Ruff lint/format and strict mypy pass for native Windows and the Linux
target (196 sources). Existing focused resume-worker tests (5) and project-analysis
tests (32) pass. An initial direct invocation of DB-backed tests lacked their
required disposable DB and produced 28 setup errors; hosted CI supplies that DB.
The correction is published as `b86ebb8`. Hosted results are available in the
[branch's quality workflow](https://github.com/icyshimakaze/interview_prep_AI/actions/workflows/ci.yml?query=branch%3Arebuild%2Fprofessional-v2);
confirm a green run for the selected release revision before production.

Built the corrected release image locally as `interview-prep-api:release` and
`interview-prep-api:b86ebb8`. Its Linux PDF/project subprocess smoke passed as a
non-root user with 512 MiB memory, and no dotenv files were present in the image.
No hosted resources, real database migrations or live AI calls
were made in this release step. No browser session, linked Vercel project or cloud
CLI credentials were available. Neon, Render and Vercel integrations were found
but are not installed/connected; the user must connect them to enable hosted work.
The remaining account-mode release gaps below are unchanged. See the
[release plan](.agent/plans/github-release.md).

Hosted CI follow-up: Linux passed 627 backend tests, with one provenance failure
because Git's LF checkout of `questions.json` differed from its recorded original
CRLF hash. The same mismatch affected legacy `requirements.txt`. Pin those two
immutable legacy files to CRLF checkout in `.gitattributes`; preserve all recorded
hashes, source contents, exporter validation and tests. Verify a fresh checkout
with automatic newline conversion disabled before pushing the correction.

Deployment-guide follow-up: checked current provider documentation and moved the
Blueprint's `DATABASE_URL` and `ALLOWED_ORIGINS` prompts from the environment group
to the service. Render ignores group-level `sync: false`; generated keys and other
defaults stay in the group. Updated the runbook accordingly. No deployment or
secret-file change. Formatting and whitespace checks passed for this correction;
hosted Blueprint validation remains part of the user's import review.

## Phase 23B — free-tier production deployment preparation

Completed 23 October 2026. See the [A–S deployment runbook](docs/DEPLOYMENT.md),
[full preparation report](docs/PHASE_23B_REPORT.md) and
[phase plan](.agent/plans/phase-23b.md). No push, hosted deployment, paid resource,
existing application-data migration or actual dotenv-file change occurred.

- Replaced the paid Starter + cron Blueprint with **one Render Free web service**,
  retaining Vercel and Neon. No cron/worker/disk/Render DB is provisioned. Initial
  profile stays zero-key mock; complete backend/frontend account examples enable
  Clerk + xKiro on the **same app** while recruiter demo remains isolated/mock.
- Production now validates selected AI/auth/security settings, rejects placeholder
  gateway/database secrets, and checks database/schema read-only before serving.
  Startup never migrates or seeds; head remains **0012**, with no schema change.
  Render probes `/health`; explicit `/api/v1/health/ready` still checks DB/revision.
  Production docs/OpenAPI routes remain disabled.
- In-process cleanup runs at startup/hourly while awake. **Sleeping/suspended
  services cannot perform scheduled physical deletion**; expiry authorization
  still denies access. Updated runbook/privacy copy rather than promising an
  hourly deletion SLA on Free. Existing standalone cleanup remains available.
- Free profile uses 600-second idle interview polling, owned-read/mutation wakeups
  and a lost-wakeup fix; durable jobs retain existing fences/failure behavior.
  PDF/project processing shares bounded capacity, set to one slot on Free.
- Added content-free production request metadata logging (method, route template,
  status, duration and random request ID), with raw access logs off. No raw paths,
  queries, headers, bodies, IPs or identities. Added production HSTS and required
  matching Clerk live keys for the Vercel account profile. Backend credentials
  remain outside client bundles; no new public API-base variable is needed.
- Documented exact monorepo Docker/Next commands, all real environment names,
  manual Neon migrations/grants, safe per-visitor demo initialization, Clerk
  DNS/JWT/redirect settings, secret entry, redeploy/recovery and spending controls.
  Account example conservatively uses zero retries and 10 / 30 / 100 owner-hourly /
  owner-daily / global-daily AI budgets, with exact requested free Qwen IDs.

Final verification:

- Full backend gate passed: **628 tests in 435.83 seconds**, Ruff lint/format
  (**209 files**), strict mypy (**196 source files**), fresh migration, complete
  downgrade/upgrade round-trip, zero schema drift, OpenAPI/contracts and legacy
  hashes/seeds. Corrected one new test's expected demo bootstrap status to its
  existing **200** contract; the focused and complete reruns passed. No check
  was disabled or weakened.
- Frontend zero-warning lint, strict TypeScript and **166 tests across 18 files**
  passed. Vercel-production gateway build, browser production build and final
  ordinary native production build passed. TypeScript regeneration equality,
  repository Prettier, Actionlint, Compose config and Git whitespace passed.
- Full local production harness passed at 0012 with verified PostgreSQL and
  frontend/backend TLS, restricted runtime grants, non-root **512 MiB API**,
  mock/no AI credentials, 29 catalogue versions/zero repeat writes, secure cookies,
  CSRF, exact origins, gateway spoof rejection, quotas and cleanup. This is not
  a hosted 0.1-CPU load/reliability benchmark.
- **25 Playwright tests passed**, one Chrome worker: persisted recruiter journey,
  visitor isolation/deletion, assessments/interviews, roadmap/progress, illustrative
  Project Defense, error recovery, desktop/mobile/keyboard and automated axe checks.
- Production-account regression verifies signed test JWT/JWKS, ownership and a
  mocked real-provider failure while the demo stays mock/usable. No live Clerk
  callback or hosted authentication claim. **No live inference in 23B**; earlier
  23A smoke remains historical evidence only.
- Four configured private values had zero matches in **436 checked source files**
  and **23 browser JS files**. No actual env files tracked now or found by filename
  in reachable history; production image contains no dotenv files. Existing env
  ignore rules verified. Verification-owned DBs/containers/servers and generated
  runtime credentials were removed; unrelated existing resources were preserved.

Ready for a separately authorized, limited recruiter preview within provider
free-tier limits. Personal steps remain: canonical domain/profile choice, free
platform/repository account connections, private secret entry, Neon roles/backup/
migration grants, Clerk production domain/DNS/JWT/OAuth and actual hosted flow
verification. Render sleeps/restarts, Neon/Vercel/Clerk quotas apply, and xKiro free
availability is not guaranteed. Do not provision paid services to bypass limits.

Before broad personal-data account registration, resolve existing self-service
export/erasure, Clerk deletion reconciliation and strict script-CSP release gaps.
The running local stack was not refreshed; its previously observed revision 0010
still requires the documented image/migration update. No public URL was claimed.
Next task: review the runbook and complete account-dependent setup/release gaps;
deploy only under separate explicit authorization.

## Phase 23A — complete xKiro integration and verification

Completed 23 October 2026 against the existing working tree. See the
[detailed nine-part report](docs/PHASE_23A_REPORT.md) and
[phase plan](.agent/plans/phase-23a.md). Existing uncommitted work and actual
root/backend/frontend secret files were preserved. No push or deployment.

- Verified the pre-existing provider, schema/domain grounding, technical/STAR
  rubrics, adaptive interviews, resume-evidence reviews, saved Defense feedback,
  quotas and mock demo; kept those boundaries and deterministic engines.
- Native Settings now read absolute root `.env`, then `backend/.env`, regardless
  of shell cwd; process environment wins. Added requested `XKIRO_MODEL_SMART` and
  `XKIRO_MODEL_MULTIMODAL` with backward-compatible legacy aliases. Added a
  placeholder-only backend example and updated backend-only Compose forwarding.
  Compose users with a backend-local key must specify both dotenv files as
  documented in [XKIRO.md](docs/XKIRO.md). Actual dotenv files were not edited.
- Connected opt-in saved job-description review, roadmap activity suggestions
  from evidence-based saved reasons, and six project practice questions from
  bounded static facts. Provider disclosure, explicit sharing consent and owned
  sources precede dispatch. Existing requirements, plans, evidence and defense
  runs are not mutated by these suggestions. No repository code is executed.
- Additive migration **`0012_ai_context_reviews`** extends existing receipts with
  composite owned source references, cascades and one-source validation. It
  preserves existing rows/cache identities and refuses downgrade when new-source
  results would be erased. Existing 30-day cleanup, cache reuse, quota reservation
  and bounded explicit retry/fencing logic apply to the new operations.
- Added four concurrent remote-call slots per shared application HTTP client;
  total timeout includes slot wait. Database owner/global budgets remain shared
  across processes. Free IDs remain unchanged; no paid or silent mock fallback.
- After **160 mocked provider/schema/config/rubric/concurrency tests passed**,
  executed exactly **one** minimal synthetic Max-free request (128-token cap,
  60-second deadline, zero retries). **HTTP 200 in 3.86 seconds**: authentication,
  exact `qwen/qwen3.8-max:free` identity and JSON validation passed. No private
  document/answer was sent; no key/header/raw response was printed or saved.

Final verification:

- Complete backend gate passed: **610 tests in 401.94 seconds**, Ruff lint/format
  (**205 files**), strict mypy (**192 source files**), fresh upgrade, schema drift,
  full downgrade/upgrade round trip, OpenAPI equality and legacy hashes/seeds.
  The disposable databases created by these runs were removed. A new fixture
  typo exposed by the first full run was corrected; no check was weakened.
- Frontend zero-warning lint, strict typecheck and **162 tests across 18 files**
  passed; the final Next.js production build passed. Repository Prettier and
  regenerated TypeScript contract equality checks passed. Offline backend wheel
  and source-distribution builds also passed. Browser/container production
  harnesses and live Clerk flows were not repeated in this phase.
- No actual dotenv files tracked now or found by filename in reachable Git
  history. Configured keys were absent from checked source, **23 browser JS
  bundles**, and both Python package artifacts; neither archive contains actual
  env files. Root/backend/frontend secret-file ignore rules were verified.
- Tests use fictional credentials and in-memory HTTP; live HTTP is blocked in
  pytest and CI needs no xKiro key. New regressions cover environment precedence,
  requested/legacy variables, unsupported request statuses, concurrent/queued
  deadlines, new source ownership/consent/cache/cascade/failures, guarded downgrade,
  one-call synthetic smoke behavior and UI rerender/provenance parsing.

Limits: the single live request establishes connectivity/parsing, not feature
quality or Omni availability. Resume review still uses retained evidence;
roadmap suggestions cover six short topics and at most 600 minutes; project
questions use up to 30 static facts. Results require human review and cannot
validate competence. Existing large synchronous assessment latency, account
erasure/export and provider-retention limitations remain documented.

The current local frontend/liveness/readiness return 200, but the running API
still reports **`0010_security_budgets`**. It was not refreshed or migrated.
Next: review/apply **0012**, refresh runtime grants and backend images, configure
and test Clerk for real account flows, then complete the documented hosted release
checks under separate deployment authorization. Public recruiter demo stays mock.
No existing application data or running service was changed by verification.

## Live xKiro resume verification (preceding phase)

Used the user-authorized root environment key and supplied resume for actual free
xKiro inference. The key was never printed, copied to an artifact or sent to the
browser; the root `.env` and original PDF were not modified.

- Real PDF upload returned **201**: one page, **35 retained evidence entries**.
  Anonymous analysis access returned 401 and denied sharing consent returned 422
  before dispatch. Protected endpoints used a locally signed test account and
  test JWKS in a disposable database, not a real Clerk/browser login.
- The initial 30-second request timed out. A 60-second diagnostic attempt returned
  HTTP 200 in 32.69 seconds but had incorrect model-generated evidence offsets
  (21 of 30 mismatched lengths); domain validation correctly rejected it.
- Fixed the xKiro document wire contract: the model supplies exact quotes, and
  the backend computes Unicode source positions locally. Unsupported/paraphrased
  quotes, unexpected fields and duplicate names remain rejected. Public Pydantic
  schemas and domain validation are unchanged. Versioned provider identity to
  `xkiro-chat-v2`; Ollama/OpenAI/mock behavior is preserved.
- The corrected live review returned **200** in **25.14 seconds**, using
  **`qwen/qwen3.8-max:free`** with real `model_assisted` provenance: **29 grounded
  skill mentions and six suggestions**. This is review feedback, not verified
  competence. The private result is in ignored `.cache/live-xkiro-resume-result.json`;
  the redacted verification report is `.cache/live-xkiro-check.json`.
- Repeating the review reused the saved result with **no second upstream call or
  quota reservation**. The recruiter demo remained `MockAIProvider` with no AI
  call. All live-check disposable databases were removed. There were three
  explicit resume inference attempts total (timeout, rejected output, success),
  all using the requested free model; no paid model or silent mock fallback.
- Focused mocked provider/schema tests: **113 passed**. The complete backend gate
  passed: **594 tests** in 380.72 seconds, Ruff lint/format (**199 files**), strict
  mypy (**187 sources**), fresh migration/downgrade/upgrade and drift checks,
  OpenAPI equality and legacy hashes/seeds. Its disposable container/database and
  generated credentials were removed. New regressions cover quote-only wire
  schemas, Unicode/duplicate-source positions, invented/inexact quotes, unexpected
  offset fields and duplicate skill rejection. Repository formatting/whitespace
  checks passed. Frontend/public contracts were unchanged; frontend/browser gates
  were not repeated in this backend-only correction (preceding results below).

The running local website is reachable (HTTP 200), but its existing Compose API
still reports **`0010_security_budgets`**, **`AI_PROVIDER=mock`** and
**`AUTH_ENABLED=false`**; that image has no xKiro support. The root environment
selects xKiro and loads the key, but the running container has not been refreshed.
Adding the key alone does not rebuild containers, migrate the database or configure Clerk.
The current-source backend resume flow is live-verified; the running browser's
authenticated upload/review flow is not. Follow [the local update/key guide](docs/XKIRO.md)
and [authentication setup](docs/AUTHENTICATION.md) to enable it. A diagnostic
60-second deadline was used; the root's 30-second default was preserved. The
guide documents the optional 60-second setting for variable free-model latency.
No existing application data migration, auth change, deployment or push occurred.

## xKiro integration (preceding phase)

Implemented xKiro as the recommended real account provider using its fixed
OpenAI-compatible Chat Completions endpoint. Mock remains the default and the
zero-key recruiter demo is unchanged. Existing Ollama/OpenAI adapters remain.
See [the plan](.agent/plans/xkiro-provider.md) and [secure setup](docs/XKIRO.md).

- Backend-only `XKIRO_API_KEY` is masked/excluded from Settings serialization.
  Existing secret files/values were not printed or modified; no live inference was requested.
  Default models are `qwen/qwen3.8-max:free` for text/reasoning and
  `qwen/qwen3.8-omni-flash:free` for the bounded inline-image adapter. Typed
  per-operation routes are server configuration. Non-free IDs require an explicit
  configured model and `XKIRO_ALLOW_PAID_MODELS=true`; no automatic paid fallback.
- Pydantic envelope/domain validation rejects malformed JSON, partial completions,
  tool calls, refusals, incorrect model identity and invalid evidence/rubrics.
  Existing total deadlines, body/token limits and retry rules are reused. xKiro
  rate-limit errors receive a safe distinct code; other adapters retain behavior.
- Assessments/interviews use existing per-owner/global database budgets and saved
  feedback. Routing changes alter frozen provider identity; per-call provenance
  records the routed model, including contextual follow-ups. Objective grading,
  selection, extraction, static scanning and practice transitions remain local.
- Added opt-in account resume-evidence review and saved Project Defense answer
  feedback. UI disclosure and sharing consent precede dispatch to xKiro/downstream
  providers. Raw PDFs/source archives are not sent. A retained-evidence review is
  not full-document analysis and cannot confirm claims or validated performance.
- Additive migration **`0011_ai_analyses`** adds bounded owned analysis receipts,
  composite source/owner constraints, 30-day expiry and cleanup. Completed results
  are reused before a new budget/call; concurrent/ambiguous dispatch is fenced.
  Resume revisions participate in cache identity; unique dispatch tokens prevent
  late success/failure responses from overwriting replacement receipts.
  One further explicit retry is allowed for failed work. Evidence mutations
  invalidate old reviews and source/owner deletion cascades them. No existing
  application data was migrated; update/grant instructions are documented.
- Updated root/production env examples, backend-only Compose variables, CI/test
  isolation, README, provider/privacy/deployment docs and generated API contracts.
  The native env loader reads the ignored root `.env`, not `backend/.env`.

Verification:

- Complete backend gate: **589 tests passed** in 430.61 seconds, including 29
  mocked xKiro cases and nine saved-analysis cases. These cover all six text
  operations, image routing, free/paid guards, deadlines/errors, consent/ownership,
  budgets, cache reuse/invalidation, expiry and stale-dispatch replacement fencing.
  Ruff lint/format passed (**198 files**) and strict mypy passed (**186 source files**).
- Fresh upgrade through **`0011_ai_analyses`**, downgrade/upgrade round trip and
  schema drift checks passed on an isolated disposable PostgreSQL instance.
  OpenAPI contracts and legacy hashes/seeds matched. The temporary database,
  container and generated credentials were removed after verification.
- Frontend zero-warning lint, strict typecheck and **158 tests across 18 files**
  passed. The 11 new review tests cover explicit sharing, simulation provenance,
  keyboard focus, safe retries/disclosures and actionable AI errors without
  exposing upstream text. Review text wraps within narrow containers. Repository
  Prettier and regenerated TypeScript-contract equality checks passed.
- Complete **Next.js 16.4.1 production builds passed**, including the production
  gateway configuration and final ordinary local target (`http://127.0.0.1:8000`).
  The Linux backend production image also built successfully.
- `scripts/check_production.py` passed locally at migration 0011: **mock AI with
  no AI credentials**, TLS database/frontend/backend, non-root API, restricted
  runtime grants, 29 seeded catalogue versions with zero repeat writes, secure
  cookies/CSRF, exact CORS, gateway spoofing rejection, quotas and cleanup.
  Browser bundles contained none of its generated server credentials. Owned
  containers and ephemeral credentials/private key were removed afterward.
- **25 Playwright tests passed** against a production frontend, temporary API
  and separate database with mock AI. Desktop/375px/320px layouts, account-form
  component fixtures, keyboard/skip links, dialog focus/Escape/recovery, reduced
  motion, axe A/AA checks and the persisted candidate journey passed. The runner
  removed its servers, database, container and generated credentials.

Earlier resource-blocked attempts are superseded by these successful final checks.
Verification used serial gates, one browser/build worker and bounded Node heaps.
Three older disposable test databases remain on the pre-existing application
PostgreSQL server; their originating runs could not be confirmed, so they were
preserved. This verification's owned resources were removed.

Next: configure a key privately using [docs/XKIRO.md](docs/XKIRO.md), apply the
documented migration/grants and restart the backend when ready to enable account
AI. Existing application data and running Compose images were not replaced.
Live provider quality/availability, Clerk callbacks, hosted deployment and manual
screen-reader/device checks remain unverified; none is claimed by mocked tests.
No real xKiro/OpenAI call, application-data migration, deployment or push occurred.

## Production deployment preparation (preceding phase)

Prepared **Vercel + Render + Neon** without creating hosted resources, deploying,
or requiring a paid AI API. Follow the
[deployment runbook](docs/DEPLOYMENT.md) and
[production plan](.agent/plans/production-deployment.md).
[ADR 0001](docs/adr/0001-managed-deployment.md) selects Render: the earlier design
chose a VM and contained no Render/Railway decision, so the hosting target is
explicitly superseded rather than presented as an existing decision.

- Added [Vercel configuration](frontend/vercel.json), a manual-deploy
  [Render Blueprint](render.yaml), a production
  [backend image](deploy/backend.Dockerfile) with reviewed catalogue content,
  backend/frontend environment examples and
  [restricted runtime grants](deploy/runtime-grants.sql). Render assigns `PORT`;
  the new typed entry point binds it as a non-root process without trusting
  arbitrary proxy headers. The root frontend-oriented Docker ignore rules remain
  intact; a production-Dockerfile-specific allowlist keeps environments, tests,
  caches and unrelated files out of this backend context.
- Public release profile enforces **`PUBLIC_DEMO_ONLY=true`**, **`AI_PROVIDER=mock`**
  and **`AUTH_ENABLED=false`**. No OpenAI, Ollama or Clerk key is needed. A separate
  later account-enabled profile can select optional providers. Real feedback and
  simulated history retain their existing provenance/validation distinctions.
- Added an authenticated frontend gateway: Vercel's sanitized client-IP metadata
  is forwarded with a server-only credential, supplied gateway fields are
  replaced, and the API rejects direct/forged calls before body processing.
  Existing ownership, CSRF and bearer checks remain. Native development ignores
  browser-supplied forwarding addresses. CORS permits exact HTTPS origins only;
  frontend Clerk authorized parties use only the configured canonical origin in
  Vercel production, preserving local development aliases.
- Production database access requires verified certificate/hostname TLS. Neon
  examples use direct asyncpg URLs with explicit SSL context configuration,
  avoiding incompatible libpq URL parameters and PgBouncer assumptions. Production
  pools are bounded to three plus two connections per process; development/test
  pool sizes and command timeouts are preserved. No schema or API DTO changes.
- Migrations and idempotent question publication remain explicit owner-role
  commands; only the restricted DB credential belongs on Render. API health is
  the existing schema-aware readiness endpoint. Hourly cleanup uses that runtime
  role. No automatic startup migrations, shared demo login or destructive seed.
- The runbook covers Neon creation/roles, exact migration/publication/grant
  commands, backend/frontend deployment, frozen pnpm/Corepack setup, complete
  environment tables, canonical CORS/cookies, secrets, preview isolation,
  callbacks, demo setup, optional local Ollama and optional OpenAI later. It
  distinguishes free service accounts from hosting charges and AI API keys.
  The prepared Render API/cron use paid compute; this is a no-paid-AI deployment,
  not a promise of free hosting. Existing local `.env` and application data were
  preserved, along with all preceding UI and cleanup work.

### Verification — Production deployment preparation (preceding phase)

- Local production-mode check passed with **no AI credentials**, using an owned
  TLS PostgreSQL container, the non-root production API image, a restricted login,
  and HTTPS frontend/backend gateways. It applied head `0010_security_budgets`,
  checked schema drift, published **29 versions**, reran publication with **zero
  new versions**, and verified DB TLS, no runtime DDL/schema-version writes,
  actual same-origin secure cookies/CSRF, exact CORS, header spoof rejection,
  two isolated visitors, creation quotas, mock-provider metadata and expiry cleanup.
  Cleanup physically removed the expired principal while retaining the other demo.
  Generated test credentials were absent from browser JS and response headers.
- Frontend zero-warning lint, strict typecheck and **147 tests across 17 files**
  passed, including **13 new gateway/production-configuration cases**. Production
  Next.js builds passed under both production-profile and ordinary browser-test
  configuration. **25 Playwright tests** passed with the full persisted candidate
  journey and desktop/mobile accessibility checks. No checks were weakened.
  The final native production build restores the ordinary localhost API target;
  the existing running Compose application was not changed.
- Render and Vercel manifests passed their publicly documented JSON schemas.
  Repository formatting, local runbook links and `git diff --check` passed.
- Full backend gate passed: **551 tests in 496.11 seconds**, including **29 new
  deployment cases**; Ruff lint/format (**191 files**), strict mypy (**180 source
  files**), disposable migration downgrade/re-upgrade, schema drift, OpenAPI and
  legacy preservation all passed. No application database was downgraded or reset.

### Limits and next task — Production deployment preparation (preceding phase)

No Vercel/Render/Neon/Clerk account, project, DNS entry, callback or hosted database
was created or changed. No push, deployment, paid inference, external repository
import or application-data migration occurred. Local TLS ingress models Vercel's
documented metadata contract; it is not hosted-platform verification. Real network
quotas/cookies, cold starts, provider certificates, plan limits, backups/restore
and optional Clerk/OAuth still need the runbook's release smoke after explicit
authorization. Account data remains disabled in the public profile until the
documented privacy/lifecycle release requirements are met. Next: review the
prepared configuration and authorize a separate deployment only when ready.

## Product quality and accessibility review (preceding phase)

Reviewed all fourteen requested product areas using the
[product quality plan](.agent/plans/product-quality-review.md). Demo/Dashboard
and Profile/Settings share routes, producing twelve distinct public/demo screens.
The [page-by-page review](docs/PRODUCT_QUALITY_REVIEW.md) records findings,
changes, accessibility evidence and limitations. Existing cleanup, test and
changelog work from the preceding startup phase was preserved.

- Inspected the running app in Chrome at **1280 × 900, 375 × 812 and 320 × 812**.
  Retained before/after captures and machine-readable results in ignored
  `.cache/product-review-before/` and `.cache/product-review-after/`. The after
  pass covered **36 page scans**, with **no document overflow or axe violations**;
  six additional repository-analysis/defense scans also passed. Wide semantic
  tables intentionally retain contained horizontal scrolling.
- Replaced generic landing/dashboard slogans and stale feature-availability
  claims with concrete capabilities and next actions. Removed repeated advice,
  decorative icons and oversized empty-state spacing. Flattened excess task,
  evidence, history and review cards while keeping the established visual system.
- Fixed unstyled interview controls/answer input, the squeezed mobile search and
  repository URL fields, **15px of ZIP-picker overflow at 320px**, table row-header
  styling and the stray final-row border. Mobile filters now expose their state
  and applied count, preserve selections and work with Enter/Space. Pagination
  wraps, checkbox labels provide larger targets, and control typography is
  consistent. Source/evidence policy detail remains available in disclosures.
- Input-boundary contrast against white improved from **1.83:1 to 3.58:1**.
  Project Defense practice has an H1 and receives focus when opened; its primary
  action is distinct from secondary controls. Loading includes visible status
  text. Consistent project alerts retain actionable messages and local drafts.
  Corrected a written-answer hint that always claimed mock feedback, and an
  undefined interview feedback-background class. No fabricated metrics, outcomes
  or testimonials were added; simulation/provenance/privacy notices remain.
- The production build exposed a security stop for Next.js **16.4.0**. Verified
  the official 14 October advisory and registry audit, then patched Next.js and
  its matching ESLint configuration to **16.4.1**. Only their resolved packages
  changed; no new library was added. Production audit then reported **zero known
  advisories**, compared with one critical and one high advisory before the fix.

### Verification — Product quality and accessibility review (preceding phase)

- Frontend zero-warning **lint**, strict **typecheck**, all **134 component
  tests across 15 files**, and the **production build** passed. Repository
  Prettier and `git diff --check` passed. The initial sandbox build worker
  failure was rerun with process access; the subsequent security stop was
  resolved by the patch.
- **25 Playwright tests across four specs passed**, including two new keyboard/
  mobile-filter/reduced-motion regressions, all workspace screens at desktop,
  375px and 320px, and actual account-form component fixtures at the same sizes.
  The real candidate journey still covers filters, saved assessments, mock
  interviews, repository analysis/defense, roadmap changes, persisted progress,
  ownership isolation and demo erasure. No assertions or gates were weakened.
- Checked keyboard navigation/skip links, route and invalid-field focus, dialog
  focus containment/Escape/return, labels and accessible names, heading/table
  semantics, text/control contrast, alerts/retry and reduced motion. Final axe
  A/AA scans reported zero violations; this is not a full conformance claim.
- Built the Linux frontend image and refreshed only the local frontend service.
  The app remains at **<http://localhost:3000**>. Readiness and same-origin
  HTTP/API/ PostgreSQL smoke passed. Browser runners removed their temporary
  servers and disposable databases; the application database and other services
  were retained.

### Limits and next task — Product quality and accessibility review (preceding phase)

Live Clerk sign-in is unconfigured. Account forms were inspected as labelled
static fixtures and tested with authenticated-client component mocks, not a real
account session. No manual screen-reader audio session, physical mobile device,
real AI provider or external repository import was tested. Backend logic, APIs,
migrations and ownership rules were unchanged; the full backend suite was not
rerun. All edits remain uncommitted; no push or public deployment occurred.
Next: verify the configured account journey with a real Clerk development
instance and conduct a manual screen-reader/device pass before public release.

## Local application startup (preceding phase)

The user authorized running the documented local setup. Docker Desktop was already
running with older containers; the existing ignored `.env` was preserved. Built
and started the current Compose services, applied migrations through
`0010_security_budgets` to the configured application database and explicitly
published **29 new reviewed catalogue versions**. The existing PostgreSQL volume
was retained. The website is running at `http://localhost:3000`; the demo was
opened in the default browser. Services are intentionally left running for use.

- Startup exposed an existing cleanup crash: the standalone maintenance process
  imported only part of the ORM graph, so mapper configuration could not resolve
  referenced interview/project tables. API/test initialization had already loaded
  these models, masking the separate entry-point failure.
- Fixed [cleanup startup](backend/src/interview_prep/cleanup.py) to import and
  configure the complete explicit model registry before database work. Added a
  [fresh-interpreter regression](backend/tests/test_cleanup.py) independent of
  pytest's preloaded models; it failed before the fix and passed afterward.
- Rebuilt the cleanup image, completed a real one-shot maintenance invocation
  successfully and restarted the hourly loop. Expiry cleanup remains its intended
  behavior; no volume reset, downgrade or manual deletion of candidate data.
- **8 focused tests passed** (new cleanup regression plus isolation tests). Backend
  lint, format (**186 files**) and strict mypy (**175 source files**) passed.
  No frontend, dependency, schema or API contract change was required.
- Compose startup/readiness, migration-head inspection and the HTTP smoke passed:
  frontend, API liveness, PostgreSQL/schema and same-origin forwarding. Landing,
  demo and service-status pages returned HTTP 200. A real headless browser clicked
  **Verify connection**, confirmed API/PostgreSQL connectivity and revision 0010,
  and verified the demo entry. An initial shell-pipe encoding mismatch in the
  temporary assertion was corrected with a Unicode escape; the unchanged UI's
  full connection text then passed. No paid provider call was made.

The full automated suite was not rerun for this small startup fix. Code/test/status
changes remain uncommitted; this request authorized local execution, not a new
commit/push or public deployment. Next: use the local demo, then review the startup
fix for a later commit. Earlier deployment/privacy limitations remain in effect.

## Engineering portfolio presentation (preceding phase)

Implemented the [portfolio presentation plan](.agent/plans/portfolio-presentation.md)
after checking the actual routes, policy engines, models, provider wiring, workers,
UI, migrations, setup/verification scripts and clean Git baseline `59e3507`.
That preceding quality-pipeline commit has been pushed to `rebuild/professional-v2`.

- Rewrote [README.md](README.md) with the problem/motivation, recruiter journey,
  feature boundaries, current architecture/Mermaid diagram, algorithms, Project
  Defense, zero-key/provider behavior, stack/schema/API, environment/setup,
  Docker/migrations/deployment, testing, privacy, limitations and next work.
  The hosted-demo URL is explicitly unconfigured, with replacement/configuration
  instructions; no unverified badge, adoption/performance claim or testimonial.
- Added [current architecture](docs/ARCHITECTURE.md), separate from the historical
  V2 proposal, and source-linked implementation maps in every requested domain
  guide. Corrected stale claims that interview selection/creation were future
  work, old readiness/table counts and outdated HTTP decompression language.
  The current registry has 52 application tables; readiness head is
  `0010_security_budgets`; catalogue dry-run validates 29 authored prompts.
- Added [interview notes](docs/INTERVIEW_NOTES.md) with short/extended explanations,
  architecture/data/security/concurrency/cost/failure/scaling discussion and
  **34 implementation-backed interviewer questions and answers**. Added
  [resume bullet options](docs/RESUME_BULLETS.md), contribution caveats and an
  inspectable evidence map. Quantified test bullets cite the dated prior run,
  without claiming all tests were authored in one change or by one person.
- Published four visually inspected original browser screenshots: landing,
  Skill Matrix, saved objective assessment and mock interview review. They were
  copied unchanged from the retained successful 22 October quality-run artifacts;
  [provenance/reproduction](docs/screenshots/README.md) distinguishes live demo
  screens from the public interface preview. No new capture or hosted deployment
  is claimed; fictional-data and simulation disclosures remain visible.
- Preserved the ranked security audit and its open production/privacy requirements.
  Clarified that only answer evaluation/follow-ups use optional remote providers;
  local source/evidence/planning workflows do not use the other interface methods.
  Updated the changelog and related development/data-model entry points. No
  application behavior, schema, API contract, dependency or CI changes were made.

### Verification for this documentation phase

- **101 focused pytest cases passed** across `test_adaptive.py`,
  `test_skill_engine.py`, `test_evaluation_rubric.py` and `test_planning_rules.py`.
  These existing pure-policy/schema tests required no database/provider service.
- Backend `--phase lint` passed: Ruff lint, format check (185 files), strict mypy
  (174 source files). Whole-repository Prettier and `git diff --check` passed.
- Local link/anchor validation passed across all 55 repository Markdown files.
  All four published PNGs are byte-identical to their original retained artifacts
  and have the documented 1280-pixel width; they were also visually inspected.
- The README's frozen `uv sync --project backend --frozen` and
  `pnpm install --frozen-lockfile` passed. This shell needed the installed uv
  executable added to PATH; sandbox cache/editable-package access required reviewed
  permissions. An initial sandbox/offline sync failed and the regular frozen
  sync restored the editable package successfully; no lockfile changed.
- Initializer preserved the existing ignored `.env`; Compose configuration passed
  with `--quiet` without exposing values. Check runners' CLI flags, Uvicorn entry
  point/help, Alembic head/history and catalogue validation (`writes: false`)
  passed. OpenAPI and legacy preservation checks passed; TypeScript contract
  regeneration was byte-identical. Playwright discovery found 23 tests in four
  specs; discovery is not a new browser execution.

### Limits and next task — Engineering portfolio presentation (preceding phase)

Docker Desktop was stopped and left stopped. This documentation phase did not
start/migrate/seed the application database, launch the full Compose/native stack,
or rerun the full backend/frontend/browser/container suite. The prior complete
521/134/23 test run and builds below remain dated evidence, not fresh results.
No live Clerk, AI, public GitHub import, hosted CI or public deployment was verified.
Portfolio changes are prepared for the subsequently authorized commit/push to
`rebuild/professional-v2`; deployment is outside this request. Next: observe the
hosted checks, address the documented release gaps and configure a verified HTTPS
demo URL when deployment is explicitly authorized.

## Full-stack automated quality pipeline (preceding phase)

Implemented the [quality pipeline plan](.agent/plans/full-stack-quality.md).
[TESTING.md](docs/TESTING.md) maps the existing backend/component suites to the
requested domains and documents the real, intercepted and static browser checks.

- `pnpm check` runs the complete sequential backend/frontend/build/browser pipeline.
  Focused backend phases expose lint/types, pytest and migration validation as
  separate CI steps. The browser runner now owns both servers, a fresh database,
  migrations and catalogue seeding; it checks the compiled API rewrite and cleans
  up only resources it created. Alternate ports preserve normal running services.
- Pytest forbids real HTTP before collection, component tests reject unstubbed
  fetch, and browsers block external origins. Runners replace inherited provider
  and Clerk settings with mock/disabled configuration. Provider protocol tests
  use in-memory HTTP and dummy credentials. CI receives no repository secrets.
- GitHub Actions separates backend, frontend and browser gates, with real
  PostgreSQL, frozen dependencies and pinned actions. Browser checks consume the
  exact production build artifact. JUnit reports and bounded failure artifacts
  provide diagnostics. Container packaging remains a build-only gate.
- Browser steps cover the demo candidate journey through target/resume context,
  question filters, saved assessments, mock interviews, local repository analysis,
  Project Defense, generated roadmaps/history and persisted progress. Two visitors
  check ownership and erasure without bypassing creation quotas. Account form
  layout/axe fixtures now render directly, independent of Vitest output files.
- New regressions cover test isolation and connectivity failures, demo lifecycle,
  repository loading/retry/empty states and interview revision races. A live
  browser failure exposed worker claim/completion advancing revisions twice;
  guarded UI retries now allow three total attempts and still refuse any changed
  candidate state. Repository-list failures no longer masquerade as an empty list.
- Added contribution guidance, root security policy, changelog, PR/issue templates
  and expanded weekly Dependabot coverage to Compose images as well as the existing
  package/lockfile, Dockerfile and action ecosystems. No application dependencies,
  schema migrations or API contracts were added.

### Verification — Full-stack automated quality pipeline (preceding phase)

- A single complete `scripts/check_all.py --api-port 18101 --frontend-port 13101`
  run passed against real disposable PostgreSQL databases on Windows, using the
  locked backend virtualenv and installed Chrome (`E2E_BROWSER_CHANNEL=chrome`).
- Backend: **521 passed in 480.56 seconds**, including **11 new isolation/smoke
  cases**. Ruff lint/format (**185 files**), strict mypy (**174 source files**),
  populated migration guards, full downgrade/re-upgrade, schema drift, OpenAPI
  and legacy preservation passed. Separate CI `--phase lint` and
  `--phase migrations` invocations also passed. No pytest warnings or skipped
  cases. The CA trust test retains its original trust-store assertions and now
  reads OpenSSL-decoded subjects without the previous cryptography warning.
- Frontend: **134 tests across 15 files passed**, including **11 new cases** for
  demo lifecycle, truthful repository states, worker-only revision retries,
  retry bounds and cross-tab draft/state protection. Zero-warning ESLint,
  strict TypeScript, generated-contract consistency, repository Prettier and
  the production build passed. JUnit reports record zero failures/errors.
- Playwright: **23 passed across four specs**, with all eight live candidate
  journey steps, same-origin API/database smoke, desktop/mobile form axe checks,
  focus/navigation and intercepted recovery states. The final full run passed
  without retries or skipped tests. Earlier failures led to the two UI fixes
  and corrected stale smoke/schema/feedback expectations, accessible selectors
  and response barriers; assertions were retained rather than bypassed.
- `docker compose build` passed for backend, cleanup, migration and frontend
  images, including the Linux production frontend build. Images were built
  without starting or deploying the updated application. Official actionlint
  **1.7.12** validated the workflow; its Linux CI binary is checksum-pinned.
  The production artifact packaging command also passed: **2,005 members**, with
  server, static CSS and rewrite manifest present and **no environment files**.
- Scoped credential scan found **zero matches** in **404 working files, 585
  reachable historical blobs, 24 browser assets and 28 local logs**, checking
  two current local secrets without printing them. UTF-16 PowerShell logs were
  decoded for scanning. Scope/pattern limitations still apply.
- The runners stopped their owned servers and removed their disposable databases.
  The application database was not migrated, seeded or truncated by these checks.
  Docker Desktop was stopped afterward, restoring its original state.

### Limits and next task — Full-stack automated quality pipeline (preceding phase)

- Live browser verification uses a disposable database and mock AI. Real Clerk
  sign-in and authenticated account browser flows remain separate integration
  checks; static account previews do not claim interactive login coverage.
- Hosted GitHub Actions results and branch protection cannot be established by
  local runs. Scheduled Dependabot configuration must reach the default branch
  (`main`) to activate there. Private security reporting is a repository setting.
- Commit scope: `test: add full-stack automated quality pipeline`. No push or
  deployment is requested for this phase. Next: review/push when authorized, then
  observe hosted checks and configure the documented repository settings. Existing security release limitations remain in
  [SECURITY.md](docs/SECURITY.md).

## Application security and privacy review (preceding phase)

Implemented the [security review plan](.agent/plans/security-review.md).
[SECURITY.md](docs/SECURITY.md) ranks findings from Critical to Informational,
records the actual trust boundaries and deletion/retention behavior, and separates
verified fixes from remaining production requirements. Prior uncommitted
evaluation, Project Defense and roadmap work is preserved.

- Fixed **one Critical dependency finding**: certifi 2026.7.22 trusted the root
  affected by GHSA-6q48-6c7w-9gw2 / PYSEC-2026-4320. Updated only certifi to
  **2026.10.19** and added a regression against HTTPX's actual CA trust store.
  Exploitation requires compromised intermediate keys and network interception;
  this review found no evidence of an actual compromise. Existing images need
  rebuilding to consume the patched lockfile. No dependencies were added.
- Fixed **two High application findings**: request bodies are now bounded before
  JSON parsing by byte/time/concurrency limits; paid assessment work has durable
  validated-result receipts, bounded retries and shared principal/global budgets.
  Rollback no longer loses earlier successful paid feedback. Failed or deleted
  imports still consume shared hourly budgets. Quota/database failure prevents
  dispatch; simulations remain local and do not consume provider budgets.
- Fixed exception-message exposure to server logs, automatic HTTP decompression
  before response limits, slow-drip JWKS discovery, misleading privacy/settings
  copy, normalized dot-only repository names and Compose ignoring APP_ENV. Added
  a baseline CSP, isolated PDF worker imports/cwd and hostile provider-output
  rendering coverage. Source code and archive members are never executed.
- Migration **0010_security_budgets** adds pseudonymous quota counters and owned
  evaluation receipts without rewriting candidate data. Receipts expire after
  48 hours; counters expire at the hour/day boundary; hourly cleanup removes
  expired rows. Principal deletion cascades receipts. Downgrade refuses live
  quota/receipt rows so rollback cannot silently refund budgets or lose retry
  state. API readiness now requires this revision.

### Verification — Application security and privacy review (preceding phase)

- Final full backend harness: **510 passed in 430.32 seconds**, including **21
  new security regression cases**. One cryptography deprecation warning arose
  while inspecting a legacy CA's nonpositive serial number; no warning filter
  or assertion was suppressed. Ruff lint/format (**181 files**), strict mypy
  (**170 source files**), fresh migrations, populated downgrade refusals, full
  downgrade/re-upgrade, schema drift, OpenAPI consistency and legacy preservation
  all passed. The application database was not used for these checks.
- Frontend: **123 tests across 14 files passed**, including the new malicious
  generated-content rendering case. Zero-warning ESLint, strict TypeScript and
  the production Next.js build passed. The test run used two workers; initial
  frontend/backend overlap caused resource-contention timeouts, and both suites
  were rerun separately without changing assertions, test timeouts or rules.
- Live production npm audit: **121 dependencies including optional packages,
  zero advisories**. Live post-fix OSV scan: **43 locked PyPI packages, zero
  advisories**. Earlier network/approval failures were resolved. These checks do
  not cover base-image/OS packages, archived V1 dependencies or unknown issues.
- Whole-repository Prettier and `git diff --check` passed. An HTTP smoke check
  against the built frontend verified the privacy page, retention disclosure,
  CSP, nosniff and frame denial; its temporary process was stopped. Compose
  environment resolution honored development and production APP_ENV overrides.
- Scoped post-build credential scan: **383 working files, 585 reachable history
  blobs, 24 browser assets, 22 local logs and two current local secret values;
  zero matches**. This checks named patterns and exact local values without
  printing credentials; it is not a guarantee for every credential format or
  remote/unreachable history. The report describes the excluded locations.
- Docker Desktop was stopped after verification, restoring its original state.
  Automatic approval review initially blocked that cleanup because of a usage
  limit; the resumed cleanup completed successfully on 22 October.
- Tests use disposable PostgreSQL databases and mocked external integrations.
  No live AI, Clerk, GitHub or browser E2E was exercised. The application database
  was not migrated or seeded. No push or deployment was performed.

### Remaining requirements and next task

- Roll out migration **0010** and rebuild backend images before using the updated
  application; configure the shared quota key/settings and hourly cleanup. No
  confirmed Critical/High finding remains unfixed in this working tree. Provider
  ceilings count attempted calls, not currency; configure provider spend limits.
- Production still requires full account erasure/export and identity lifecycle
  reconciliation, a restricted parser OS sandbox, public-ingress limits/TLS,
  separated migration/runtime database roles and documented backup/log retention.
  Existing granular and demo deletion are tested; deleting a profile does not
  erase account practice history or third-party data. These are explicit release
  limitations, not claims of complete privacy compliance or sandboxing.
- Next: operator rollout and live authentication/browser verification in the
  intended environment, then close the documented production release gaps.

## Personalized roadmap and persisted progress analytics (preceding phase)

Implemented the [roadmap/progress plan](.agent/plans/personalized-roadmap-progress.md).
[ROADMAP_PROGRESS.md](docs/ROADMAP_PROGRESS.md) documents recommendation rules,
scheduling, preservation, aggregation denominators, provenance and coverage limits.

- Account/demo roadmaps use the selected owned target and priority, reviewed job
  requirements versus lexical mentions, resume/profile context, assessment and
  interview evidence, latest Project Defense statuses, explicit weekly time and
  an optional interview date. All recommendation/aggregation logic is deterministic;
  no AI provider is called and no readiness or hiring-company claim is calculated.
- Versioned `personal-roadmap-v1` tasks expose topic, rationale, ordinal priority,
  objective, estimated effort, recommended activity, planned week and status.
  Existing skill-evidence rules guide practice/validation/maintenance. Unscored
  defense answers suggest explanation review without inventing performance grades.
- Generate/regenerate, complete/reopen and rationale/history views are implemented.
  Regeneration archives the prior version without deleting its tasks or completion
  events. Stable evidence/activity keys omit completed work; fresh source identities
  can justify new activity on the same topic. Reopening retains previous events,
  and recompletion appends a new one. Revisions, idempotent generation keys,
  ownership, principal locks, CSRF and immutable metadata guards protect writes.
- Weekly scheduling respects the entered budget and queues work outside estimated
  capacity before an interview date. Starts use the saved timezone (UTC without a
  profile), resolved through PostgreSQL timezone data for Windows portability.
  Estimates are editorial weekly buckets, not calendar appointments or speed claims.
- `progress-analytics-v1` reads real persisted records: completed objective
  assessment accuracy/category counts, newest interview rubric rating series,
  current/historical roadmap completion, repeated concept misses, recent sessions,
  validated strengths in tested scope and areas requiring further validation.
  Latest failed evaluations cannot resurrect older ratings. Null/ungraded is
  distinct from zero; simulations never validate skills or create missed-concept
  claims. Model suggestions and objective misses remain separately labelled.
- Charts require three comparable sessions on three distinct UTC dates; assessment
  charts also require one grading policy. Interview series partition by kind,
  provider/model/version, rubric, profile and assessed dimensions. Sparse histories
  use tables/empty explanations. Accessible loading/error/retry states and privacy /
  landing-page disclosures are updated. No new dependencies were added.
- Migration `0009_personal_roadmaps` adds nullable bounded snapshot/recommendation
  JSON and generation identity, preserving old tasks without invented rationale.
  Populated downgrade refuses data loss. Old demo task completion delegates to the
  same revision-aware service. Prior Project Defense and evaluation work is kept.

### Verification — Personalized roadmap and persisted progress analytics (preceding phase)

- Full backend run: **488 passed, 1 failed**. That new regression case failed
  because its test session expired ORM records after commit; its fixture now uses
  the application's `expire_on_commit=False` setting. Final focused verification
  passed **23 tests, 466 deselected**, including that corrected case and all new
  planning/aggregation cases. All **489 tests** passed across these runs; this is
  not a single clean full 489-test run. This phase adds **18 backend cases**.
- Final disposable harness passed Ruff lint/format (**174 files**), strict mypy
  (**164 files**), upgrades, schema drift checks, full downgrade/re-upgrade,
  populated downgrade refusal, OpenAPI consistency and legacy hashes/seeds.
- Frontend full run: **122 tests across 14 files**, including **10 new cases**.
  Final focused run: **10 passed** after the form-selection correction. Zero-warning
  ESLint, strict TypeScript and the production build passed. Tests cover rationale,
  completion/reopen, preserved history, request failures, null versus zero, sparse
  chart suppression, sufficient history and authenticated/demo API contracts.
- Whole-repository Prettier and `git diff --check` passed. Docker Desktop was
  stopped after verification, restoring its original state.
- Tests use disposable databases; the application database was not migrated or
  seeded. No live AI, Clerk integration or browser E2E was exercised. No test,
  lint rule, type check or database guard was weakened. No commit, push or
  deployment was performed.

### Limits and next task — Personalized roadmap and persisted progress analytics (preceding phase)

- Apply `0009_personal_roadmaps` (and preceding migrations) before starting the
  updated API. Next: operator rollout and a browser smoke check in the intended
  environment. Existing source windows and validation limits remain explicit.
- Plans retain at most 50 generated versions per principal, with 12 tasks per
  generation. Account history has no automatic expiry or individual generation
  deletion. Demo expiry/deletion removes owned records. Historical rationale/source
  identifiers remain saved even if source evidence is later removed.
- Scheduling is greedy and can leave unused time. Missing/unscored/partial data
  creates validation activities, never fabricated weaknesses or readiness scores.
  Numeric trends are descriptive observations with disclosed sample sizes and
  provenance, not calibrated competence or predictions.

## Project Defense Mode (preceding phase)

Implemented the [Project Defense plan](.agent/plans/project-defense.md).
[PROJECT_DEFENSE.md](docs/PROJECT_DEFENSE.md) documents the workflow, extraction
coverage, security boundaries, limits, retention, API and migration recovery.

- Public GitHub URL and raw ZIP import, plus a labelled offline teaching fixture,
  work in account and recruiter demo workspaces. All use the same deterministic
  `project-static-v1` analyzer; no LLM, repository execution or new dependency is
  required. GitHub snapshots pin the default-branch commit and persist provenance.
- Static facts cover languages, manifests, dependencies/frameworks, probable
  frontend/backend components, database/auth clues, route/model declarations,
  tests, CI, Docker and documentation. Architecture/technology views distinguish
  observed declarations from inference and cite file paths/lines. File lists
  preserve archive-relative directory structure and disclose omissions/truncation.
- Imports use fixed GitHub hosts without redirects, tokens or inherited proxies;
  bounded downloads/uploads; ZIP path/link/duplicate/bomb checks; and a trusted
  isolated Python worker with memory/time/concurrency bounds. Archives are never
  extracted and source bodies are never retained. This is not a complete OS
  sandbox or comprehensive secret scanner; those limits are explicit in the docs.
- `project-prompts-v1` generates ten private draft questions about architecture,
  framework choice, auth, persistence, scaling, security, tests, dependencies,
  AI-assisted ownership and reflection. Drafts never become reviewed curriculum.
  Optional AI enrichment is not enabled. Defense practice is explicitly unscored.
- Saved defense sessions support draft/submit/skip/pause/resume/end, durable history,
  revision conflict protection and recovery of local drafts. Server-side ownership,
  composite foreign keys, principal locks, quotas and database guards protect
  isolation and terminal answers. Failed imports/saves do not overwrite saved work.
- Migration `0008_project_defense` adds nullable snapshot metadata and owned
  run/answer tables without rewriting existing records. Populated downgrade is
  refused. Snapshot deletion removes generated questions and defense history.
  Demo data expires with its workspace; account snapshots have no automatic expiry.
- Updated account/demo navigation wiring, generated API contracts, landing-page and
  privacy disclosures. Preserved the preceding structured-evaluation work.

### Verification — Project Defense Mode (preceding phase)

- Full backend regression: **469 passed**. Final focused run: **39 passed,
  432 deselected**, including two additional cases and the final path/order edits.
  All **471 backend tests** passed across these runs (not one full 471-test run).
  This phase adds **36 backend cases** covering archive/network boundaries,
  extraction, ownership, quotas, replay/revisions, durable answers, demo CSRF,
  deletion and refusal of a lossy migration rollback.
- Ruff lint/format passed for **161 files**; strict mypy passed for **152 files**.
  Disposable database upgrade, drift check, full downgrade/re-upgrade, OpenAPI
  consistency and legacy source hashes/seeds passed in both final harness runs.
- Frontend: **112 tests across 13 files** (7 new cases), zero-warning ESLint,
  strict TypeScript and production build passed. Tests include truthful evidence
  labels, demo import, durable pause, failed-save preservation and stale-tab draft
  recovery. No tests or type checks were weakened.
- Application database migration/seeding, live GitHub requests, live AI providers,
  Clerk integration and browser E2E were not run. GitHub boundary tests use mocked
  HTTP; parser tests execute the real isolated worker. Test databases were removed
  by the harness. No commit, push or deployment was performed.
- Whole-repository Prettier and `git diff --check` passed. Docker Desktop was
  stopped after verification, restoring its original state.

### Limits and next task — Project Defense Mode (preceding phase)

- Apply `0008_project_defense` before running the updated API; the application
  database remains unchanged. Next: operator rollout and a browser/live-public-
  GitHub smoke check in the intended environment, with gateway request/rate limits.
- Static heuristics are deliberately partial and do not establish runtime behavior,
  security, authorship or competence. GitHub unauthenticated rate limits and large
  archives/metadata can require ZIP import. Per-process concurrency is not a
  distributed rate limiter. Source paths/declarations can still contain sensitive
  information despite filename exclusions.

## Structured, versioned answer evaluation (preceding phase)

Implemented following the [evaluation plan](.agent/plans/answer-evaluation.md).
[Evaluation rubric](docs/EVALUATION_RUBRIC.md) documents every criterion, exact
score meanings, aggregation, simulation behavior, storage and compatibility.

- New `answer-rubric-v1` evaluations include overall feedback, strengths,
  improvements, missing concepts, recommended answer structure, a potential
  follow-up and explained criterion results. General criteria always apply;
  technical and behavioral profiles add the requested specialized criteria.
  Profiles come from authored question types, not answer instructions.
- Model judgments use anchored 0–4 scores and a rounded-down mean of assessed
  criteria. Null means not assessed/not applicable, with a required reason.
  `MockAIProvider` (`mock-structured-v2`) remains deterministic: only lexical
  completeness coverage receives a proxy score; correctness, STAR, ownership
  and other semantic criteria remain explicitly unassessed. No fake ML or
  competence/readiness claims were introduced.
- Structured contracts enforce versions, complete ordered profiles, score bounds,
  aggregate consistency, concept membership/complements, explanations, provider
  scoring basis and payload byte bounds before persistence. Dedicated prompt
  version is `answer-evaluation-v2`; existing untrusted-input boundaries remain.
- Assessment metadata and interview result JSON persist the evaluation, rubric,
  provider/version, configured model and completion timestamp. The authored
  question rubric version stays separate. Existing JSON columns suffice: no
  migration, backfill, dependency or rewrite of historical evaluations.
- Shared accessible feedback UI renders coaching, criterion explanations, score
  meanings and provenance in both reviews. API/client contracts and runtime
  parsers are updated; old records remain readable without invented breakdowns.
- Interviews retain their committed submitted answer on provider failure;
  assessments retain their committed draft and revision when grading rolls back.
  Existing ownership, demo isolation, fencing/retry and evidence exclusions remain.

### Verification — Structured, versioned answer evaluation (preceding phase)

- Full backend regression: **432 passed**. Final focused verification passed
  **166 tests, 269 deselected**, including the additional adapter validation and
  three added cases. All **435 tests** passed across these runs; this is not a
  single full 435-test run. Added **37 backend cases** in this phase.
- Ruff lint/format passed for **147 files**; strict mypy passed for **139 files**.
  Disposable database upgrade, drift check, full downgrade/re-upgrade, OpenAPI
  drift and legacy source hashes/seeds passed in the full harness.
- Frontend final verification: **105 tests across 12 files** (15 added cases),
  zero-warning ESLint, strict TypeScript and production build passed.
- Whole-repository Prettier and `git diff --check` passed. Windows sandbox
  restrictions on Docker startup and Vite child processes were resolved through
  reviewed local execution; no check or test was weakened.
- Verification uses disposable PostgreSQL databases; the application database
  was not migrated or seeded. The harness removed its test databases and Docker
  Desktop was stopped afterward, restoring its original state. Live
  OpenAI/Ollama, Clerk and browser E2E were not exercised. Schema/transport tests
  do not establish real-model scoring quality.

### Limits and next task — Structured, versioned answer evaluation (preceding phase)

- Historical results and generated follow-up answers are not regraded. Old
  in-progress interviews pin their original provider descriptor: the mock version
  change can produce `provider_changed`; answers remain saved and the session can
  finish with partial feedback. New sessions use the new version.
- The rubric is editorial and uncalibrated. Next: review representative technical
  and behavioral answers with humans before evaluating optional live providers.
  Broader reviewed question inventory remains separate work.
- No commit, push or deployment was performed.

## Complete mock interviews (preceding phase)

Implemented the approved [state-machine design](docs/MOCK_INTERVIEW_STATE_MACHINE.md),
following the [implementation plan](.agent/plans/mock-interview-implementation.md).
See [MOCK_INTERVIEWS.md](docs/MOCK_INTERVIEWS.md) for workflow, contracts, migration,
worker operation, sharing and recovery. The user's request authorizes a GitHub push
on `rebuild/professional-v2`, including the dependent adaptive/provider work that
was already present locally. Final verification results are recorded below.

- Complete account/demo configure, start, one-question play, typed autosave, submit,
  skip, contextual follow-up, pause/reload/resume, early end and final review.
  All seven types use actual published inventory; explicit difficulty is exact.
- Frozen owned adaptive context and candidate versions preserve selection and
  required role coverage. Main questions cannot repeat within a session. Sparse
  specialized coverage is disclosed. Simulation/model feedback never validates
  competence or raises adaptive difficulty.
- Answers commit with a command receipt and durable work row before AI dispatch.
  Short transactions, principal/session locks, revisions, unique keys and database
  guards prevent duplicate submission, reordered turns, reopened final answers
  and foreign ownership. Evaluation failure retains the answer and navigation.
- Two bounded worker loops recover queued/expired work using leases and fencing.
  Interrupted ambiguous dispatch is not automatically replayed. Finalization can
  complete with partial evaluation coverage; a current failed evaluation permits
  one explicit retry before close. Late cancelled follow-ups cannot insert turns.
- Follow-ups use AIProvider with the actual submitted parent/context, one slot per
  main, three per session and depth one. Mock authored probes are clearly simulated;
  children remain unscored because generated probes have no reviewed rubric.
- Migration `0007_mock_interviews` adds four owned workflow tables and compatible
  interview extensions. Legacy data remains readable, populated lossy downgrade
  refuses, and readiness/contracts now require the new revision. Dashboard/history
  hints are hidden during play; generated children are excluded before exposure
  counts. No existing migration is rewritten.
- Recruiter demo always pins mock, including when account AI config is remote or
  unavailable. Default remains `AI_PROVIDER=mock`; `INTERVIEW_WORKER_ENABLED=true`
  starts local database-backed work without Redis or external credentials.
  Privacy, development, data-model and architecture documentation are updated.

### Verification and delivery

- Added **22 PostgreSQL/API integration cases** for workflow, persistence, failure,
  type inventory, ordering, replay, concurrency, ownership, follow-up budgets,
  cancelled results, leases/retry, finalization deadline, demo CSRF/pinning and
  erasure, unavailable optional configuration and populated rollback refusal.
- Backend: the full regression run passed **396 tests**. Final focused verification
  passed **37 tests, 361 deselected**, including all 22 new interview cases and the
  last two added regressions. All 398 tests have passed across those runs; this is
  not a single full 398-test run. Ruff lint/format passed for 145 files and strict
  mypy passed for 137 source files.
- Clean upgrade, drift check, complete downgrade/re-upgrade, populated rollback
  refusal, generated OpenAPI/TypeScript and legacy hashes/seeds passed. Earlier
  context/question/resume migration tests retain their assertions with the new
  expected head. No test, time limit or database guard was weakened.
- Frontend: **90 tests across 11 files**, zero-warning ESLint, strict types and
  final production build passed. The normal backend build destination is restored.
- Browser: **23 Chrome checks passed**, including a live mock interview with
  save/pause/reload/resume, contextual follow-up, skip, completion and review;
  accessibility checks passed in tested views. Review screenshot visually inspected.
- Initial regression found older readiness/head assertions still pinned to 0006;
  they now expect 0007 while preserving mismatch, rollback and preservation checks.
  An expiry/finalization flush-order issue was fixed without weakening guards.
- Disposable databases and isolated localhost test services are used. The running
  application database has not been migrated, seeded or deployed by this phase.
  Live OpenAI/Ollama and live Clerk are not required or exercised.
- Whole-repository Prettier, `git diff --check` and quiet Compose validation passed.
  A credential-pattern scan of the 92 changed/new files found no matches; ignored
  environment files are excluded from delivery. Temporary API/frontend processes
  and disposable databases were removed; Docker Desktop was stopped afterward,
  restoring its original stopped state.

### Limits and next task — Complete mock interviews (preceding phase)

- The 23 typed catalogue prompts limit longer specialized interviews. Broader
  independently reviewed content remains needed; no automatic substitute questions.
- Timing is advisory and can include disconnected time unless explicitly paused.
  Unsaved browser-memory text is not recoverable after reload; acknowledged drafts
  are stored. Interaction expiry does not erase retained account history.
- Model output remains unverified; final review has no readiness score. Follow-up
  answers remain unscored. Individual interview deletion/export, voice/code execution
  and calibrated evaluation are outside this phase.
- Next: authorized rollout must apply 0007 and use compatible API/frontend builds;
  then expand reviewed curriculum and verify live account/provider configuration
  as needed. Git push does not deploy or migrate a running environment.

## Mock-interview state-machine design (preceding design phase)

Reviewed the existing interview models/SQL guards, assessment workflow, adaptive
selector, provider contracts, authored catalogue, identity/demo boundaries and
dashboard/history/evidence readers. The proposed design is documented in
[MOCK_INTERVIEW_STATE_MACHINE.md](docs/MOCK_INTERVIEW_STATE_MACHINE.md), following
the [design plan](.agent/plans/mock-interview-design.md).

- Specifies all seven requested interview types and target/type/difficulty/count
  configuration; exact difficulty filters and truthful runtime inventory limits.
  The manifests contain 23 typed-interview questions, including just one each for
  Frontend, System Design and Behavioral. Database publication was not inspected.
- Defines session, interactive-phase, answer and durable-work transitions for one
  question at a time, typed drafts, timing, skip/submit, pause/resume, follow-ups,
  full completion, early end, expiry and final review.
- Defines account/demo endpoint bodies/views, revisions and command receipts,
  owned transaction boundaries, proposed additive schema/guard changes, worker
  leases, crash recovery, bounded evaluation and late-result fencing.
- Proposes one follow-up slot per main, three per session and depth one. Follow-up
  answers remain unscored because generated probes have no reviewed rubric.
  Mock contextual presentation uses an exact parent/answer excerpt with explicitly
  simulated authored probes; no fake semantic understanding or competence claims.
- Calls out current integration gaps: no durable AI queue or live interview router,
  required private follow-up storage, aggregate provider scores versus authored
  dimension evidence, and dashboard feedback that must be hidden during play.
  Existing fictional sessions and prior adaptive/provider work must be preserved.

This phase changes documentation only. It does not add application code, endpoints,
database migrations, generated contracts, tests, dependencies or running services.
The document includes a future acceptance-test matrix; those tests are not yet
implemented or executed. Runtime test/build suites were not rerun for this design.
Verification: Prettier passed for all three changed documentation files;
`git diff --check` passed, and all nine source links in the design resolve.
Normal completion, early end, provider outage, replay, cancellation and expiry
were walked through against the proposed transitions; this is design review,
not runtime verification.

Next: implement the documented design only in a separately requested phase,
starting with migration/state-policy tests and owned commands, then durable work,
UI and end-to-end verification. Broader reviewed catalogue coverage is needed for
longer specialized interviews; no fallback should silently change their type.

## AI-provider architecture (preceding phase)

Implemented following the [AI-provider plan](.agent/plans/ai-providers.md) and
[architecture specification](docs/AI_ARCHITECTURE.md). `AI_PROVIDER=mock` is the
default; local development, tests, CI and recruiter demo need no AI credentials.
The preceding adaptive work is preserved. No new dependency, schema migration,
paid API call, model download, commit, push or deployment was performed.

- Shared typed asynchronous interface implements resume analysis, job-description
  analysis, answer evaluation, follow-up generation, roadmap recommendations and
  project questions. Bounded schemas and domain validation apply to every provider.
- Deterministic mock uses literal evidence and authored practice templates, with
  explicit simulation provenance. Existing lexical assessment scoring is preserved
  in one shared implementation. It does not claim validated competence or real AI.
- Optional Ollama uses a configured origin/model; optional OpenAI uses server-side
  Responses structured outputs. Missing optional configuration or unavailable
  servers fail safely on use; they do not prevent application startup or demo use.
  Recruiter demo remains pinned to mock even when an account provider is enabled.
- Fixed prompts are separate from business rules. Documents and answers remain
  untrusted user data. Outputs undergo schema, evidence-span, reference, repetition
  and budget validation before use. Providers have no tool-execution capability.
- Remote calls have bounded response sizes, total deadlines and narrow transient
  retries. Invalid output, refusals and ambiguous post-send timeouts are not retried.
  Safe errors omit upstream bodies and secrets; no silent simulated fallback.
- Credentials stay in backend configuration. Environment examples, Compose and CI
  default to mock with blank remote configuration. Account assessment setup and the
  privacy page disclose optional sharing before submission.
- Conceptual assessment evaluation uses the shared provider through a compatibility
  adapter. Validated metadata records configured model and prompt version; old
  records remain readable. Objective grading, ownership and evidence eligibility
  remain intact. OpenAPI and generated TypeScript contracts are updated.

### Verification — AI-provider architecture (preceding phase)

| Check                | Actual result                                                                                                                                                                                                                                                                           |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New AI tests         | **80 passed**: 79 provider/validation tests and one PostgreSQL/API integration test. Covers all six methods, mock determinism, schemas, domain constraints, unavailable providers, deadlines, retries, invalid configuration, injection-like text, demo isolation and saved provenance. |
| Backend regression   | Full run: **375 passed, one existing migration test timed out**. That test passed unchanged on a focused rerun (**1 passed, 375 deselected**). All 376 tests have passed across these runs; this was not a single clean full-suite run.                                                 |
| Backend gates        | Ruff lint/format passed for 134 files; strict mypy passed for 127 source files.                                                                                                                                                                                                         |
| Migrations/contracts | Disposable clean upgrade, drift check, complete downgrade/re-upgrade, OpenAPI contract check and original-source preservation checks passed on the focused harness run. No migration files changed.                                                                                     |
| Frontend             | Zero-warning ESLint, strict TypeScript, **81 tests across 10 files** with one worker, and production build passed.                                                                                                                                                                      |
| Configuration        | `docker compose config --quiet` passed without displaying resolved configuration or credentials.                                                                                                                                                                                        |

The broad backend run encountered an asyncpg timeout during the existing populated
migration preservation test. The unchanged focused rerun passed, including the
harness's remaining migration and contract checks. No test or timeout was weakened.
An automatic approval-review usage limit interrupted the earlier Compose check;
the resumed check succeeded. Disposable database verification did not migrate or
seed the application database. Verification databases were removed by the harness;
Docker Desktop was stopped afterward, restoring its original stopped state.
Whole-repository Prettier and `git diff --check` passed after the documentation update.

### Limitations and next task — AI-provider architecture (preceding phase)

- The other five provider operations are implemented and tested internal services;
  their owned user workflows and review screens are future work. Resume upload
  continues to use local extraction and does not automatically send documents to AI.
- Structured output and exact excerpts do not establish factual accuracy or defeat
  every prompt injection. Model-assisted and simulated results remain excluded from
  validated skill performance and adaptive difficulty evidence.
- Remote evaluation is sequential with a deadline per answer. A slow multi-answer
  submission can outlast the browser's existing 75-second wait; reload the saved
  attempt before retrying. Background processing/progress reporting is future work.
- Live Ollama/OpenAI, browser E2E and live Clerk were not exercised in this phase.
  No real-provider quality or model-compatibility claim is made by mocked transport
  tests. Next: connect additional operations to explicit owned review workflows and
  evaluate optional models using reviewed examples before relying on their advice.

## Explainable adaptive selection (preceding phase)

Implemented following the [adaptive plan](.agent/plans/adaptive-selection.md) and
[algorithm specification](docs/ADAPTIVE_ALGORITHM.md). New assessment starts use
`adaptive-v1`; existing attempts keep their frozen questions. No ML, external
provider, dependency installation, schema migration, commit, push or deployment.

- Pure typed selector with bounded inputs, reproducible seeded tie-breaking and
  per-choice score components/reasons. These are editorial scheduling heuristics,
  not competence probabilities or readiness predictions.
- Easy diagnostics without eligible history; per-skill starting levels from
  recorded difficulty. Two distinct successful concepts raise one level; two
  eligible failures lower one level, including repeated failure on one concept.
  Easy-floor failures favor a topic break. Missing/untrusted results are ignored.
- High-relevance weaknesses receive priority using existing owned job/skill
  evidence. Optional `target_id` is checked server-side. Resume claims, simulated
  evaluations, self-review and demo evidence cannot raise difficulty.
- Stable question IDs enforce five-exposure cooldowns across versions; concept
  spacing, two-topic streak limits and every-fourth exploration preserve diversity.
  Least-recent fallback discloses unavoidable repeats. Batches never duplicate a
  question or invent performance. Absolute exposure counts preserve exploration
  after the 1000-row history window fills.
- Assessment starts retain exact category/type/difficulty filters, ownership,
  principal locks and retry behavior. Frozen traces use existing configuration
  JSON and are returned as additive `selection` metadata. Old configurations remain
  readable/replayable. OpenAPI and generated TypeScript are updated.
- All private inputs are server-derived and bounded. Traces exclude response text,
  resume excerpts, keys and rubrics. Partial evidence disables performance
  adjustment. Existing assessment retention applies; no new external sharing.

### Verification — Explainable adaptive selection (preceding phase)

| Check                | Actual result                                                                                                                                                                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Adaptive tests       | **46 passed**: 37 pure policy cases and nine real PostgreSQL/API cases. Includes all requested candidate scenarios, transitions, repetition, long-run diversity, ownership, trace persistence, old configurations and evidence eligibility. |
| Backend gates        | Ruff lint/format passed for 121 files; strict mypy passed for 114 source files. All **250 existing tests passed** in the broad regression run. The final focused run passed all 46 adaptive tests.                                          |
| Migrations/contracts | Disposable clean upgrade, drift check, complete downgrade/re-upgrade passed; generated contracts and original source hashes/seeds verified.                                                                                                 |
| Frontend             | Zero-warning ESLint, strict TypeScript, **79 tests across 10 files** with one worker, and production build passed.                                                                                                                          |
| Formatting           | Whole-repository Prettier and `git diff --check` passed, including the final documentation refresh.                                                                                                                                         |

An initial integration scenario incorrectly demanded four unrepeated MCQs from
the two-MCQ catalogue: that broad run finished with 292 passes and this one failure.
Its fixture now uses the larger written-question inventory; all assertions remain.
The final focused run passed all 46 adaptive tests, including three additional
review regressions. Review added coverage for repeated same-concept failure
and tied first-history timestamps. Windows child-process restrictions were resolved
with reviewed execution for frontend tests/build. Docker needed startup before
the disposable database checks; no application migrations or seeds were run.
Both disposable databases were removed. Docker Desktop was stopped after
verification, restoring its original stopped state. The first cleanup attempt
was blocked by an automatic approval-review usage limit; the resumed cleanup succeeded.

### Limitations and next task — Explainable adaptive selection (preceding phase)

- Adaptation happens between assessments. A single-question pure API is available
  for a future interview workflow; production interview delivery is not added.
- The current assessment UI keeps its existing configuration controls. Job-specific
  selection is available through the optional API target field; a target picker
  and user-facing explanation display can follow as a separate UI phase.
- The 29-question catalogue has sparse topic/level coverage. Cooldowns and topic
  diversity may require a nearest-level choice, or least-recent reuse, with reasons.
  Explicit difficulty filters never relax. No outcome improvement is claimed.
- No time-based evidence decay or calibrated difficulty is implemented. Older API
  binaries that reject new JSON keys cannot read new adaptive attempts; preserve
  the compatible reader in rollback builds rather than deleting stored traces.
- Next: independent curriculum/policy review, broaden authored coverage, then wire
  this selector into the real interview workflow. Browser E2E and live Clerk were
  not rerun in this backend-engine phase; no new UI was introduced.

## Real assessments (preceding phase)

Implemented following the [assessment plan](.agent/plans/real-assessments.md) and
[workflow, scoring, privacy and rollout specification](docs/ASSESSMENTS.md).
The user-authorized local commit includes the preceding question-bank and
skill-engine phases, which the assessment implementation integrates with.
Commit message: `feat: replace self-rating with real assessment engine`.
No dependency installation, push, live migration, live seed or deployment occurred.

- The runnable V1 launcher no longer offers self-rated sliders, fake metrics or
  its classifier. Original bytes are preserved as a non-executable provenance
  fixture with the original SHA-256/AST seed checks intact; questions/requirements
  and the 15 legacy draft versions remain unchanged.
- Migration `0006_real_assessments` extends existing owned aggregates with frozen
  configuration, validated multiple-select selections, scores and evaluation
  metadata. Existing rows/final answers survive; populated lossy rollback refuses.
- Account/demo workflows configure from actual published inventory, start, save,
  navigate, resume, submit, persist, review and paginate history. Category and
  difficulty are exact filters. Six supplemental authored prompts bring the
  explicit catalogue to 29; no breadth or psychometric validation claim is made.
- MCQ, exact-set multiple-select and literal objective short answers score on the
  server. Answer keys, concepts/rubrics and correctness never leave the assessment
  API before completed submission. Blanks become skipped; drafts stay editable.
- The evaluation-provider boundary validates structured output/provenance and
  bounds conceptual evaluation time. Default `MockAIProvider` uses a documented
  lexical-coverage simulation, requires no key/network call, and does not set
  correctness or validate competence. Objective counts and conceptual points are
  separate, with real category-level response/skip totals and no readiness number.
- Principal/attempt locks, start keys, revisions, immutable final answers and
  atomic submission handle concurrency/retries without duplicate attempts/events.
  Expiry, invalid state/options, limits, foreign ownership and demo CSRF fail safely.
  Provider failures leave saved drafts intact. Frontend failures retain local
  input, block failed navigation and offer saved-state reload/retry.
- Responses are stored privately with question versions/evaluation timestamps.
  Account attempts have no automatic expiry or individual deletion UI; profile
  deletion does not erase preparation history. Demo exit/expiry and principal
  erasure cascade. Privacy/setup/legacy docs and generated contracts are updated.

### Verification — Real assessments (preceding phase)

| Check                | Actual result                                                                                                                                                                                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Backend              | Ruff lint/format passed for 115 files; strict mypy passed for 108 files; **250 tests passed** on disposable PostgreSQL, including 29 new assessment/migration/legacy cases.                                                                                                          |
| Migrations/contracts | Clean upgrade, metadata drift check, complete downgrade/re-upgrade, old-row preservation, populated rollback refusal, OpenAPI and original provenance hashes/seeds passed.                                                                                                           |
| Frontend             | Zero-warning ESLint, strict TypeScript, **79 tests across 10 files** with one worker, and production build passed.                                                                                                                                                                   |
| Browser              | **23 Chrome tests passed** with a seeded disposable API/database. Actual multiple-select save/reload/resume, protected keys, objective/mock review, ownership isolation and demo erasure passed. Zero axe violations in tested desktop/mobile views; screenshots visually inspected. |

An initial concurrent run hit timing failures in unchanged frontend tests and an
existing backend fixture cleanup. Isolated runs passed without changing assertions
or test time limits. A new demo test initially expected 201 from the established
200 session-creation contract; its expectation was corrected without changing the
production API. Live Clerk credentials remain unavailable: account integration
uses signed tokens/trusted test JWKS and mocked frontend SDK/transport.

The browser harness removed its temporary API/database, and the owned port-3100
frontend was stopped. A final production build restored the normal backend
destination. Catalogue validation reports 29 questions without database writes;
original source hashes, frozen migrations and legacy seed reconciliation remain
verified.

Rollout: apply migration 0006, validate/publish the two manifests explicitly, then
deploy the matched API/frontend in an authorized environment. Running services
have not been upgraded. Future work: independent curriculum review, a real
interview workflow, and live Clerk verification before an authorized release.

## Production question bank (preceding phase)

Implemented on `rebuild/professional-v2` following the
[question-bank plan](.agent/plans/question-bank.md) and
[question-bank API/content/rollout guide](docs/QUESTION_BANK.md).
Preserved the preceding uncommitted skill-engine work. No new dependencies, commit,
push, live migration, application-data seed or deployment occurred.

### Content and behavior

- Preserved all original files and 15 legacy title-only version-1 drafts. Authored
  complete version-2 adaptations plus eight broader-topic prompts: **23 questions**
  in the explicit versioned catalogue, with constraints, expected concepts, tags,
  role relevance, difficulty/type and source classification. No volume/usage or
  outcome claims. Difficulty and role relevance are editorial classifications.
- Migration `0005_question_bank` adds nullable version metadata, frozen ordered
  concepts/tags/roles and owned append-only practice attempts. Existing content and
  history remain intact. Latest released versions govern browsing; retirement does
  not resurrect an older release. Populated lossy downgrade is refused.
- Explicit validated transactional publication preserves stable legacy IDs/drafts,
  retirement and editorial versions; reruns are idempotent, publication is serialized
  and collisions roll back. API reads/demo bootstrap never publish global content.
- Account/demo Question Bank now supports literal search, category/topic, real
  difficulty/type/role filters, active/inactive views, stable pagination, owned
  bookmarks and attempted state. All filters apply in PostgreSQL before paging;
  escaped wildcard input cannot broaden search. Facets respect private ownership.
- Detail shows prompts and MCQ option text/IDs; no answer keys, correctness flags
  or rubric anchors are returned. Expected concepts unlock only after an owned
  submitted response to that exact version. Historical attempts never reveal newer
  concepts. Bookmarks are independent of attempted state and survive version changes.
- Submitted history combines owned question-bank/assessment/interview responses
  across versions; draft/skipped work is excluded. Bank practice is explicitly
  self-review (simulation in demo), with no fabricated score or competence evidence.
  Responses can be deleted from bank history; deleting the final qualifying attempt
  removes concept access on the next read. Other channels preserve their history.
- Inputs/storage are bounded, ownership is resolved server-side, duplicate retries
  return one stored attempt, changed-key payloads/stale versions fail safely, and
  owner locks serialize concurrent mutations. Demo mutations retain Origin/CSRF and
  the two-visitor quota. Responses stay private, never execute and are not sent to AI.
- Frontend has loading/empty/error/retry, canceled/stale-response guards, retained
  failed answers/retry keys, duplicate-gesture prevention, explicit self-review and
  confirmation before response deletion. Filters/results/history are separate small
  components; privacy, authentication, development and rollout docs are updated.

### Verification — Production question bank (preceding phase)

| Check                            | Actual result                                                                                                                                                                                                                                                                                               |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend                          | Ruff lint/format passed for 105 files; strict mypy passed for 99 files. **221 tests passed** on disposable PostgreSQL, including 28 new bank/content/migration cases.                                                                                                                                       |
| Migration/contracts/preservation | Clean upgrade, metadata drift, downgrade/re-upgrade, populated rollback refusal, original-row preservation, OpenAPI and original V1 hashes/seed checks passed.                                                                                                                                              |
| Frontend                         | Zero-warning ESLint, strict TypeScript, **68 tests across nine files** and production build passed. Tests cover filters/pages, stale responses, retained retry keys, gated concepts, history/deletion and SDK-authorized transport.                                                                         |
| Browser/accessibility            | **23 Chrome browser tests passed** with a seeded disposable API/database, including actual difficulty/pages/bookmarks, concept disclosure, reload/history/deletion and existing two-visitor isolation. Zero axe violations in tested desktop/mobile views; screenshots inspected and mobile overflow fixed. |
| Formatting                       | Whole-repository Prettier, diff checks and Compose configuration passed; original files and frozen migrations have no diff. Explicit content-directory validation reported 23 questions with no writes.                                                                                                     |

Browser fixtures use a seeded disposable database and actual API responses. The
bank flow shares the existing demo visitor scenario rather than weakening the
production two-visitor quota. Real Clerk credentials remain absent: backend account
tests use signed tokens/trusted test JWKS; frontend account tests mock SDK/transport.
Live managed account sign-in was not exercised.

The final production build restored the normal backend destination. The browser
harness removed its temporary API/database and the owned port-3100 frontend was
stopped. One concurrent build/test run hit timing failures in unchanged profile
tests; the separate rerun passed without changing test limits or assertions.
The optional Compose seed tool uses a read-only content mount and defaults to
validation without writes; no live container seed command was run.

### Rollout and next task

- Apply migration 0005, validate the authored catalogue and explicitly run its
  `--apply` seed in the reviewed environment, then deploy updated API/frontend.
  Existing Compose services still serve their preceding implementation.
- This phase provides durable submitted practice/self-review, not scored assessments
  or durable unfinished drafts. Account responses have no automatic expiry and can
  be deleted individually; demo responses expire with the workspace. Active deletion
  does not erase backups. Full account/history erasure remains separate work.
- Continue independent curriculum review with new immutable versions. The current
  23-question set is deliberately limited, not a claim of comprehensive coverage.
- Next: implement deterministic objective assessment creation/answer/submission/
  scoring against this versioned content, with protected keys and explicit evaluation
  provenance. Configure/exercise live Clerk before an authorized deployment.

## Explainable skill evidence engine (preceding phase)

Implemented on `rebuild/professional-v2` using the
[skill evidence plan](.agent/plans/skill-evidence-engine.md). The complete versioned
policy and API are documented in [SKILL_EVIDENCE_ENGINE.md](docs/SKILL_EVIDENCE_ENGINE.md).
No ML, external service, dependency, database migration, commit, push or deployment
was introduced. Existing application data and Compose services were preserved.

### Behavior and integrity

- Pure deterministic engine separates job importance, resume mentions and
  demonstrated competence. Profile interests and user-added claims remain
  self-reported. Missing resume evidence never establishes missing ability.
- Required/Preferred use confirmed linked requirements for the selected job's
  latest version. Proposed/text-only matches are Mentioned; absent selected-job
  evidence is Low relevance. Rejected linked requirements suppress re-extraction.
- Completed deterministic assessments and eligible completed interview rubrics
  contribute tested evidence. Simulation, self-review, model-assisted output,
  missing grades, incomplete sessions, incomplete/mismatched rubric coverage,
  unreviewed questions and multi-skill attribution cannot validate competence.
- Latest eligible result per channel/concept governs retakes; unresolved negative
  results win over positives. Strong evidence requires two distinct successful
  concepts, not repeated attempts. Assessment validation remains separately visible
  when interview practice is needed. These are documented editorial rules, not
  statistical confidence or claims of mastery.
- Priority sorts by Required/Preferred/Mentioned/Low relevance, then
  Practice/Validate/Maintain, then skill name/key. Ordinal positions and the rubric
  anchor threshold are documented; no summed score or readiness percentage exists.
- Read-only account/demo endpoints resolve ownership on the server, protect
  private question content, return source IDs/excerpts/provenance, and use
  no-store responses. Every input category is bounded; overflow is disclosed and
  withholds validation. No new evidence snapshots or retention stores are created.
- Skill Matrix is available at `/app/skills` and `/demo/skills`, with all owned
  target choices, separate evidence columns, priority/source disclosures, refresh,
  loading/empty/error/retry states and stale-response protection. Account changes
  remount private state. Demo sources never validate real competence.

### Verification — Explainable skill evidence engine (preceding phase)

| Check                     | Actual result                                                                                                                                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Targeted evidence tests   | **50 passed**, covering pure policy, real PostgreSQL source adapters, authenticated ownership, job versions, corrections/rejection, retakes, rubric boundaries/completeness, exclusions, demo isolation and partial-input behavior.  |
| Backend full suite        | Ruff lint/format passed across 94 files; strict mypy passed for 89 files. **193 tests passed** on disposable PostgreSQL; migration round trips, schema drift, OpenAPI and legacy preservation checks passed.                         |
| Frontend lint/types/tests | Zero-warning ESLint and strict TypeScript passed; **60 tests passed** across eight files, including authenticated matrix transport, malformed responses, target races, source rendering, empty/retry/refresh and existing workflows. |
| Production/browser        | Production build and **23 Chrome browser tests passed** with an isolated API/database. Final normal-destination production build also passed.                                                                                        |
| Accessibility/visual      | Zero axe violations in tested views, including actual matrix markup on desktop/mobile and live demo source disclosure. Screenshots inspected; mobile table has a labeled keyboard-scrollable region.                                 |
| Formatting                | Whole-repository Prettier and `git diff --check` passed.                                                                                                                                                                             |

The test fixtures follow published-content and completed-evaluation immutability;
no integrity protections were weakened. Invalid content snapshots used for adapter
defense tests remain in memory and are rolled back. Windows frontend checks used
reviewed child-process access. Browser checks removed their temporary API/database;
the owned port-3100 frontend was stopped.

### Limits and next task — Explainable skill evidence engine (preceding phase)

- The engine consumes existing structured history; production assessment/interview
  creation and a requirement-review editor remain separate work. New raw job text
  consequently produces Mentioned entries until requirements are reviewed.
- Finite lexical matching can miss skills and retain negative/aspirational mentions;
  it does not interpret experience or assert proficiency. Source dates are shown;
  no automatic evidence decay or calibrated readiness prediction is claimed.
- Real Clerk browser credentials remain unavailable. Backend ownership tests use
  signed test tokens; frontend account integration mocks SDK/transport. Live browser
  verification uses the isolated fictional demo, not real-account sign-in.
- Next: author reviewed questions/rubrics and build the deterministic assessment
  workflow, then connect explicit job-requirement review to the existing schema.
  Configure and exercise live Clerk before an authorized deployment.

## Secure resume upload and evidence review (preceding phase)

Implemented on `rebuild/professional-v2`, following the
[resume ingestion plan](.agent/plans/resume-ingestion.md). The user explicitly
authorized committing and pushing this work to GitHub, including the preceding
verified candidate profile/target-job changes still in the working tree.
Existing application database and Compose services were preserved; this phase
does not deploy or migrate them.

### Functionality, integrity and privacy

- Account Resume now uploads PDFs, lists owned records, displays original cited
  evidence, and supports corrections, category/review changes, explicit additions,
  entry deletion and confirmed aggregate deletion. Loading/empty/error states,
  retained failed drafts, conflict reload and duplicate-gesture guards are present.
- Require PDF MIME, `.pdf` extension, validated normalized filename, PDF signature
  and strict parsing. Filename paths/control characters are rejected and never
  become filesystem paths. Bound uploads to 5 MiB/20 pages, extracted text to
  100,000 characters, decoded streams to 2 MiB and evidence to 100 entries.
- Stream raw bodies without multipart spooling. Two in-flight read/parse operations
  per API process, 15-second read and worker deadlines, 512 MiB OS worker limits
  on Windows/Linux, and Linux CPU bounds protect processing. Workers receive no
  application credential environment, suppress parser logs, and return validated
  excerpts/metadata through private pipes. Encrypted/corrupt/excessive PDFs fail
  safely without creating records. Scans/blank PDFs explain missing selectable text.
- Raw PDFs and full extracted text are never permanently stored or logged. They
  remain only in request/worker memory. Retained data is the validated display label,
  checksum/page/size/extraction metadata, selected cited excerpts and user edits.
  No OCR, AI, external document service, link fetching or automatic profile filling.
- The deterministic `lexical-sections-v1` extractor proposes explicit language,
  framework, database/tool mentions and project/education/experience excerpts.
  Negative and aspirational mentions preserve their context for review. It creates
  no global skills, competence scores, experience estimates or missing-skill verdicts.
  **No evidence detected never means the candidate does not know something.**
- Proposed, confirmed-by-user and rejected states are explicit. Corrections retain
  original PDF excerpts; user additions have no PDF source fields. Rejected claims
  are excluded from dashboard preparation context. Confirmation is user review,
  not independent verification. Every API uses verified account ownership, strict
  input bounds and locked aggregate revisions; missing/foreign IDs return 404.
- Deleting an unreferenced resume removes every version/excerpt/correction and
  preserves the account/profile/jobs. Existing history references can block the
  aggregate deletion; individual evidence can still be erased. Active-record
  deletion does not erase operator backups. Account evidence has no automatic
  expiry; full account/history erasure remains unavailable and is disclosed.
- Migration `0004_resume_evidence` adds revisions, extraction notes and evidence
  category/origin fields, preserving legacy IDs/excerpts and compound ownership
  constraints. User-origin source fields must be null. Lossy downgrade is refused.
  Earlier frozen migrations and V1 files are unchanged. Added only pinned
  `pypdf==6.20.1`, with a matching lockfile and generated API contracts.
- Updated public privacy/product availability copy, README, authentication,
  development and data-model notes; added [resume API/privacy guide](docs/RESUME_PRIVACY.md).

### Verification — Secure resume upload and evidence review (preceding phase)

| Check                     | Actual result                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend lint/format/types | Ruff passed across 82 Python files; strict mypy passed for 77 source/test/script files.                                                                                                                                                                                                                                                                       |
| Backend tests             | **143 passed** on fresh migrated PostgreSQL, including actual valid/blank/encrypted/corrupt PDFs, invalid MIME/extensions/signatures/paths, declared and chunked oversized bodies, page/decompression bounds, worker timeout/reaping, deterministic source offsets, ownership, corrections/rejection, concurrent revisions and deletion/history preservation. |
| Migrations/contracts      | Upgrade, metadata drift, downgrade/re-upgrade, original content preservation, populated rollback refusal, OpenAPI and legacy hashes/seeds passed. Dedicated 0003-to-0004 preservation/recovery test passed.                                                                                                                                                   |
| Frontend lint/types/tests | Zero-warning ESLint and strict TypeScript passed; **52 tests passed** across seven files, including SDK-authorized upload/review/delete transport, retained failed file/draft state, safe errors, no-evidence semantics and existing account/context workflows.                                                                                               |
| Production/browser        | Production build and **21 Chrome browser tests passed** with a disposable API/database; zero axe violations in tested views, including desktop/mobile actual resume form/evidence markup. New screenshots visually inspected.                                                                                                                                 |
| Linux runtime             | Separate backend container image built with frozen production dependencies. Non-root parser passed valid/blank/encrypted/corrupt/compressed-limit checks with network disabled, read-only storage and container resource bounds. Existing service images/containers were not replaced.                                                                        |

The resume browser preview is explicitly a static test fixture, not a live account
or authentication bypass. Existing live demo/connectivity/mobile/modal regressions
remain covered. Real Clerk credentials are absent; managed account browser upload
was not run. Windows backend tests use genuinely signed tokens and trusted test
JWKS; frontend account integration mocks the SDK/transport. Worker behavior was
verified on both Windows and Linux.

Whole-repository formatting and `git diff --check` passed. The final production
build restored the normal backend destination. The browser harness removed its
temporary API/database, and the owned port-3100 frontend was stopped. A targeted
review of 80 commit candidates found no configured secrets, credential-shaped
strings or environment files; cache/test/runtime artifacts remain ignored.

### Rollout limits and next task — Secure resume upload and evidence review (preceding phase)

- Apply migrations through `0004_resume_evidence` before starting the updated
  API/frontend. Existing services still serve the previous implementation.
- The finite extractor cannot reliably understand all layouts or semantic claims;
  users must review proposed evidence. No OCR or proficiency inference is provided.
- Process limits are resource isolation, not complete OS sandbox certification.
  Production ingress, container resource configuration, HTTPS, logging policy,
  backups and live Clerk account isolation need the documented release review.
- Next: configure and exercise live Clerk with two accounts, apply the reviewed
  rollout, then build assessments using explicitly reviewed candidate context.

## Candidate profile and target jobs (preceding phase)

Implemented the requested account workflows end-to-end in source on
`rebuild/professional-v2`, following the
[candidate context plan](.agent/plans/candidate-profile-target-jobs.md).
No new dependencies, commit, push, or deployment occurred in this phase. The
existing application database/Compose services were preserved; the new migration
was applied and verified only on disposable PostgreSQL databases.

### Functionality and data handling

- Settings/Profile now saves optional display name, short education description,
  graduation year, supplied technologies/interests and interview date, alongside
  existing target role, experience, timezone and study budget. The form uses hours
  per week and persists whole minutes. Optional fields can be cleared. No contact,
  demographic, birth-date, institution or grade fields were added.
- User interests live in normalized `profile_interests` rows with explicit owner/
  profile constraints. They remain supplied labels; neither profile context nor
  job descriptions create inferred skills, requirements or competence evidence.
- Added owned profile GET/PUT/DELETE. Profile edits/deletion require current ID and
  revision; identity prevents stale edits after delete/re-create. Deletion erases
  profile/interests and clears the UI while preserving account, jobs and history.
- Target Job now supports a persisted paginated list, status filter, creation,
  detail view, editing and confirmed deletion. Title and supplied description are
  required; company, source URL and notes are optional. Priority is low/normal/high;
  status is saved/applied/interviewing/archived. Source links are HTTP(S), without
  embedded credentials, and are stored without fetching. Job text renders as text.
- Every target read/write uses the resolved account owner; unknown ownership input
  is rejected, foreign/missing IDs return 404, edits/deletion use locked revisions,
  lists are bounded to 20 per page, and account storage is limited to 100 jobs.
- Description edits append immutable versions; metadata edits preserve the latest
  description without creating duplicate versions. Referenced jobs cannot be
  deleted; a safe conflict offers archive editing and preserves preparation history.
- Forms retain failed edits, show field errors and save feedback, block duplicate
  gestures, and offer explicit reload/discard recovery after conflicts. Shared
  dialogs are scrollable on mobile. Existing auth separation, subject-change guards,
  empty/loading states, demo disclosure and recruiter-demo operations are preserved.
- Revision `0003_candidate_context` preserves existing rows, adds optional profile
  fields and interest rows, and adds target metadata with neutral defaults. It
  refuses rollback that would discard populated new context. Readiness/smoke/browser
  expectations now require the new schema. OpenAPI and TypeScript contracts match.
- Updated public privacy copy, authentication/data/development/UI documentation,
  README and [candidate context API/retention guide](docs/CANDIDATE_CONTEXT.md).

### Verification for candidate context

| Check                | Actual result                                                                                                                                                                                                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend lint/format  | Ruff passed across 70 Python files.                                                                                                                                                                                                                                                                      |
| Backend strict types | mypy passed for 66 source/test/script files.                                                                                                                                                                                                                                                             |
| Backend tests        | **115 passed** on a fresh migrated PostgreSQL database, including CRUD, input bounds, supplied-label behavior, ownership, unauthenticated/foreign access, concurrent edits, stale revisions, profile re-creation, history-preserving deletion and count/list bounds.                                     |
| Migration/recovery   | Clean upgrade, metadata drift, downgrade to base/re-upgrade, legacy demo compatibility and populated rollback refusal passed. Dedicated 0002-to-0003 test preserved existing profile/job/description data and refused lossy rollback. Application database was not downgraded or migrated in this phase. |
| Contracts/legacy     | OpenAPI drift and original hashes/seeds passed; generated frontend types updated. Original V1 files and frozen 0001/0002 migrations have no diff.                                                                                                                                                        |
| Frontend lint/types  | Zero-warning ESLint and strict TypeScript/Next route generation passed.                                                                                                                                                                                                                                  |
| Frontend tests       | **41 passed** across six files. Includes authenticated target CRUD integration, optional profile fields/clearing, hour conversion, supplied-label validation, confirmation, conflict/error recovery and preserved account-isolation checks.                                                              |
| Production build     | `pnpm build` passed, including the final build with the normal backend destination restored.                                                                                                                                                                                                             |
| Browser checks       | **20 Chrome tests passed** using an isolated production frontend/API and fresh migrated disposable database; existing real demo persistence/isolation/deletion and all workspace regressions passed.                                                                                                     |
| Accessibility/visual | Zero axe WCAG A/AA violations in tested public/demo/modal views and desktop/mobile profile/job forms; new form screenshots inspected. Form QA uses actual component markup rendered as explicitly labeled static test fixtures, with no account auth bypass. This is not full WCAG certification.        |

One browser run hit a transient PostgreSQL connection timeout; the full rerun
passed without relaxing checks or increasing connection timeouts. Added a backend
regression and safe 503 handling for database timeouts instead of unexpected 500
responses. Windows process permissions used reviewed local execution. The browser
harness removed its test API/databases; the temporary native frontend was stopped.

### Rollout limits and next task — Candidate profile and target jobs (preceding phase)

- Apply migration `0003_candidate_context` before starting the updated API/frontend
  in the intended environment. Existing Compose services still serve the preceding
  implementation. No automatic deployment or application-data changes were made.
- Real Clerk credentials remain absent. Live managed sign-in/profile/job CRUD was
  not exercised against Clerk. Backend tests use genuine signed JWTs with a trusted
  mock JWKS transport; frontend integration tests mock SDK/transport. Static browser
  form fixtures verify layout/accessibility, not live account interactions.
- Resume ingestion, extraction/requirements review, assessment creation, AI,
  exports/full account erasure and scheduled-cleanup operational follow-up remain
  later work. Account profile/job retention and the archive/delete boundary are
  documented explicitly.
- Next: configure/test live Clerk with two accounts and apply the reviewed local
  rollout, then implement the deterministic assessment slice against supplied
  candidate/job context with authored content and preserved history.

## GitHub publication request

On 2026-10-13 the user explicitly authorized committing and pushing the accumulated
V2 foundation, relational model, authentication/recruiter demo and UI work to the
existing `rebuild/professional-v2` branch on `origin`, using the commit message
`feat: add authentication and recruiter demo mode`. The verification results below
record the completed implementation checks. A pre-commit scan of 178 candidate
files found no configured secrets or credential-shaped content; local credentials,
dependencies and runtime/build artifacts remain ignored. Earlier no-commit/no-push
notes describe the state at the end of those implementation phases.

## Public and authenticated UI foundation (preceding phase)

Implemented the requested public site and ten-section workspace on
`rebuild/professional-v2`, following the [UI plan](.agent/plans/ui-foundation.md).
Existing uncommitted foundation/authentication/data work was preserved. No package,
schema, migration, backend endpoint, or application database changes were needed.
No commit, push, merge, or deployment was performed in this phase.

### Interface and behavior

- Replaced the connectivity-first landing screen with product explanation, how it
  works, feature overview, privacy section, demo/account CTAs and a professional
  footer. Added `/privacy`; preserved the live connection check at `/status`.
- Established warm neutral surfaces, dark ink, muted green, system sans text,
  editorial serif headings, subtle borders and ample spacing. No gradient headings,
  fabricated testimonials/logos/outcomes, decorative animation or external fonts.
- Added deep-linked Dashboard, Target Job, Resume, Assessments, Interviews,
  Question Bank, Roadmap, Project Defense, Progress and Settings/Profile sections.
  Shared desktop sidebar and mobile modal navigation preserve active-route state,
  browser history and main-content focus. Existing `/app/*` auth protection remains.
- New-account dashboards lead with profile onboarding and preparation actions;
  no fabricated scores, progress, completed work or readiness metrics appear.
  Saved profile context and histories come from the existing owned API. Features
  without production workflows have explicit, useful empty/unavailable states.
- Added reusable buttons/link buttons, labeled inputs/selects/form sections,
  tables/badges, line icons, empty states, skeletons, errors and native dialogs.
  Visible focus, skip links, modal focus wrapping/restoration, Escape, mobile table
  scroll regions and associated validation/status messages support keyboard use.
- Profile edits persist through the existing revision-checked endpoint, with
  pending/success/error feedback, retained failed edits, duplicate-submit protection,
  and explicit discard/reload recovery. Account changes remount private state; a
  late token result cannot send an old account's pending profile after unmount.
- Demo now uses the same route-based shell. Fictional/simulation disclosure stays
  visible; sample results, evidence and events are labeled. Task status filtering,
  completion persistence, retry/reset and owned deletion are preserved. Exit uses
  a confirmation dialog with recoverable deletion errors. Demo profiles are read-only.
- Updated authentication/development/README guidance and added the
  [UI foundation guide](docs/UI_FOUNDATION.md) with routes, components and limits.

### Verification for the UI phase

`pnpm format:check` also passed across all matched repository files.

| Check                           | Actual result                                                                                                                                                                                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm lint`                     | Passed; zero warnings.                                                                                                                                                                                                                                |
| `pnpm typecheck`                | Passed; Next route generation and strict TypeScript.                                                                                                                                                                                                  |
| `pnpm test`                     | **29 passed** across four files, including API validation, truthful onboarding/empty states, profile validation/save/conflict/duplicate handling, account isolation and in-flight account changes.                                                    |
| `pnpm build`                    | Passed; production Next build, including final build with the normal backend destination.                                                                                                                                                             |
| Browser verification            | **18 Chrome tests passed** against the production frontend on port 3100, with a fresh migrated disposable PostgreSQL database and temporary API on port 8100.                                                                                         |
| Browser coverage                | Real connectivity, API failure/retry, two-visitor demo isolation/foreign-ID rejection/persistence/deletion, missing-key account behavior, all ten section deep links, mobile overflow, skip navigation, dialog focus/Escape/error recovery.           |
| Accessibility and visual review | Automated axe WCAG A/AA checks found **0 violations** in tested public, privacy, desktop/mobile demo sections and modal states. Desktop/mobile landing, dashboard, settings and table screenshots inspected. This is not complete WCAG certification. |
| Browser harness                 | Added optional bounded API/frontend ports so existing services need not be stopped. Ruff lint/format and strict mypy passed for the modified script (with `MYPYPATH=backend/src`).                                                                    |
| Preservation                    | Original `app.py`, `questions.json`, `requirements.txt` have no Git diff; no dependencies or lockfiles changed in this UI phase.                                                                                                                      |

Initial Windows sandbox worker restrictions were resolved with reviewed local
execution. Browser verification found and fixed modal focus wrapping. An aggregate
ten-screen sweep was split into independent per-section checks, with three workers
to avoid local resource contention; assertions and coverage were retained. Temporary
API/database resources were removed by the harness; the temporary native frontend
was stopped. Existing Compose services were not rebuilt or replaced, so their UI
remains the earlier version until an explicitly authorized local update.

### Limits and next task — Public and authenticated UI foundation (preceding phase)

- Real Clerk credentials remain absent. Live sign-up/sign-in/profile-save/sign-out
  against Clerk was **not run**; account UI integration tests use mocked SDK/transport.
  No production authentication bypass or fake signed-in preview was added.
- Real resume/job/repository ingestion, published question browsing, assessment and
  interview creation, roadmap generation, AI evaluation, exports and account erasure
  remain later workflows. The UI communicates these boundaries explicitly.
- The existing Compose cleanup container was already restarting when inspected;
  investigate that operational issue separately before relying on scheduled erasure.
  This UI phase did not change that service or claim to reverify its operation.
- Next: configure/test live Clerk with two accounts, then implement the reviewed
  deterministic assessment slice with authored questions, durable drafts and grading.
  Public deployment/security gates from the preceding phases still apply.

## Relational and account implementation (preceding phases)

The relational data model, account authentication/authorization and separate
recruiter demo are implemented on `rebuild/professional-v2`. The earlier V2
foundation remains intact. No commit, push, merge or public deployment occurred.
The final frontend, backend, PostgreSQL and hourly cleanup run through Docker
Compose on localhost; the migration service exited with code 0. Temporary native
verification services were stopped.
Clerk keys were not supplied; real managed sign-up/sign-in/sign-out requires the
documented configuration and was not exercised against a live Clerk instance.

Read the repository rules, architecture, status and affected code before these
phases. Work followed the [relational plan](.agent/plans/relational-data-model.md)
and [account/demo plan](.agent/plans/authentication-demo.md). The explicit user
request advances the schema and account/demo slice ahead of the architecture's
original incremental phase order; broader product workflows remain outside scope.

### Relational persistence

- Added 36 normalized domain tables in revision `0002_relational_model`, alongside
  the three existing demo infrastructure tables. All requested User/Profile,
  TargetJob, Resume, Skill/evidence/requirements, Question/Bookmark, assessment,
  interview/evaluation, roadmap/progress and project entities are represented.
  Versioned content, grading criteria/options, source files/facts/citations and
  evaluation dimensions use relational rows, not application-state JSON blobs.
- UUID identities, UTC server timestamps, constrained enums, meaningful bounds,
  deliberate foreign-key cascades/restrictions, owner-first indexes and compound
  ownership/aggregate foreign keys enforce integrity. Published grading/content,
  final answers, terminal evaluations and historical contexts have database guards.
  Progress facts are append-only and reference completed owned work.
- Preserved existing demo UUIDs and hashed credentials with a principal backfill.
  Migration SQL is frozen independently of live models. Populated domain rollback
  refuses destructive changes; empty rollback/re-upgrade and compatibility demo
  backfill/recovery are tested. The application database was upgraded, never downgraded.
- Installed an idempotent validated development loader and actually loaded
  **15** legacy title-only drafts, **six** skills and **seven** aliases into the
  application database. A second import returned the same count without duplicates.
  Original `app.py`, `questions.json` and `requirements.txt` remain unchanged.
  No missing prompt, answer, rubric, user history or large question count is invented.
- Documented table mappings, history/erasure rules, migration recovery and seeds in
  [DATA_MODEL.md](docs/DATA_MODEL.md); updated architecture/development/legacy notes.

### Accounts and recruiter demo

- Installed pinned Clerk Next.js integration and PyJWT/cryptography dependencies;
  updated both lockfiles. Sign-up/sign-in pages, conditional Clerk provider,
  protected account dashboard and SDK sign-out are implemented. Missing keys show
  an explicit account-unavailable state; no simulated account login is accepted.
- FastAPI verifies trusted RS256 signatures, configured issuer/audience, subject,
  expiry/issued-at/not-before, authorized frontend origin and at most 60-second
  token lifetime. Fixed trusted JWKS discovery has bounded caching/rotation,
  response size and timeout; token-provided key URLs are rejected. Verification
  and discovery failures fail closed with safe structured errors.
- Reusable account/demo dependencies resolve the principal server-side. Account
  bootstrap is an explicit authenticated POST. All exposed private reads/writes
  filter by owner; forged ownership input is rejected. Suspension remains effective;
  foreign private IDs return 404. Profile changes use row locks and revision checks.
  Frontend bearer tokens remain in SDK memory and account data is subject-scoped.
- Landing **Try Interactive Demo** opens a separate cookie-owned workspace without
  sign-up or AI keys. Each visitor gets Aarav Rao **(fictional)**, fictional resume
  evidence/target, three authored private questions, two simulated assessment
  attempts, one simulated interview, three roadmap tasks and four initial progress
  events. Persistent disclosure and simulation labels prevent real-usage/AI claims.
- Demo task completion is CSRF/Origin protected, owner-scoped and idempotent.
  Reload preserves edits; exit erases only that visitor's principal/private records.
  Expired cookies can be reset safely; live resets still require CSRF. The two-new-
  workspace/hour quota and 24-hour expiry remain enforced. Hourly cleanup erases
  the entire expired private graph. Account credentials never select demo mode.
- Added [AUTHENTICATION.md](docs/AUTHENTICATION.md) with actual Clerk template,
  issuer/key/origin setup, verification behavior and known release limitations.

### Verification for these phases

| Check                      | Actual result                                                                                                                                                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend lint/format        | Ruff passed; 63 Python files formatted.                                                                                                                                                                                                         |
| Backend strict types       | mypy passed for 60 source/test/script files.                                                                                                                                                                                                    |
| Backend tests              | **86 passed** on fresh real PostgreSQL; no skipped integration cases.                                                                                                                                                                           |
| Clean migrations           | New random database: upgrade → metadata check → tests → downgrade to base → upgrade → metadata check passed; created test database removed afterward.                                                                                           |
| Recovery/backfill          | Separate clean migration tests preserve legacy demo IDs/hashes and refuse populated rollback without losing data.                                                                                                                               |
| Ownership/auth             | Real RSA-signed token tests with trusted mock JWKS; invalid claims/signatures, key rotation/outage, suspension, forged owner input, foreign IDs, account/demo confusion, CSRF/expiry/reset and erasure passed.                                  |
| Seeds/content              | Exact 15-title reconciliation, idempotent reruns, editorial preservation and invalid-manifest rejection passed; application seed ran twice successfully.                                                                                        |
| Frontend lint/format/types | ESLint zero-warning gate, Prettier and strict TypeScript passed.                                                                                                                                                                                |
| Frontend unit/build        | **8 tests passed**; native Next.js production build passed.                                                                                                                                                                                     |
| Browser verification       | **5 Chrome tests passed**, including live connectivity, recovery, keyboard/mobile behavior, isolated persistent demo, deletion and missing-key account state. Used a newly created migrated database; temporary API/database removed afterward. |
| Accessibility/visual       | Automated axe checks found **0 violations** in tested views; recruiter demo and foundation screenshots inspected. This is not complete WCAG certification.                                                                                      |
| Startup/database           | Updated native frontend/API started; actual direct/proxied health/readiness connected to PostgreSQL at `0002_relational_model`. Updated backend/migrate/cleanup containers built and started successfully.                                      |
| Contracts/preservation     | OpenAPI export/drift, generated TypeScript types, source hashes and original-file Git diff checks passed.                                                                                                                                       |
| Live Clerk flow            | **Not run:** user confirmed no development keys; complete required setup is documented.                                                                                                                                                         |

`scripts/check_backend.py` now creates a previously nonexistent random test
database and removes only that created database. `scripts/check_browser.py`
provides an isolated repeatable browser check without modifying application quotas;
it refuses an existing API listener and stops only its own temporary process tree.

Windows sandbox process-spawn restrictions were resolved through reviewed local
execution; tests/type checks were not weakened. Docker registry timeouts required
cached backend downloads and a bounded longer timeout. The frontend container
build passed after registry connectivity recovered, including the final pnpm
configuration. Full Compose startup/health and direct/proxied smoke checks passed.
All five frontend page routes returned 200; unauthenticated account access returned
structured 401 with no-store headers. Moved non-authentication pnpm 12 settings
from `.npmrc` into `pnpm-workspace.yaml`, so strict engine checks, bounded fetch
timeout and request concurrency apply. Configured local secret values were absent
from 97 checked source/static files; this was a targeted check, not a security audit.

### Remaining work and next task

- Configure Clerk development keys/issuer and the named 60-second API JWT template,
  then exercise live sign-up, sign-in, profile save and sign-out with two accounts.
  Signed JWTs can remain usable until expiry plus leeway; no instant revocation is claimed.
- Implement the next reviewed deterministic assessment slice with genuinely authored
  published questions/rubrics, saved drafts, grading and submission idempotency.
  The schema and fictional demo history do not constitute those production workflows.
- Real resume/repository ingestion, AI providers, adaptive selection, durable jobs,
  exports/account/source erasure, signed Clerk lifecycle webhooks, consent and backup
  recovery remain later tasks. No upload or AI endpoint was opened here.
- Public HTTPS ingress, trusted proxy/client-IP policy, production CSP, separate
  migration/runtime DB roles and release/security review remain required before
  public release. Current Compose services bind to localhost. CI is configured,
  but no GitHub run occurred because nothing was pushed.

Local entry points: [frontend](http://localhost:3000),
[demo](http://localhost:3000/demo), [liveness](http://localhost:8000/health),
[readiness](http://localhost:8000/api/v1/health/ready).

## Foundation verification archive (2026-10-09)

The following records the earlier foundation phase only. Its phase-specific
counts and deferred work are superseded by the current implementation above.

### Foundation phase

V2 foundation implemented and locally verified on `rebuild/professional-v2`.
V1 baseline: `48fcd90`; preceding architecture documentation: `997f27c`.
The frontend, backend, PostgreSQL, and hourly demo cleanup are running through
Docker Compose on localhost. The one-shot migration service exited successfully.
Temporary native processes used for verification were stopped.

No commit, push, merge, or public deployment was performed. Major product features
remain outside this foundation request.

### Foundation completed work

- Read `AGENTS.md`, the preceding status, `.agent/PLANS.md`, the complete
  [approved architecture](docs/V2_ARCHITECTURE.md), and existing source/data;
  inspected Git status before implementation. Followed the
  [foundation plan](.agent/plans/v2-foundation.md).
- Created the explicitly requested `frontend/`, `backend/`, `docs/`,
  `scripts/`, and `.github/` structure, plus `content/` for preserved editorial
  seeds. These paths replace the architecture's proposed `apps/web/` and
  `apps/api/`; the modular-monolith topology is unchanged.
- Installed pinned frontend dependencies with pnpm 12.8.1 and Python dependencies
  with uv 0.12.24. Both lockfiles are present. Native checks used the existing
  Node 26.8.1/Python 3.12.1 installations; containers use Node 24 LTS/Python 3.12.
- Added Next.js **16.4.0**, React **19.3.0**, App Router, strict TypeScript **5.9.3**
  with unchecked-index checking, Tailwind **4.3.3**, ESLint, Prettier, accessible
  button/card primitives, and a responsive live connectivity screen. No fabricated
  metrics or AI capabilities are displayed.
- Added FastAPI **0.143.0**, Pydantic **2.14.0**, typed pydantic-settings,
  SQLAlchemy **2.1.4** with asyncpg, Alembic **1.20.0**, pytest, Ruff, and strict
  mypy. Configuration and API errors hide secret values; responses have safe
  error envelopes, request IDs, and no-store headers, including unexpected errors.
- Implemented `GET /health` for liveness and `GET /api/v1/health/ready` for real
  PostgreSQL/schema readiness. Next.js forwards `/api/v1/*` to FastAPI.
  Deterministic OpenAPI export and generated frontend types are checked for drift.
- Added the initial versioned migration for expiring demo workspaces, hash-only
  credentials, ownership FK/cascade, and atomic creation limits. Demo requests
  resolve the owner from an opaque HttpOnly cookie; exact Origin checks protect
  bootstrap, CSRF protects reuse, and account bearer credentials never select demo
  mode. No candidate input, upload, or AI operation is accepted.
- Added PostgreSQL **18.6**, persistent Compose storage, localhost-only published
  ports, one-shot migrations, startup health gates, hourly cleanup, and non-root
  application containers. Base images are pinned by digest; builds use frozen
  lockfiles. Only the needed resolver install script is explicitly permitted by
  pnpm's current `allowBuilds` policy.
- Added sanitized configuration examples, random local configuration bootstrap,
  secure ignore rules, CI checks/container builds, dependency-update configuration,
  [development instructions](docs/DEVELOPMENT.md), and
  [legacy migration notes](docs/LEGACY_MIGRATION.md).
- Preserved `app.py`, `questions.json`, and `requirements.txt` byte-for-byte.
  AST/JSON export verifies baseline hashes and retains **15** unique question-title
  drafts and **24** original roadmap suggestions with stable IDs, aliases, and
  provenance. Drafts have no invented prompt, answer, rubric, difficulty, or
  outcome. Unsupported marketing metrics and readiness-tree labels are excluded.

### Foundation verification results

| Check                                    | Actual result                                                                                                                                                                                                  |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend/backend dependency installation | Completed; exact direct pins, lockfiles, frozen reinstall, no peer incompatibilities.                                                                                                                          |
| Frontend startup                         | Native standalone production server and final Compose frontend started successfully.                                                                                                                           |
| Backend startup and liveness             | Native and final container API started; live `GET /health` returned HTTP 200 with the declared JSON contract.                                                                                                  |
| Database connectivity/readiness          | Real PostgreSQL 18.6 connected; native/direct/proxied readiness returned HTTP 200 at revision `0001_demo_foundation`.                                                                                          |
| Frontend lint/types/format               | `pnpm lint`, `pnpm typecheck`, and `pnpm format:check` passed.                                                                                                                                                 |
| Frontend unit tests                      | `pnpm test`: **4 passed**. Covers keyboard activation, valid/malformed responses, API failure, network failure, and retry state.                                                                               |
| Browser checks                           | `pnpm test:e2e`: **3 passed** with installed Chrome 154, including live container connectivity, intercepted 503 recovery, keyboard navigation, and mobile overflow.                                            |
| Accessibility/visual review              | Automated axe WCAG A/AA checks reported **0 violations**; desktop/mobile screenshots inspected. This is not a claim of complete WCAG conformance.                                                              |
| Frontend production builds               | `pnpm build` passed natively; final Docker frontend build passed on Node 24 LTS.                                                                                                                               |
| Backend lint/format/types                | Ruff check/format passed across backend/scripts; strict mypy passed for **28 files**, including tests/scripts.                                                                                                 |
| Backend tests                            | Final `pytest`: **27 passed**, using a migrated disposable real PostgreSQL database for integration cases.                                                                                                     |
| Migrations                               | Application upgrade succeeded. Disposable DB upgrade, downgrade/upgrade round-trip, and metadata drift checks passed; application data was never downgraded.                                                   |
| Live demo identity/persistence           | Two visitors through the frontend received distinct owned workspaces; CSRF reuse returned the same workspace; both survived an API restart.                                                                    |
| Compose                                  | Configuration validation, all image builds, and `up -d --no-build --wait` passed; frontend/backend/PostgreSQL healthy, cleanup running, migration exit code 0.                                                 |
| Contracts/legacy preservation            | OpenAPI drift, generated client regeneration, legacy seed reconciliation/hash checks, and unchanged-original Git diff passed.                                                                                  |
| Credential handling                      | Actual generated local credentials absent from **99** checked source/static-bundle files; local configuration/cache/runtime artifacts remain ignored. This is a targeted check, not a complete security audit. |

The backend verification script runs all backend gates and migration/contract
checks against `interview_prep_test`, guarding against the application database.
Final smoke checks verified frontend HTTP, liveness, real database/schema, and
same-origin forwarding. CI is configured but has not run on GitHub; no push occurred.

### Foundation decisions and fixes

- Use pnpm/uv without an additional workspace orchestration layer. Keep the single
  generated client in the frontend until another consumer needs a shared package.
- Select compatible stable tool versions rather than leave broken peer ranges:
  TypeScript 5.9 matches openapi-typescript's supported range, and ESLint 9 matches
  the plugins currently bundled by eslint-config-next.
- Fixed SQLAlchemy 2.1's missing asyncio/greenlet requirement, pnpm's changed build
  approval configuration, ESLint plugin incompatibilities/config warnings, ESM
  test-tool configuration, and formatting failures without weakening checks.
- Replaced the native `next start` command with the supported standalone entry
  point and static-asset preparation. Verified both that entry point and Docker's
  direct standalone server.
- Keep V1 archival source at the root and outside the V2 runtime. Its dependency
  failures and unsupported claims remain documented in
  [the audit](docs/CURRENT_STATE_AUDIT.md), not ported into V2.

### Foundation limitations at that time

- ESLint 9.39.5 is compatibility-pinned because the bundled React/accessibility/
  import plugins still exclude ESLint 10 in their peer ranges. The registry marks
  ESLint 9 deprecated; review this pin when compatible upstream plugins ship.
  The full configured rules and zero-warning lint gate pass.
- This is a verified local-development foundation. Public HTTPS ingress, trusted
  proxy/client-IP policy, production CSP, separate migration/runtime DB roles,
  account authentication, backup/restore, and release/security review remain
  later work. Behind an unconfigured gateway, the demo creation quota applies to
  the gateway peer address.
- Demo workspaces expire within 24 hours; cleanup runs hourly. There is no learning
  workflow or personal-data ingestion. Accounts, profiles, assessment, grading,
  AI providers, adaptive selection, roadmaps, analytics, jobs, and Project Defense
  are not implemented.
- GitHub-hosted CI, public deployment, performance/load tests, complete manual
  accessibility review, vulnerability audit, and real-model evaluation were not
  performed. Legacy curriculum still needs provenance/license and rubric review.

### Next task proposed at that time

Architecture phase 2: author and review questions/rubrics for one topic, then
implement a durable objective-assessment slice with owned persistence, saved
drafts, deterministic grading, duplicate-submit protection, and minimal results.
Keep accounts, ingestion, AI, and Project Defense within their later phases.

### Foundation local entry points

- Frontend: [<http://localhost:3000](http://localhost:3000>)
- Liveness: [<http://localhost:8000/health](http://localhost:8000/health>)
- Readiness:
  [<http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready>)

Stop with `docker compose down`; retain the database volume during ordinary
shutdown. Reproduce setup and checks using [README.md](README.md) and the
[development guide](docs/DEVELOPMENT.md).
