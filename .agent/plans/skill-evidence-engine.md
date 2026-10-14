# Explainable skill evidence engine

## Objective and scope

Build a deterministic, versioned, read-only skill matrix from owned profile labels,
current resume evidence, a selected target's latest requirements, and completed
assessment/interview history. Separate resume claims from demonstrated outcomes.
No ML, readiness percentages, new grading workflow, push, or deployment.

## Components and decisions

- Add a pure Python evidence policy, typed response schemas, bounded owned data
  adapters, and account/demo GET endpoints. Preserve existing source records.
- Use reviewed global vocabulary plus the existing finite lexical vocabulary;
  exact profile labels remain self-reported. Preserve source IDs and explanations.
- Required/preferred reviewed requirements override lexical mentions. Text-only
  mentions are explicitly unreviewed; no semantic understanding is claimed.
- Deterministic completed results alone can validate; simulation, self-review,
  model output, ungraded work and incomplete sessions cannot validate.
- Frontend: new Skill Matrix navigation, target selection, source disclosure,
  priority explanations, loading/empty/error/retry and stale-response protection.

## Database / privacy / API

No schema changes or migration: matrix is derived on request, never persisted.
No external sharing. Every private query uses the authenticated owner. Optional
target IDs are ownership checked; foreign/missing IDs return 404. Bound reads,
report omitted input rather than silently treating missing data as absence.
GET /api/v1/{account,demo}/skill-evidence?target_id=UUID. No client owner input.

## Order and verification

1. Document states, source eligibility, matching, precedence and sort policy.
2. Implement engine and source adapters; add concrete unit and ownership tests.
3. Generate OpenAPI/TS contracts; build and test matrix UI and authenticated wiring.
4. Run backend lint/format/mypy/tests/migration/contract checks, frontend lint,
   strict types, tests and build; browser/accessibility checks where available.
5. Review diff, record exact results and limits in PROJECT_STATUS.md.

## Outcome

Completed. Pure engine, owned account/demo reads, generated contracts and the
frontend matrix are implemented. No schema changes, new dependencies, source-data
mutations, commit, push or deployment. Required/Preferred consume reviewed existing
requirements; the production requirement editor and practice-creation workflows
remain separate work, disclosed in the UI and policy document.

Verification: 193 backend tests (including 50 new evidence tests), 60 frontend tests
and 23 Chrome browser tests passed. Backend/frontend lint and strict types,
production builds, migration round trips, schema/contracts/legacy checks, formatting
and diff checks passed. Desktop/mobile screenshots inspected; tested views had no
axe violations. Live Clerk credentials remain unavailable. See PROJECT_STATUS.md
for actual results and operational limits.
