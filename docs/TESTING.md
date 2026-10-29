# Automated testing and quality gates

## Current release verification boundary

The [30 October production attempt](FINAL_LAUNCH_2026_10_30.md) reached a hosted
READY build and passed Android provider-policy/anonymous-security preflight, but
its independent callback-correlation gate failed. Saved-work, normal-restart,
returning-login and revocation checks were not reached for that new account. Do
not treat the demo suite as proof of public signup. The source retains focused
[Better Auth](../backend/tests/test_better_auth.py),
[social policy](../backend/tests/test_social_auth.py), and
[callback diagnostics](../frontend/tests/oauth-diagnostics.test.ts) tests. These
are separate from human-controlled production consent and device acceptance.

The supported pipeline tests the current V2 application with PostgreSQL, the
production frontend and deterministic MockAIProvider. It does not require Clerk
keys, model downloads or paid AI credentials. The archived V1 runtime is outside
the supported test target; its source hashes and preserved content are checked.

## Run the full suite

From the repository root, install the frozen dependencies and start PostgreSQL as
described in [CONTRIBUTING.md](../CONTRIBUTING.md), then:

```sh
pnpm --filter @interview-prep/frontend exec playwright install chromium
pnpm check
```

`pnpm check` invokes `scripts/check_all.py` through the backend uv environment.
It runs gates sequentially to avoid backend/parser and browser/JS worker
contention: backend lint/types/tests/migrations/contracts, frontend
lint/format/types/tests/generated contracts, production build, connectivity smoke
and all Playwright tests. It fails on the first unsuccessful gate. Test failures
are not replaced by snapshots or skipped assertions.

Use `pnpm check --api-port 8100 --frontend-port 3100` to leave normal services
running. Windows can use installed Chrome or Edge with the process environment
variable `E2E_BROWSER_CHANNEL=chrome` or `msedge`; CI uses bundled Chromium.
PowerShell syntax is `$env:E2E_BROWSER_CHANNEL = 'chrome'`.
If Windows reserves an alternate port, choose another pair such as 18100/13100.
Custom-port checks leave an ignored build targeting that test API; run `pnpm build`
with the normal backend configuration before a subsequent native `pnpm start`.

## Focused commands

| Purpose                                           | Command from the repository root                                              |
| ------------------------------------------------- | ----------------------------------------------------------------------------- |
| Complete backend gate                             | `pnpm check:backend`                                                          |
| Backend lint/format/mypy only                     | `uv run --project backend python scripts/check_backend.py --phase lint`       |
| Full pytest, fresh migrations and contracts       | `uv run --project backend python scripts/check_backend.py --phase tests`      |
| Fresh migration round-trip and metadata/contracts | `uv run --project backend python scripts/check_backend.py --phase migrations` |
| Frontend lint / strict types                      | `pnpm lint` / `pnpm typecheck`                                                |
| Component and API-client tests                    | `pnpm test`                                                                   |
| Repository formatting                             | `pnpm format:check`                                                           |
| Production frontend build                         | `pnpm build`                                                                  |
| Build and isolated browser suite                  | `pnpm check:e2e`                                                              |
| Browser test selection                            | `pnpm check:e2e -- --grep "isolated fictional demo"`                          |
| Use an already built matching frontend            | `pnpm check:e2e --skip-build`                                                 |
| List browser tests without servers                | `pnpm --filter @interview-prep/frontend exec playwright test --list`          |
| Container packaging, no deployment                | `docker compose build`                                                        |

For a selected pytest file, use the `backend/` working directory and a migrated
disposable `TEST_DATABASE_URL` ending `_test`. Direct pytest deliberately fails
if a DB test has no such database; it does not silently skip integration coverage.
Most pure unit tests need no PostgreSQL. Never point that variable at personal data.

## Coverage map

These are behavioral suites, not a claim of 100% code coverage or exhaustive
correctness. New rules should extend the relevant suite rather than add tests
that repeat implementation details.

| Backend area                                                            | Evidence                                                                                                                                                         |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Models, relational ownership, immutability and cascades                 | `test_relational_model.py`, `test_auth.py`, `test_demo.py`, domain integration suites                                                                            |
| Migrations, preserved populated data and unsafe rollback refusal        | `test_migrations.py`, `test_*_migration.py`, `test_projects.py`, `test_personal_roadmaps.py`, `test_security_budgets.py`; harness round-trip and `alembic check` |
| Authorization, tokens, CSRF and foreign IDs                             | `test_auth.py`, `test_demo_workspace.py`, all account/demo domain API suites                                                                                     |
| Skill evidence eligibility and deterministic priority                   | `test_skill_engine.py`, `test_skill_performance.py`, `test_skill_api.py`                                                                                         |
| Question filtering, pagination, answer protection and self-review       | `test_question_bank.py`, `test_question_content.py`                                                                                                              |
| Objective assessment scoring, drafts, concurrency and failure           | `test_assessments.py`, `test_ai_assessments.py`, `test_security_budgets.py`                                                                                      |
| Adaptive selection, exposure, ties, bounds and source eligibility       | `test_adaptive.py`, `test_adaptive_integration.py`                                                                                                               |
| Interview state machine, recovery, cancellation and worker fencing      | `test_interviews.py`, `test_interview_recovery.py`                                                                                                               |
| Evaluation schemas, domain consistency, provenance and malicious input  | `test_ai_validation.py`, `test_evaluation_rubric.py`, `test_ai_providers.py`                                                                                     |
| Roadmap generation, scheduling, progress and history                    | `test_planning_rules.py`, `test_personal_roadmaps.py`                                                                                                            |
| Repository analyzer, URL/ZIP/path bounds and non-execution              | `test_project_analysis.py`                                                                                                                                       |
| Project Defense ownership, state/revision rules, replay and persistence | `test_projects.py`                                                                                                                                               |
| Request/HTTP limits, quotas and test isolation itself                   | `test_security_boundaries.py`, `test_security_budgets.py`, `test_test_isolation.py`, `test_smoke_contract.py`                                                    |

Backend paths above are under `backend/tests/`. Constraint, concurrency and
migration cases run against real PostgreSQL, not SQLite substitutes. The parser
suites execute the actual trusted worker on local hostile/invalid fixtures.

| Frontend area                                                      | Evidence under `frontend/tests/`                                                                                            |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Profile, target job, resume/evidence and filter forms              | `candidate-profile.test.tsx`, `profile-form.test.tsx`, `target-jobs.test.tsx`, `resumes.test.tsx`, `question-bank.test.tsx` |
| Navigation, truthful empty states and accessible workspace content | `workspace.test.tsx`, `skill-matrix.test.tsx`, `account-workspace.test.tsx`                                                 |
| Loading/errors/retry and availability                              | Domain view suites, `service-status.test.tsx`, `planning.test.tsx`, `demo-workspace.test.tsx`                               |
| Assessment UI, scoring labels, drafts and review                   | `assessments.test.tsx`, `evaluation.test.tsx`                                                                               |
| Interview UI and saved state                                       | `interviews.test.tsx`, `evaluation.test.tsx`                                                                                |
| Demo bootstrap, expiry, CSRF erasure and retry                     | `demo-workspace.test.tsx`; actual two-visitor browser journey                                                               |
| Repository / defense and roadmap / progress                        | `projects.test.tsx`, `planning.test.tsx`                                                                                    |

## Browser coverage and isolation

The live demo journey exercises landing-page **Try Interactive Demo**, candidate
dashboard, target-job context, fictional resume evidence and skill analysis,
question filters, saved objective and conceptual assessments, mock interview
pause/resume/follow-up/skip/review, actual local repository analysis and Project
Defense, roadmap generation/completion/preserved history, and progress derived
from those persisted records. A second browser proves foreign IDs remain private
and demo exit erases that visitor's credential. Named Playwright steps identify
each part of the journey in the report.

This uses exactly two demo creations; the application's real creation/import
limits remain enabled. The live journey has no retry because its two creations
consume the hourly network quota. A retry would obscure the original failure with
quota errors. Other CI browser tests may retry once, and any flaky outcome remains
visible in the report. Contexts and fictional data are isolated from application
data. No test-only HTTP route or authentication bypass is added.

Other browser cases cover public navigation, health connectivity, mobile overflow,
keyboard/focus behavior and automated axe checks. Intercepted API failures and
layout-only workspace fixtures are labelled in their source. Account profile,
target, PDF/evidence and skill forms additionally have desktop/mobile axe checks
using actual components rendered to static HTML directly in the browser test
process. Those static fixtures have no React handlers and do not establish an
authenticated Clerk session. Their interactions are covered by component tests;
account ownership/CRUD is covered by backend integration tests. Live Clerk login
and real account browser workflows remain a separate integration check.

`scripts/check_browser.py` builds the app, creates a new random database, migrates
and seeds only that database, starts the API and standalone frontend, checks real
connectivity, runs Playwright and removes its owned processes/database in `finally`.
It refuses occupied ports and a reused build with a different API rewrite. The
frontend always uses same-origin API forwarding. A browser suite can run without
first running Vitest or preparing manual fixture files.

## No paid AI in automation

- The runners override inherited/local provider and Clerk settings, force
  `APP_ENV=test`, `AUTH_ENABLED=false`, `AI_PROVIDER=mock` and empty remote provider
  keys/models. No configuration file is rewritten.
- Pytest blocks standard synchronous and asynchronous HTTPX network transports
  before test collection or network access. Provider protocol and failure-injection tests use explicit
  in-memory transports or local spies with dummy credentials. PostgreSQL connections
  are allowed. Application evaluation and all browser sessions use MockAIProvider.
- Component tests reject unstubbed fetch. Browser contexts block requests outside
  the configured local frontend origin. The API runs only mock AI in the harness.
- CI references no repository secrets, does not run `pull_request_target`, and has
  read-only repository permissions. No paid provider or live GitHub import is used.

## CI and diagnostics

[The GitHub Actions workflow](../.github/workflows/ci.yml) has three useful gates:
backend lint/tests/migrations, frontend lint/types/tests/build, and browser/container
packaging after both pass. It uses frozen installs, commit-pinned actions and a
digest-pinned PostgreSQL service. A checksum-pinned actionlint release checks
workflow syntax and expressions in CI. The browser job downloads the exact production
build from the frontend job; it does not rebuild a different app for testing.
The container build step builds images without running or publishing them.

Backend and frontend JUnit reports are retained for seven days. Failed browser
runs retain the HTML report, JUnit, traces, screenshots and the two local server
logs for seven days. The intermediate frontend build is retained for one day.
Artifact paths are explicit; `.env` and the rest of `.cache` are not uploaded.
Use fictional data only: traces contain DOM, requests and answers.

Locally, results are in ignored `.cache/*-junit.xml`, `frontend/playwright-report/`
and `frontend/test-results/`. Open browser traces with Playwright's trace viewer.
The latest executed counts, platform and limits are in
[PROJECT_STATUS.md](../PROJECT_STATUS.md). Local verification does not assert that
a hosted GitHub run has passed. Repository branch-protection rules and enabling
private vulnerability reporting are maintainer settings, not changes this workflow
can silently apply.

Dependabot proposes weekly package, lockfile, image/digest and action updates.
Scheduled configuration must reach the default branch to activate there; the
current V2 branch must be merged before its new schedule applies. Review updates
with the same gates; there is no automatic merge. See
[GitHub's artifact documentation](https://docs.github.com/en/actions/tutorials/store-and-share-data)
and [Dependabot version updates](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-version-updates)
for the underlying hosting behavior.
