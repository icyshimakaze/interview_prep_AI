# Mock-interview state-machine design

- Objective: review the existing system and specify a resumable, one-question-at-a-time
  typed interview covering all seven requested interview types before implementation.
- Scope: documentation only. Preserve all existing uncommitted adaptive/provider
  work. No application code, migration, generated contract, dependency or service changes.
- Review: interview models and SQL guards, assessment lifecycle/API, question-bank
  inventory, adaptive selection, AI contracts, identity/demo isolation, dashboard
  readers and skill-evidence eligibility.
- Design: explicit session/turn/work states, configuration and type coverage,
  bounded follow-ups, timing, endpoint payloads, transaction boundaries, durable
  evaluation, idempotency, revisions, ownership, recovery and final review.
- Database/API: document proposed additive migration, worker and contract changes;
  implement none. Explain compatibility with existing fictional sessions and guards.
- UI/privacy: define controls, progress and recovery semantics, server draft storage,
  disclosures and hidden review content. No new UI in this phase.
- Verification: inspect source and content, walk normal and failure transitions,
  specify future unit/integration/browser tests; run Markdown formatting and diff
  checks only. Runtime checks are not evidence for a documentation-only proposal.
- Deliverables: docs/MOCK_INTERVIEW_STATE_MACHINE.md and PROJECT_STATUS.md update.

Outcome: repository review and design completed in
docs/MOCK_INTERVIEW_STATE_MACHINE.md. Specifies all requested interactions and
contracts, truthful inventory limits, private follow-up storage, durable evaluation
and recovery, compatibility and a future acceptance matrix. PROJECT_STATUS.md
records design-only scope and the next phase. No application implementation.
Verification: Prettier for the three documentation files and git diff --check
passed; all nine design reference links resolve. Runtime checks were not run.
