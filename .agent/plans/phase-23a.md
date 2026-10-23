# Phase 23A — complete and verify xKiro

## Objective and scope

Preserve the existing uncommitted integration and working deterministic engines.
Close verified gaps: backend-local dotenv loading, requested model variable names,
bounded concurrent cloud calls, and opt-in JD/roadmap/static-project question reviews.
Keep mock the zero-key default and always force it for recruiter demo. No push,
deployment, actual dotenv edits, private-data live calls, or paid-model substitution.

## Components and contracts

- Settings: absolute root then backend dotenv paths; process environment wins.
  Accept requested model names and legacy names, preserving Python field names.
- Reuse provider schemas, consent UI, quotas and saved analysis receipts. Add owned
  source references for immutable job versions, roadmap plans and project analyses.
  Reviews suggest only; never mutate requirements, evidence, scheduled tasks or
  existing defense runs. Roadmap review uses bounded saved task reasons derived
  from assessment/resume/target context. Project questions use static facts only.
- Add migration 0012 preserving existing rows; refuse destructive downgrade when
  new-source receipts exist. Cascade source/owner deletion, retain 30-day cleanup.
- Add backend-only example config, current docs, generated contracts and status.

## Security and privacy

Resolve ownership on server before reading any source. Require consent bound to
provider version; no auto-dispatch on render. Strict Pydantic/domain validation,
bounded input/output/deadlines/retries, per-process concurrency and durable budgets.
Never display upstream errors, keys or raw private inputs. Check secret tracking
and ignore behavior using filenames/booleans only; preserve actual env files.

## Order and verification

1. Verify code/docs and official xKiro Chat Completions documentation.
2. Implement config/regressions, source-backed opt-in reviews and UI, concurrency.
3. Run mocked provider/schema tests first. Then ONE synthetic free-model request
   with zero retries, safe categorized reporting and no raw responses/headers.
4. Run backend lint/format/strict types/full tests/fresh migration round trip and
   drift/contracts; frontend lint/typecheck/tests/build; inspect final diff.
5. Record exact results, feature boundaries and remaining deployment blockers.

## Outcome

Complete. Backend: 610 tests, Ruff lint/format, strict mypy, fresh migrations,
downgrade/upgrade, schema drift, contracts and legacy preservation passed. Frontend:
162 tests, lint, strict types, formatting, generated contract equality and production
build passed. Offline Python wheel/source distribution built and passed credential
scans. One synthetic Max-free request returned validated HTTP 200 in 3.86 seconds.

No existing application database migration, service refresh, push or deployment
occurred. The running local API still reports revision 0010; current-source head
is 0012. Remaining release steps and feature limits are in
[the phase report](../../docs/PHASE_23A_REPORT.md).
