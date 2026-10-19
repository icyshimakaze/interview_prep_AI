# Implement mock interviews

- Objective: deliver the approved persisted interview workflow, backend and frontend,
  integration tests, final review and a GitHub push on the existing branch.
- Preserve: prior adaptive/provider work, legacy fictional sessions, assessment
  behavior, ownership, immutable final answers and default mock/no-key operation.
- Order: additive migration/models and state contracts; frozen adaptive selection;
  transactional commands/idempotency; durable evaluation/follow-up worker; owned
  API and review; frontend configure/play/resume/review; regression and browser checks.
- Database: new revision after 0006, frozen guards, legacy-compatible nullable
  extensions and owned candidate/content/command/work tables. Populated downgrade
  refuses loss. No application database migration or deployment without authorization.
- Security: server-derived ownership, demo CSRF/mock pinning, bounded untrusted
  input/output, answer commit before provider dispatch, no hidden rubric leakage.
- Verification: state/business and PostgreSQL integration tests for recovery,
  ordering, follow-up bounds, concurrency, ownership, failures and migrations;
  frontend tests, lint/types/build, contracts, formatting and browser demo checks.
- Delivery: update design/status with actual behavior/results, review diff and
  secret exposure, commit the related prior/current work and push to origin.

Outcome: implemented the complete backend/frontend and migration 0007. Answer
submission commits before provider work; demo is pinned to mock. Full backend
regression: 396 passed. Final focused run: 37 passed, including all 22 new interview
cases and two final regressions. All 398 tests passed across these runs. Ruff145,
strict mypy137, frontend90, Chrome23, lint/types/build, contracts and migration
roundtrip/preservation passed. Exact results and remaining limits are recorded in
PROJECT_STATUS.md. GitHub delivery uses the existing rebuild/professional-v2 branch
with the user's explicit push authorization; no deployment or application migration.
