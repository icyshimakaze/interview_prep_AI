# Project Status

Updated: 2026-10-19 (Asia/Calcutta).

## Complete mock interviews (current phase)

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

### Limits and next task

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

### Verification

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

### Limitations and next task

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

### Verification

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

### Limitations and next task

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

### Verification

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

### Verification

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

### Verification

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

### Limits and next task

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

### Verification

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

### Rollout limits and next task

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

### Rollout limits and next task

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

### Limits and next task

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

- Frontend: [http://localhost:3000](http://localhost:3000)
- Liveness: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)

Stop with `docker compose down`; retain the database volume during ordinary
shutdown. Reproduce setup and checks using [README.md](README.md) and the
[development guide](docs/DEVELOPMENT.md).
