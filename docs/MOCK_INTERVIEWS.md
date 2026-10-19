# Running mock interviews

The account and recruiter-demo interview workflows implement the approved
[state-machine design](MOCK_INTERVIEW_STATE_MACHINE.md). Default configuration
uses `AI_PROVIDER=mock`; recruiter demo sessions always use MockAIProvider, even
when the account provider is OpenAI or Ollama. No AI key or model download is
needed for local development, automated tests or the demo.

## User workflow

Open **Interviews** at `/app/interviews` or `/demo/interviews`. Choose an owned
target job or general practice, one of seven interview types, adaptive/explicit
difficulty and main-question count. Inventory comes from published typed questions.
The current catalogue has sparse specialized coverage: Frontend supports one
medium prompt, System Design one hard prompt and Behavioral one easy prompt.
Unsupported configurations are disabled/rejected rather than silently changed.

Start, type an answer, and save or let the draft autosave. Submit locks the answer;
Skip retains any supplied text as skipped. Only one question is answerable at a
time. Feedback stays hidden until review. After a submitted main answer, optionally
ask for a follow-up, answer the prepared probe, or continue without it. Follow-ups
are limited to one slot per main and three per session, with no nested children.
An unavailable/cancelled generation consumes its slot and cannot insert a late turn.

Pause saves the current draft. **Save, pause and return** makes interrupted work
easy to find in history; reloading restores acknowledged server state. Active
sessions can also recover after an unplanned disconnect. Unsaved text exists only
in page memory. A stale draft is retained in memory for reconciliation on reload;
it is never silently applied to another tab's version. Lost command replies can
be retried with the identical command key/body. The UI can safely retry a confirmed
worker-only revision conflict after checking that the saved draft/cursor agree.

Complete after all main questions and any exposed follow-up resolve. End early
explicitly chooses whether to retain an unsubmitted draft, submit it, or skip it.
Both paths provide final review, including retained answers, actual answered/skip/
unasked counts, per-turn timing and evaluation coverage. Simulation/model-assisted
scores use the actual 0–4 scale and never establish readiness or competence.
Follow-up answers are unscored because generated probes have no reviewed rubric.

## Persistence and recovery

Migration `0007_mock_interviews` adds owned frozen candidates, generated follow-up
content, command receipts and durable work rows, and extends the existing interview
tables. Historical sessions remain `legacy` and read-only. Existing final answers,
scores and provenance survive. Populated downgrade refuses loss of new interview
data. Updated readiness requires this migration; apply it through the normal
development/release workflow before running the new API.

Main-answer submission commits the answer, evaluation row, work row and command
receipt in one transaction. AI evaluation starts afterward in a separate worker
transaction. No network request holds the command's database locks. Optional
provider failure marks evaluation unavailable; it cannot roll back a saved answer
or prevent navigation or final review. A failed current evaluation can be retried
explicitly once while active/paused, with a new evaluation version.

Two bounded worker loops run in the FastAPI lifespan by default. Pending jobs are
claimed using database leases and fencing tokens. A process restart recovers
undispatched work; an ambiguous interrupted dispatch fails safely rather than
automatically repeating a possibly billed request. Queue deadlines are 120 seconds,
leases 90 seconds, provider calls at most their configured deadline (maximum 60).
Finalization settles pending work within 120 seconds or returns partial evaluation
coverage. Startup scans settle overdue work without requiring the browser to remain
open. A stopped backend resumes processing when started again.

`INTERVIEW_WORKER_ENABLED=true` is the default. Integration-test fixtures explicitly
disable automatic loops and drive the same runner deterministically; the browser
harness enables the real loops. Disabling workers in a running app leaves work
queued until an enabled API process starts. No Redis, new dependency or external
AI service is needed.

Timing counts active answering intervals and excludes explicit pauses and provider
waits. It may include unobserved time away while disconnected. It is advisory,
never a scored time limit. Interaction expires after 24 hours, bounded by demo
workspace expiry. Expiration closes unanswered drafts without submitting them.
Account history is retained; interaction expiry is not data deletion. Demo exit
and expiry use existing erasure/cascade behavior.

## API and integrity

Routes under `/api/v1/account/interviews` and `/api/v1/demo/interviews` expose
options, owned history/detail, draft creation/configuration, start, draft save,
submit/skip, follow-up request, advance, pause/resume, complete/end, evaluation retry
and final review. Exact schemas are exported in `backend/openapi.json` and generated
TypeScript. The [design contract](MOCK_INTERVIEW_STATE_MACHINE.md) documents paths
and state guards. Mutation receipts identify command, operation, session and applied
revision; created turn/evaluation IDs are available in the fresh session view.
History omits the current answer/prompt; detail exposes only the current turn.

Every mutation uses a UUID command key and expected session revision. Same-key
replay returns the original receipt with current authorized session state; changed
payloads conflict. Ownership and nested session/turn membership are server-derived;
foreign IDs return 404. Demo mutations require existing origin/CSRF checks. Database
guards enforce immutable context/turn content/final answers, valid session/turn
transitions, main ordering, one open turn, unique follow-up parent and bounded slots.

Main selection uses frozen owned adaptive inputs, an explicit versioned interview-
type mapping, required role coverage and stable seeded tie-breaking. Only exposed
main questions count toward repetition history; generated children are excluded
before counting. Simulation/model-assisted results do not raise difficulty or
validate skills. No rubric dimensions are invented from aggregate provider scores.

Private follow-up content is never published into the global question bank. The
generator receives the submitted parent answer and bounded authored context through
AIProvider. Mock's authored probe is displayed with the actual parent and literal
answer excerpt; this is clearly simulated contextual practice. Optional remote
providers retain their own provenance and never silently fall back to mock.

Current-turn responses, dashboard/history and skill-evidence readers withhold
evaluation feedback during play. Review is a deterministic projection of saved
records, not another AI call. The privacy page discloses draft/answer retention,
optional sharing and timing limits. Credentials remain server-side.

## Verification

Backend integration tests cover persistence before provider failure, replay and
concurrent submission, all seven types, invalid ordering, ownership, pause/reload,
early end, expiry, contextual children and budgets, late-result cancellation, lease
recovery, retry versions, finalization deadlines, demo pinning/CSRF and erasure.
Frontend tests cover configuration, draft/retry recovery, paused controls, autosave,
pending generation, protected hints and partial review. The live Chrome demo flow
exercises saving, pause/reload/resume, follow-up, skip, complete and final review.
See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for exact executed results.

Live model quality and live Clerk verification remain operator checks. This phase
does not add voice/video interviews, code execution, secure proctoring, background
project analysis, account erasure/export controls or a calibrated scoring model.
