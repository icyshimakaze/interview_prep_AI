# Structured answer evaluation

## Objective and scope

Return explained, versioned written-answer feedback with general, technical and
behavioral criteria, strengths, improvements, missing concepts, a suggested
structure and follow-up. Preserve objective grading, owned answer persistence,
worker fencing, retry behavior and historical records. No deployment or push.

## Design

- Extend shared AI contracts and validation; use `answer-rubric-v1` and a dedicated
  evaluation prompt version. Scores use documented 0–4 anchors; unavailable
  judgments use null with a reason. Mock remains deterministic lexical simulation.
- Choose profiles from trusted question type, never instructions in an answer.
- Persist structured feedback in existing JSON columns, rubric/provider versions,
  model and completion timestamp. No schema change or migration is needed. Do not
  backfill invented judgments into historical results; additive nullable API fields
  identify them. Existing authored question rubrics retain their own version.
- Reuse review components across assessment/interview screens; show meanings,
  explanations, limitations and provenance alongside scores.
- Bound and validate output before persistence, including the existing interview
  payload byte limit. Preserve owner-scoped access and private answer retention.

## Order and verification

1. Shared rubric definitions, schemas, mock and provider instructions/validation.
2. Persistence adapters and additive review contracts; regenerate client types.
3. Shared feedback UI and parsers; backend and frontend regressions.
4. Document exact score semantics, compatibility and limitations; update status.

Run Ruff, strict mypy, backend tests (PostgreSQL harness if available), OpenAPI
drift, frontend lint/types/tests/build, formatting and diff checks. Add tests for
profile coverage, invalid output, determinism, persisted provenance and timestamp,
legacy reads, answer preservation and accessible explained feedback. Record exact
results and unavailable checks in PROJECT_STATUS.md.

## Outcome

Implemented all four steps with no dependency or database-schema changes.
Backend full regression passed 432 tests; final focused verification passed 166
tests, including three additions after the broad run. All 435 current tests passed
across these runs. Frontend passed 105 tests, lint, strict types and production
build. Backend lint/types, disposable migration round-trip and drift, OpenAPI and
legacy preservation passed. Documentation records mock limits and old pinned
session compatibility. Live provider quality and browser E2E were not exercised.
No commit, push or deployment.
