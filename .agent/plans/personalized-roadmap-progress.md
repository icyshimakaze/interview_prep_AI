# Personalized preparation roadmap and progress analytics

## Scope and acceptance

Build deterministic account/demo roadmaps from the selected owned target and its
priority/requirements, current resume/profile skill evidence, assessment/interview
performance, Project Defense practice, explicit weekly time and optional interview
date. Every item exposes topic, reason, priority, objective, effort, activity and
status. Complete/reopen are persisted; regeneration archives earlier versions and
never deletes their tasks or completion events. Preserve preceding uncommitted work.
No AI call, readiness score, outcome prediction, push or deployment.

## Design

- Reuse the skill matrix's conservative validation policy. Resume and simulated /
  model feedback can suggest validation activities but never establish strengths.
  Unscored defense answers/skips guide discussion tasks without competence claims.
- Add nullable bounded roadmap input/item JSON plus an idempotent generation UUID
  in versioned migration 0009. Preserve old seeded rows unchanged. New versions
  archive the previous active generated version; already-completed recommendation
  keys are omitted, with history visible and reopen available. Quota 50 generations.
- Serialize mutations with principal and roadmap locks, use expected revisions,
  and append completion events with fresh immutable identity on each recompletion.
  Reads/writes, target selections and histories enforce server-side ownership.
  Demo retains Origin/CSRF and simulation labels. Existing dashboard compatibility
  remains; new roadmap/progress pages use dedicated APIs.
- Separate pure recommendation/aggregation rules, bounded owned SQL loaders,
  persistence commands, contracts and UI. No extra dependencies or source text
  sharing. Persist only source references and concise reasons/counts, no answer or
  resume body copies. Scheduling respects the weekly budget and queues work that
  does not fit before the interview date, with explicit limits.
- Progress reads completed persisted attempts and latest evaluation per answer,
  not synthetic progress events or averages from mixed scoring systems. Objective
  assessment accuracy includes submitted deterministic grades only. Interview
  series require comparable structured rubric/provider/model/profile versions;
  simulations/failed/legacy-unscaled results are disclosed and excluded. Charts
  require at least three comparable sessions on three distinct UTC dates.
- Show categories, repeated missed concepts with basis/counts, active/history
  roadmap completion, recent assessment/interview/defense sessions, validated
  strengths and validation gaps. Reuse matrix eligibility for strengths. No chart
  for sparse data; show counts/tables and explanations instead. Cap read windows
  and disclose truncation; withhold validation if matrix inputs are partial.
- Account/demo UI: target/budget/date form, rationale, completion/reopen, explicit
  regenerate, preserved version history; progress loading/empty/error/retry states.

## Verification and delivery

Test scheduling/order, partial/missing inputs, no fake validation, real aggregation,
score/provenance separation, latest-result selection, no chart below thresholds,
regeneration/history/reopen/replay/revisions, ownership, CSRF, migration preservation
and UI states. Run Ruff/format/mypy, disposable PostgreSQL harness with migration
round-trips, OpenAPI/client generation, frontend lint/types/tests/build and format /
diff checks. Update PROJECT_STATUS.md and feature documentation with exact results,
limitations and next task. Application database remains outside verification.

## Outcome

Implemented versioned deterministic recommendation/weekly-capacity rules, preserved
roadmap generations and completion events, owned account/demo APIs and UI, and real
persisted progress aggregates with provenance-separated trends and sparse-history
chart suppression. PostgreSQL timezone data avoids a new Windows timezone package.
Migration 0009 is additive and refuses a populated lossy downgrade. No AI calls.

Verification: all 489 backend cases covered across a 488-pass full run plus the
final 23-pass focused run (one new test fixture's expired ORM state was corrected
to match production sessions). Ruff 174 files, strict mypy 164 files, disposable
migration round-trips/drift, OpenAPI and legacy checks passed. Frontend 122 full
suite tests plus 10 final focused tests, lint/types and production build passed.
Application rollout, live providers/Clerk and browser E2E were not run. See
PROJECT_STATUS.md and docs/ROADMAP_PROGRESS.md for limits, retention and next work.
