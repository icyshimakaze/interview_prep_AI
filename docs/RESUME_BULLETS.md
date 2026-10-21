# Factual resume bullet options

Choose a few bullets matching your actual contribution and the role. These are
descriptions of repository capabilities, not proof of personal authorship. Be able
to explain the code and attribute AI/team assistance accurately. Do not claim a
public launch, adoption, improved interview outcomes or performance gains.

## Full-stack options

- Built an interview preparation workspace using Next.js, strict TypeScript,
  FastAPI and PostgreSQL, integrating versioned candidate context, saved
  assessments, mock interviews and explainable preparation plans.
- Implemented a credential-free recruiter demo with isolated expiring principals,
  fictional candidate data, CSRF-protected mutations and explicit active-data
  deletion, separate from authenticated account workspaces.
- Connected a typed FastAPI/OpenAPI contract to React workspace views with
  saved-draft recovery, accessible loading/error/empty states and regression-tested
  assessment and interview interactions.

## Backend and algorithm options

- Designed versioned assessment allocations and deterministic objective grading,
  preserving presented options, saved responses and grading provenance for review.
- Implemented an explainable question scheduler with per-skill difficulty
  transitions, exposure cooldowns, topic exploration and reproducible selection
  traces while excluding simulated/model grades from validated performance.
- Built a skill-evidence engine that separates resume mentions from eligible
  assessment evidence, resolves concept-level retakes and exposes source-backed
  preparation priorities without readiness predictions.
- Implemented durable interview evaluation using PostgreSQL work leases, fencing,
  command receipts and optimistic revisions, preserving submitted answers across
  provider failures and stale browser commands.
- Developed deterministic roadmap scheduling and persisted progress aggregation
  with preserved completion history and explicit provenance/sample-size rules.

## AI integration options

- Integrated mock, Ollama and OpenAI adapters behind a typed provider protocol,
  validating structured feedback against schemas and domain rules before storage
  and assigning provider/model/prompt/rubric provenance on the server.
- Separated fixed AI instructions from untrusted answer context and implemented
  bounded deadlines, safe retry rules and explicit simulation disclosures without
  presenting model judgments as validated competence.
- Added shared attempted-call budgets and durable validated-result receipts to
  bound optional provider work and reuse paid assessment results across grading
  rollback, without claiming exactly-once remote billing.

Only answer evaluation and interview follow-up generation use the optional remote
providers in current product workflows. Do not describe the application as using
AI for uploaded resume analysis, roadmap generation or repository analysis.

## Security and Project Defense options

- Built static public-GitHub/ZIP analysis with file/line citations and deterministic
  Project Defense prompts, rejecting unsafe archive paths/symlinks and avoiding
  repository extraction, dependency installation and supplied-code execution.
- Enforced private ownership in API queries and composite database references,
  with versioned migrations and guards protecting published content and submitted
  practice history.
- Hardened upload/provider boundaries with pre-parser body budgets, stripped-env
  parser subprocesses, bounded outbound responses, safe errors and text-only
  rendering of untrusted generated feedback.

Resource-limited subprocesses are not a complete OS sandbox. Do not claim a
penetration-tested, production-certified or privacy-compliant service. See the
[security review](SECURITY.md) for implemented fixes and open release requirements.

## Testing and repository engineering options

- Built a full-stack verification pipeline combining real PostgreSQL migration
  and ownership tests, React component tests and Playwright demo journeys, with
  mock AI and network guards preventing paid-provider calls in CI.
- Added GitHub Actions gates for backend lint/types/tests/migrations, frontend
  lint/types/tests/contracts, production builds and browser verification against
  the produced build artifact, with frozen dependencies and bounded diagnostics.

An optional quantified version, supported by the **22 October 2026** full local
run recorded in [PROJECT_STATUS.md](../PROJECT_STATUS.md):

- Verified an interview preparation application with **521 backend tests,
  134 frontend tests and 23 Playwright tests**, alongside lint, strict type,
  migration, contract and production/container build checks.

These numbers are executed passing test cases, not code-coverage percentages,
tests authored solely in one change, unique vulnerabilities fixed, users served or
performance improvements. Do not say you authored all tests unless that is true.

## Evidence map

| Claim                    | Inspectable source / verification                                                                                                                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full stack and contract  | [Architecture](ARCHITECTURE.md), [OpenAPI](../backend/openapi.json), [API clients](../frontend/src/lib/api)                                                                                                      |
| Demo/ownership           | [Authentication](AUTHENTICATION.md), [live two-visitor test](../frontend/tests/e2e/demo.spec.ts)                                                                                                                 |
| Skill evidence/selection | [Skill engine](../backend/src/interview_prep/modules/skills/engine.py), [adaptive engine](../backend/src/interview_prep/modules/adaptive/engine.py)                                                              |
| Durable interviews       | [Worker](../backend/src/interview_prep/modules/interviews/worker.py), [commands](../backend/src/interview_prep/modules/interviews/commands.py), [recovery tests](../backend/tests/test_interview_recovery.py)    |
| Providers/cost           | [AI protocol](../backend/src/interview_prep/ai/provider.py), [quotas](../backend/src/interview_prep/core/quotas.py), [assessment receipts](../backend/src/interview_prep/modules/assessments/receipts.py)        |
| Project Defense          | [Archive reader](../backend/src/interview_prep/modules/projects/archive.py), [analyzer](../backend/src/interview_prep/modules/projects/analyzer.py), [boundary tests](../backend/tests/test_project_analysis.py) |
| Plans/progress           | [Roadmap engine](../backend/src/interview_prep/modules/roadmaps/engine.py), [progress engine](../backend/src/interview_prep/modules/progress/engine.py)                                                          |
| Quality gates/results    | [CI](../.github/workflows/ci.yml), [coverage map](TESTING.md), [dated results](../PROJECT_STATUS.md)                                                                                                             |
