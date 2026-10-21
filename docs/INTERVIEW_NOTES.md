# Interview notes

These explanations describe the implemented repository, reviewed on 22 October 2026. Adapt first-person wording to work you can personally explain and attribute;
repository evidence cannot establish who wrote a change. There are no usage,
latency, learning-outcome or hiring-outcome claims here.

## 30-second explanation

Interview Prep connects target jobs, resume evidence, saved assessments and
explanation practice. The frontend is Next.js; a FastAPI modular monolith stores
versioned, owned records in PostgreSQL. Its deterministic selector explains why a
question was chosen, and Project Defense generates cited questions from static
repository inspection without executing code. AI feedback is optional and
schema-validated. A fictional, isolated recruiter demo works without API keys.

## 2-minute explanation

The problem is that preparation activity and evidence of understanding are easy
to confuse. A resume mention does not prove a skill; a simulated score does not
validate competence. This application keeps those meanings separate.

An account can save target jobs, upload a bounded PDF and review extracted claims.
The Skill Matrix combines source-backed mentions with eligible assessment results
and explains Practice, Validate or Maintain. Assessment questions are selected by
an inspectable policy using job relevance, difficulty and exposure history, then
frozen so later content changes do not rewrite an attempt.

Interviews save typed answers before durable evaluation. Database-backed work uses
leases and fencing; stale browser commands use revisions and idempotency keys.
Optional OpenAI/Ollama output is validated against schemas and domain rules, with
provenance assigned by the server. The default mock is deterministic lexical
simulation and is labelled accordingly. Objective grading and scheduling need no AI.

Project Defense is separate: a bounded GitHub/ZIP analyzer inspects source in
memory, retains citations and generates unscored explanation questions. It does
not install dependencies, execute code or claim authorship detection. Roadmaps
preserve completed work; progress charts require comparable persisted history.

The main engineering trade-offs are stronger auditability versus schema/guard
complexity, and deterministic behavior versus limited semantic understanding.
Tests include real PostgreSQL migrations and ownership boundaries, component UI
states and live demo browser journeys. Public deployment, full account erasure,
stronger parser sandboxing and rubric calibration remain explicit next work.

## Architecture walkthrough

Start with [ARCHITECTURE.md](ARCHITECTURE.md). Follow a browser request through
Next's same-origin rewrite to FastAPI, account/demo identity resolution, a domain
service and PostgreSQL. Open the pure skill/adaptive engines to show the rules;
then show where external integration enters through the provider boundary.

Use an interview submission to demonstrate the hardest lifecycle: commit answer
and work, claim a lease, release transactions before I/O, validate the response and
fence completion. Use a repository import to show the separate parser boundary.
Cleanup is a distinct hourly process; interview loops live inside each API process.
There is no Redis, message broker, vector database or microservice deployment.

## Data model

The current registry has 52 application tables (excluding Alembic). Principals
identify account or demo ownership. Context and question versions preserve source
history; attempts freeze allocations and presented options. Interview answers and
evaluations are separate so failure cannot destroy the answer. Project facts and
questions cite an owned snapshot. Roadmaps preserve versions and append-only
completion events. Quota rows and paid-result receipts survive grading rollback.

Explain composite owner/parent foreign keys, immutable published/submitted records,
and deferred history references. Some individual deletions can be blocked; profile
deletion is not account erasure. [Data model](DATA_MODEL.md).

## Adaptive algorithm

`adaptive-v1` is an editorial scheduler, not trained ML or a standardized adaptive
test. Cold skills start easy. Eligible distinct-concept success pairs raise the
target; failure pairs lower it. Exact filters, stable-ID cooldowns, concept spacing,
topic diversity and every-fourth exploration precede ranking. Ties use least recent
exposure and a seeded hash; choices retain reasons and score components.

Assessments select once at start. Interviews freeze initial evidence and add new
turn exposures while selecting main questions; current-session AI grades do not
update difficulty. Read [the exact formula and limits](ADAPTIVE_ALGORITHM.md).

## Project Defense design

Fixed GitHub hosts provide public commit archives; users can instead upload a ZIP.
The trusted worker reads accepted members in memory and never extracts or runs
them. It emits observed declarations and labelled inferences with file/line
citations. Deterministic prompts ask about decisions and verification. Private
generated questions remain unreviewed drafts. Defense answers are persisted but
unscored; they never establish authorship or skill competence.

## AI architecture

The async protocol has six typed operations. Only written-answer evaluation and
interview follow-up generation are connected to current remote-provider workflows.
Mock, Ollama and OpenAI share schema/domain validation and provenance. Resume/job
evidence, Project Defense and personalized roadmaps remain local deterministic
pipelines. See [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) and
[EVALUATION_RUBRIC.md](EVALUATION_RUBRIC.md).

## Security decisions

Server ownership checks complement relational guards; neither UUID secrecy nor
frontend navigation is authorization. Account JWTs have strict issuer/audience,
origin and lifetime validation. Demo cookie capabilities have CSRF/Origin checks,
expiry, isolated owners and deletion. Untrusted content stays data. Parsers have
byte/time/expansion/process limits; generated feedback renders as text. Keys stay
server-side. Resource limits are not a complete OS sandbox, and safe prompts do
not guarantee semantic injection resistance. [Ranked review](SECURITY.md).

## Hard technical challenges and trade-offs

These are challenges evidenced by code/tests, not an invented personal narrative:

- **Concurrency without lost answers:** command receipts, principal/session locks,
  revisions and fenced work protect retries. The UI tolerates bounded worker-only
  revisions but refuses changed turns/answers. More state and tests are required.
- **Honest evidence:** source eligibility and concept/channel supersession keep
  simulation and conflicting evidence from becoming false validation. Conservative
  exclusion reduces the number of results that qualify.
- **Cost across rollback:** independently committed receipts preserve validated
  paid feedback when another answer fails. Ambiguous dispatch can remain blocked
  rather than automatically charge again; exactly-once billing is not promised.
- **Safe useful source inspection:** in-memory archives and subprocess limits avoid
  project execution, at the cost of incomplete static coverage and skipped files.
- **History versus erasure:** immutable versions improve reproducibility but make
  deletion a graph operation. Full account lifecycle tooling is still missing.

## Failure modes to demonstrate

| Failure                                 | Implemented response / remaining limit                                                                                              |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Stale browser command                   | 409; reload rather than overwrite another tab. Bounded retries apply only to unchanged candidate state.                             |
| Provider timeout/refusal/invalid output | Safe failure; saved answer survives. Demo remains mock, with no silent fallback for accounts.                                       |
| API stops during interview evaluation   | Durable work/leases recover according to bounded rules; stale completions are fenced. Remote computation may already have occurred. |
| Later assessment answer fails           | Grading rolls back; committed drafts and validated paid receipts survive. Assessment evaluation is still synchronous.               |
| Sparse history                          | Explicit empty/table states; no invented chart or zero for missing evidence.                                                        |
| Unsafe/oversized archive                | Reject import without replacing an existing snapshot; no substitute fixture.                                                        |
| PostgreSQL/schema unavailable           | Readiness fails; quota failure prevents remote dispatch. Liveness remains a process check.                                          |

## Scaling and cost control

No production throughput or per-user cost was measured. Start with observability
that excludes candidate text: query timing, queue age, provider status/latency and
parser saturation. Multiple API processes can claim database work, but each adds
worker/parser concurrency; shared quotas are the cross-process limit. Separate
restricted parsers and an independently operated worker tier are plausible next
steps after measurement. Principal locks serialize one owner's work deliberately.

The default/demo has no model cost. Optional calls reserve possible retries against
database-backed owner hourly/daily and global daily budgets. Imports have shared
hourly attempt caps, including failed/deleted imports. Receipts reuse validated
assessment feedback. Timeouts, response/token limits and retry rules bound work;
provider-side currency caps are still necessary. [Quotas](../backend/src/interview_prep/core/quotas.py).

## What to improve next

First close production/privacy release gaps: account export/erasure and identity
lifecycle, trusted ingress, separated DB roles, backup retention and restricted
parser execution. Then expand reviewed content, calibrate rubric examples, provide
a requirement-review editor and make assessment feedback durable. Measure real
workloads before adding distributed infrastructure or learned recommendations.

## Interviewer questions and defensible answers

### 1. Why build this instead of another question list?

The implemented distinction is the evidence lifecycle: source claims, graded
answers, explanations and next activities remain linked and labelled. A question
list alone would not need frozen allocations, eligibility rules or durable answer
evaluation. This is a design rationale, not evidence of market adoption.

### 2. Why a modular monolith?

Ownership, attempts and work receipts need coordinated transactions. Domain modules
and pure policies provide boundaries without distributed transactions or a broker.
Deployment/scale simplicity is the intent; it has not been benchmarked against
microservices. See [app assembly](../backend/src/interview_prep/main.py).

### 3. Does the Next.js proxy secure the API?

No. It gives the browser a same-origin API route, but FastAPI verifies identity and
ownership independently. Calling the backend directly does not bypass those checks.
[Identity dependencies](../backend/src/interview_prep/modules/identity/dependencies.py).

### 4. What exactly does account token validation check?

RS256 with an operator-fixed HTTPS issuer/JWKS, exact audience and allowed `azp`,
required temporal claims, at most 60 seconds between issue and expiry plus five
seconds leeway. It rejects token-supplied key URLs and pending sessions. Local
principal status is checked on requests. This does not provide instant remote
revocation. [Verifier](../backend/src/interview_prep/modules/identity/verification.py).

### 5. Why can't one demo visitor read another's UUID?

The cookie resolves a distinct expiring principal. Queries include that owner,
and composite keys prevent cross-owner children. A supplied UUID never selects
the caller's identity. Foreign IDs return inaccessible results, and the live
two-visitor browser test checks this. [Demo test](../frontend/tests/e2e/demo.spec.ts).

### 6. Why CSRF protection for the demo but bearer tokens for accounts?

Browsers attach demo cookies automatically, so mutations require exact Origin and
a CSRF token. Account endpoints explicitly require an Authorization bearer token;
the demo cookie cannot authorize them. Demo routes reject Authorization headers
to avoid account-to-demo downgrade. [Auth contract](AUTHENTICATION.md).

### 7. Why database ownership constraints as well as service checks?

Service checks produce safe API behavior; composite owner/parent references protect
integrity if a future service accidentally links the wrong records. Immutability
guards also protect submitted history. They increase migration complexity and
require real PostgreSQL tests. [Model support](../backend/src/interview_prep/db/model_support.py).

### 8. Why not put everything in JSON?

Ownership, identity, answers, relationships and citations need relational constraints
and joins. Bounded JSON is useful for frozen policy input, structured feedback and
analysis summaries that must retain their versioned shape. It is not unrestricted
document storage. [Model registry](../backend/src/interview_prep/db/models.py).

### 9. What happens if an editor changes a question after an attempt?

Published versions and grading children are immutable. Attempts refer to frozen
versions and presented option order; new content needs a new reviewed version.
Existing attempts retain their context rather than being silently regraded.
[Question model](../backend/src/interview_prep/modules/questions/models.py).

### 10. Can resume keywords validate a skill?

No. The matrix separates mentions from performance, including negative or
aspirational matches. Confirmation reviews a claim; it is not a test result.
Missing resume evidence means absent source evidence, not inability.
[Evidence engine](../backend/src/interview_prep/modules/skills/engine.py).

### 11. How do conflicting skill results resolve?

Use the latest eligible observation per channel and canonical concept, with a
stable timestamp/ID tie-break. Any current weakness takes precedence. Repeated
success on one concept cannot supply the two-concept breadth rule. Simulation and
model-assisted results are excluded. [Eligibility](SKILL_EVIDENCE_ENGINE.md).

### 12. Is the adaptive algorithm machine learning?

No. It is a bounded deterministic editorial scheduler. Constants and transitions
are explicit and tested; they are not learned, probabilistic or calibrated to
interview success. A saved input/seed reproduces selection.
[Selector](../backend/src/interview_prep/modules/adaptive/engine.py).

### 13. How does it change difficulty?

Per skill, start easy without eligible history. Replay eligible observations;
two successes on distinct concepts at/above target raise one step, two failures
at/below target lower one step. Easier successes/harder failures reset the relevant
streak. One observation cannot move the target. [Exact rules](ADAPTIVE_ALGORITHM.md).

### 14. How do you prevent a weak topic from repeating forever?

Exclude five recent question identities, space two recent concepts, redirect after
two allocations in one topic and explore a least-covered topic every fourth turn.
If the filtered catalogue is exhausted, disclose cooldown relaxation or reject an
undersized batch. Exact filters are never relaxed. [Selection tests](../backend/tests/test_adaptive.py).

### 15. Does interview feedback adapt the very next main question's difficulty?

No. The interview freezes eligible starting evidence and its pool, then selects
each main question using updated exposures and coverage feasibility. Current
simulated/model feedback does not become validated performance.
[Interview selection](../backend/src/interview_prep/modules/interviews/selection.py).

### 16. What is objective scoring here?

MCQ/multiple-select uses exact set equality, with no partial credit. Literal short
answers trim surrounding whitespace and compare against authored accepted strings;
they do not use semantic similarity or general case folding. Written feedback is
separate and does not set objective correctness.
[Scoring](../backend/src/interview_prep/modules/assessments/scoring.py).

### 17. How is mock feedback different from a model grade?

Mock matches at least half the distinct concept words of four or more characters
and computes lexical coverage. Only completeness gets that labelled proxy; other
criteria are null. A remote model uses anchored criteria and a floored mean of
non-null scores. Neither is validated competence. [Rubric](EVALUATION_RUBRIC.md).

### 18. What prevents a provider returning plausible but invalid JSON?

Pydantic rejects unknown fields, bad types and bounds. Domain validation checks
criterion order/profile, concept membership/complements, spans and score arithmetic.
Provenance comes from server code. Valid prose may still be wrong; structural
validation is not semantic accuracy. [Validation](../backend/src/interview_prep/ai/validation.py).

### 19. How do you handle prompt injection?

Fixed instructions and JSON-serialized untrusted data are separated. Providers have
no tools, shell or database authority; output is validated and rendered as text.
This limits authority and executable effects, but cannot guarantee a model ignores
every adversarial instruction or interprets source text correctly.
[Prompts](../backend/src/interview_prep/ai/prompts.py).

### 20. What private data reaches AI?

Current optional account evaluation sends the question, submitted answer, concepts
and rubric; follow-ups include recent prompts. These workflows do not send a raw
resume, project or profile. Mock sends nothing externally. OpenAI requests set
`store: false`, which does not establish zero provider retention.
[Sharing inventory](SECURITY.md#privacy-and-deletion-inventory).

### 21. What happens on a provider timeout?

Safe error codes are exposed without upstream bodies. Saved drafts/answers survive.
Read/write/pool timeouts are not automatically replayed; bounded retries cover
connection establishment or selected transient statuses within a total deadline.
There is no silent mock fallback. [Transport](../backend/src/interview_prep/ai/transport.py).

### 22. Why save interview answers before evaluating them?

Provider availability should not determine whether a user's answer is durable.
The command commits the answer and work, then a worker evaluates outside the
transaction. Failed feedback remains distinguishable from an unanswered turn.
[Commands](../backend/src/interview_prep/modules/interviews/commands.py).

### 23. How do you stop a crashed worker overwriting a newer result?

Claims have lease tokens. Completion rechecks owned work/session state and token;
an obsolete dispatch cannot commit over a newer claim. Recovery is bounded.
Remote work may nevertheless have run twice; fencing gives persistence safety,
not exactly-once provider billing. [Worker](../backend/src/interview_prep/modules/interviews/worker.py).

### 24. What if two browser tabs submit at once?

Mutations carry revisions and command UUIDs, with server locks/receipts. Stale
candidate changes conflict. The UI retries only bounded worker-only changes when
the original turn and answer still match; it does not blindly rebase user edits.
[UI regression suite](../frontend/tests/interviews.test.tsx).

### 25. Can retries repeatedly charge for the same assessment?

Validated paid results are stored in independently committed receipts keyed by
owned attempt/allocation, input and provider/prompt identity. Completed receipts
are reused; failed dispatch has a bounded retry and ambiguous started work is
not automatically replayed. Receipts expire after 48 hours; this is not perpetual
deduplication. [Receipts](../backend/src/interview_prep/modules/assessments/receipts.py).

### 26. Does Project Defense clone and run the repository?

No. It fetches a public commit archive from fixed GitHub hosts or accepts a ZIP,
reads members in memory and performs trusted static parsing. No extraction,
dependency installation, hooks, builds, tests or uploaded source execution occurs.
[Archive handling](../backend/src/interview_prep/modules/projects/archive.py).

### 27. What stops SSRF, zip-slip and archive bombs?

Strict GitHub coordinates construct fixed-host URLs; redirects/credentials and
encoded responses are rejected. ZIP paths, duplicates, prefix conflicts, symlinks,
special files, sizes, counts and expansion ratios are checked before inspection.
Workers have time/memory bounds. Trusted DNS/TLS and parser-library flaws remain
outside a complete sandbox guarantee. [Import boundary](PROJECT_DEFENSE.md#security-boundaries).

### 28. Can the static analyzer prove someone wrote or understands the project?

No. A declared dependency or route-shaped expression is only a cited clue.
Inferred component roles are labelled. Questions help a candidate explain choices;
answers are unscored and generated questions never enter reviewed global inventory.
[Analyzer](../backend/src/interview_prep/modules/projects/analyzer.py).

### 29. How do roadmap regeneration and charts avoid fake progress?

Regeneration archives prior plans and preserves completion events. Stable activity
keys omit already completed work unless fresh evidence justifies it. Charts require
three comparable sessions on three UTC dates; interview series partition by
provider/model/version/rubric/profile/dimensions. Task completion is activity,
not competence. [Progress engine](../backend/src/interview_prep/modules/progress/engine.py).

### 30. Why test with PostgreSQL instead of SQLite?

Composite references, deferred constraints, triggers, locking, JSONB and migration
guards are PostgreSQL behavior. Disposable real databases test those invariants.
Pure functions stay unit-testable; component/browser tests cover different failure
boundaries. [Harness](../scripts/check_backend.py).

### 31. How do you know CI won't spend money on AI?

Runners force mock and clear inherited provider/Clerk settings. Pytest blocks real
HTTP before collection; protocol tests use in-memory transports. Component tests
reject unstubbed fetch and browser contexts block other origins. Hosted jobs receive
no repository secrets. This tests isolation, not live model quality.
[Test boundaries](TESTING.md).

### 32. What do tests actually establish, and what is missing?

The dated full run in project status passed 521 backend, 134 frontend and 23 browser
tests plus the documented gates. That establishes those cases, not full coverage
or production load/security guarantees. Live Clerk sign-in, semantic model quality,
public deployment and complete privacy lifecycle still require separate work.
[Executed results](../PROJECT_STATUS.md).

### 33. Can a user really delete all their data?

Demo exit/expiry removes its owned active graph. Accounts can delete certain
resources, but profile deletion does not erase assessment/interview/roadmap history;
referenced sources may be blocked. Full account erasure/export, identity reconciliation
and backup retention are open release work, not compliance claims.
[Deletion inventory](SECURITY.md#privacy-and-deletion-inventory).

### 34. What would you change before serving many users?

Resolve privacy/ingress/parser release gaps first, then measure query latency,
worker backlog, provider timing and resource saturation. Separate restricted parser
and worker operation if needed, make assessment evaluation durable and review
indexes/content capacity. There are no measured throughput or scale claims to defend.
[Architecture limits](ARCHITECTURE.md#operations-and-release-limits).
