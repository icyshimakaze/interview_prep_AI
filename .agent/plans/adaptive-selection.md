# Adaptive question selection

- Objective: replace assessment allocation ordering with a versioned, explainable,
  deterministic policy; cover cold starts, eligible success/failure, job relevance,
  diversity, recent repetition, sparse history and finite inventory.
- Scope: pure selector, owned database adapter, assessment-start integration,
  persisted explanations, algorithm documentation and tests. Existing explicit
  category/type/difficulty filters and frozen in-progress attempts remain intact.
  No ML, new provider, interview workflow, UI redesign, dependency or deployment.
- Components: new `modules/adaptive` package; reuse skill evidence eligibility and
  selected-job importance; assessment service/schema/query; generated API contract.
- Database: no schema changes. Store versioned selection explanations alongside
  existing configuration JSON; retain compatibility with old configurations.
- API: optional owned `target_id` on assessment configuration; additive selection
  explanation on attempt response. Existing requests remain valid; foreign targets
  return 404. Server derives identity, evidence and question visibility.
- Frontend: retain existing assessment flow; generated types updated. No new form
  or live turn-by-turn interview UI in this engine phase.
- Security/privacy: only owned evidence and global/owned released content; no raw
  answers/resumes in selection traces, no external calls. Bound inventory/history;
  disclose history windows, withhold performance adjustment on partial evidence.
- Tests: pure policy scenarios and invariants, real database integration including
  ownership, mock exclusion, idempotent replay, exact filters and persisted traces.
- Order: document rules, implement pure policy/tests, adapter and integration,
  run gates, inspect diff, update status with actual results and limitations.
- Verification: Ruff/format, strict mypy, full backend disposable-DB harness,
  OpenAPI/types generation, frontend lint/type/tests/build, formatting/diff checks.

Outcome: implemented and documented. All 250 existing backend regressions passed
in the broad run; its one new-test fixture failure was corrected, then all 46
adaptive tests passed on the final implementation. Disposable migration round
trips, schema drift, contracts, legacy hashes, backend lint/types, frontend
lint/types/79 tests/build, formatting and diff checks passed. No new browser UI
was introduced; browser E2E/live Clerk were not rerun. No commit/push/deploy.

Review decisions: repeated failures may lower difficulty even on one concept;
successful progression requires distinct concepts. First-timestamp difficulty
ties use the easier level. Exposure ordering retains batch positions, and the
absolute allocation count preserves exploration after history-window truncation.
The next task is curriculum/policy review and a real interview-workflow integration.
