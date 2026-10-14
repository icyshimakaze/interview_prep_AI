# Question-based assessments

The account and isolated demo workspaces support configuration, starting an
attempt, saving responses, navigating, resuming unfinished work, submission,
review and paginated history. The runnable Streamlit launcher no longer contains
self-rating sliders or its trained-on-invented-labels classifier. Its original
bytes remain in a non-executable provenance fixture; see [legacy preservation](LEGACY_MIGRATION.md).

## Content and selection

The selector uses the latest reviewed, published, visible question version with
complete catalogue metadata. Supported types are `multiple_choice`,
`multiple_select`, `short_answer` (objective) and `written` (short conceptual).
Design and behavioral prompts remain available in the question bank but are not
selected for these assessments. Six supplemental authored questions in
`content/assessment-bank-v1.json` add three multiple-select questions, one MCQ and
two conceptual prompts to the existing 23-question catalogue. These are authored
practice materials, not an empirically validated psychometric instrument.

Category and difficulty are exact filters, and selected types form an inclusion
set. Selection orders candidates by the owner's previous allocation count
(ascending), then title and version UUID. Every allocation counts once,
including abandoned attempts; no predictive weighting or randomness is used.
Requesting more questions than are available is an explicit conflict, never a
silent difficulty fallback. An attempt contains 1–12 distinct versions. Stored
option positions preserve authored order (`authored-order-v1`). Retirement stops
new selection but does not change an existing attempt.

## State, persistence and API

Routes are under `/api/v1/account/assessments` and
`/api/v1/demo/assessments` with the same domain services and separate authentication.

| Method and path                         | Contract                                                                                  |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| `GET /options`                          | Actual eligible counts by category, difficulty and type; no questions or keys.            |
| `POST /`                                | Configuration plus UUID `submission_key`; atomically allocate versions/options and start. |
| `GET /?offset=0&limit=10`               | Owner's history, newest first; limit 1–50, bounded offset.                                |
| `GET /{attempt}`                        | Saved questions and responses; review only after completed submission.                    |
| `PUT /{attempt}/questions/{allocation}` | Revision, text or selected option UUIDs; replace editable draft.                          |
| `POST /{attempt}/submit`                | Revision; evaluate saved responses and atomically finalize all answers.                   |
| `POST /{attempt}/abandon`               | Revision; close unfinished work and retain saved responses.                               |

Configuration is frozen on the assessment; the attempt records policy/context
versions, start/deadline/completion timestamps, status and revision. An attempt
expires 24 hours after starting. GET computes `expired` without changing history.
Expired work can be inspected or abandoned; it cannot be edited/submitted. Each
owner can retain 100 attempts, with at most five unexpired unfinished attempts.
Account erasure and demo expiry/exit cascade through these records.
Individual assessment deletion and self-service account erasure are not implemented
in this phase; deleting a profile does not erase assessment history. Principal
erasure is an operator/future account-control action.

Responses store the allocation/version relationship, text (up to 10,000
characters via this API), selected options, save/submission timestamps, score,
maximum, correctness where meaningful, result kind, grading policy and evaluation
metadata. Metadata includes provider identity/version, rubric version,
evaluation timestamp and matched mock concepts. Submitted/skipped responses are
immutable. Blanks become skipped at final submission, with no invented score.

Start locks the principal and replays the same key/configuration to the same
attempt; different configuration with that key conflicts. Draft updates lock the
attempt and require the current revision, preventing concurrent lost updates.
Submission locks that attempt; repeat/concurrent submissions return the original
completed review without reevaluation or a duplicate progress event. A replay
cannot change responses. Failed evaluation rolls back the entire submission,
leaving the saved drafts and revision intact. Invalid states/options, foreign
allocations, unknown UUIDs and oversized bodies fail closed.

## Answer protection

Before completion, DTOs include only prompts, presented option IDs/text, owned
saved responses and timestamps. `review` is null; category results are empty.
Correct option flags/IDs, accepted answers, concepts and rubrics are never sent
by the assessment API before submission. The frontend also rejects premature
review DTOs. Keys are not present in frontend source or imported JSON. After
completion, review can disclose expected selections/accepted objective answers,
concepts and feedback. Question-bank practice separately unlocks concepts after
a submitted practice response; it never returns objective keys.

Every private query resolves the owner from verified credentials. Demo writes
require the exact allowed Origin and CSRF token. Client-supplied owner IDs are
rejected. Browser drafts remain in component memory only; responses and provider
errors are not logged or sent to an external service. Leaving a dirty page warns
about unsaved edits. A failed save blocks navigation and retains local input.
Revision/network errors offer a saved-state reload while keeping local edits.
After an ambiguous submission failure, retry is safe or reload confirms the
stored result. Draft data is discarded when the authenticated account changes.

## Scoring and provider boundary

`assessment-scoring-v1` defines every numerical value:

| Question               | Calculation                                                                                                                                                                                                                                                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MCQ                    | 1 iff the one selected option is the correct option; otherwise 0. Multiple selections are rejected.                                                                                                                                                                                             |
| Multiple-select        | 1 iff the set of selections exactly equals the correct set; otherwise 0. No partial credit; duplicates/unpresented IDs are rejected.                                                                                                                                                            |
| Objective short answer | `literal-v1`: strip surrounding whitespace from response and accepted keys, then compare exact case-sensitive strings; 1 for any match, otherwise 0. Unknown normalization versions fail closed.                                                                                                |
| Mock conceptual        | For each concept, take distinct ASCII alphanumeric words of length ≥4 after case folding. A concept matches if at least half of those words occur literally in the response. Empty word sets never match. Simulated points = `floor(4 × matched_concepts / max(1, total_concepts))`, maximum 4. |

The last rule is **simulation of lexical coverage**, not an AI judgment of
correctness, reasoning, honesty or competence. Negated statements or unrelated
word lists can score well; paraphrases can score poorly. UI and persisted
metadata label it `MockAIProvider`, `mock-lexical-v1`, `simulation`. It does not set
`is_correct` and is excluded from skill-evidence competence validation. No fake
ML, predictive readiness score or combined readiness percentage is produced.

The `EvaluationProvider` protocol accepts bounded prompt/response/concepts/rubric
data and returns a structured conceptual evaluation. The application installs
`MockAIProvider` by default, including for demo mode; no key or network call is
needed. A future account provider can be injected server-side at the dependency
boundary, with its actual identity/kind exposed in configuration. Demo evaluation
is pinned to MockAIProvider independently of the account provider.
No cloud provider is implemented or enabled here. Output is revalidated (including
already constructed model instances): integer score 0–4, bounded feedback,
allowed result kind matching provider provenance, unique concepts drawn only
from the actual rubric. Failures, invalid output and five-second per-response
timeouts return a sanitized retryable 503. The submission request has a bounded
75-second browser timeout to accommodate up to 12 sequential evaluations.

Category counts use the frozen questions and finalized responses. Objective
correct counts include only actual deterministic correctness; the denominator
includes skipped objective questions. Answered/skipped counts describe actual
responses. Conceptual points/maxima sum only evaluated conceptual responses,
with their evaluation kind displayed separately. Historical fixture scores are
retained with simulation provenance and excluded from deterministic category totals.
Categories are diagnostic slices of an
attempt, not claims about general mastery.

## Rollout and verification

Apply migration `0006_real_assessments` before starting this API. It preserves
existing assessment rows, adds optional configuration/grading fields and empty
selection arrays, expands the non-native enum check, and validates published
multi-select specifications and presented selections. Existing submitted answers
remain immutable. Downgrade refuses when new-format data exists; restore an
approved backup rather than discard retained responses to force rollback.

The explicit catalogue command now validates/publishes both manifests. It remains
transactional and idempotent, preserves editorial versions and retirement, and
does not run during requests or API startup. Without `--apply` it performs no
database writes. See [development setup](DEVELOPMENT.md) for native/Compose commands.

Tests cover scoring, selection/difficulty, persistence, navigation, objective and
conceptual review, skips, retry/concurrency, revisions, expiry, provider failure,
ownership/CSRF, disclosure, history and safe migration preservation/rollback.
The browser scenario uses a disposable database and exercises actual saved
assessment APIs alongside demo isolation and accessibility checks.
