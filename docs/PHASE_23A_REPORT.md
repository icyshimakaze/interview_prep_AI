# Phase 23A verification report

23 October 2026, Asia/Calcutta. No commit, push, service refresh or deployment.
Existing uncommitted work and actual dotenv files were preserved.

## 1. Existing integration found

The working tree already contained a real xKiro Chat Completions adapter, strict
Pydantic/domain validation, exact document grounding, free-model guards, typed
operation routing, consent UI, durable owner/global budgets, evaluation receipts
and retained-evidence/Defense feedback. Mock remained independent of account AI.
This phase completed verified gaps rather than replacing that architecture.

| Feature             | Verified integration after this phase                                                                                                                                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Resume analysis     | Existing opt-in account review of retained claims/excerpts. Exact quotations are grounded locally; summary can cover technical projects/experience. Not a full PDF review or evidence of competence.                                               |
| Job analysis        | New consent-based review of the latest saved description; grounded required/preferred/mentioned technologies, responsibilities in summary, concepts/interview topics in notes. Suggestions do not confirm requirements.                            |
| Interview questions | Existing deterministic adaptive main questions use saved profile/job/performance context; model-assisted follow-ups use the saved answer context. No generation loop or replacement of reviewed inventory.                                         |
| Technical feedback  | Existing rubric-based correctness/relevance/depth/completeness, strengths, gaps, improvements, answer structure and follow-up; strict score consistency.                                                                                           |
| Behavioral feedback | Existing behavioral rubric includes STAR structure, specificity, ownership, supported impact and reflection. No biographical verification.                                                                                                         |
| Roadmap             | Existing deterministic recommendations combine eligible results, resume evidence and target requirements. New optional AI activity suggestions use up to six saved unfinished topics/reasons and at most 600 minutes; preserve the scheduled plan. |
| Project Defense     | Existing safe static scanner and saved defense feedback remain. New optional generation shows six practice questions based on up to 30 cited static facts; does not execute source or replace a saved defense.                                     |

## 2. Changes implemented

- Absolute root `.env`, then `backend/.env` loading, independent of shell cwd;
  process environment overrides both. Actual secret files were not edited.
- Requested model variables plus backward-compatible legacy aliases; new
  backend placeholder example and backend-only Compose variable forwarding.
- Opt-in job, roadmap and project-question endpoints/UI through existing
  consent, safe errors, durable quotas and validated saved-result machinery.
- Additive `0012_ai_context_reviews` source columns and composite owner/source
  foreign keys, deletion cascades, one-source constraint and guarded downgrade.
  Existing rows and resume/Defense cache identities are preserved.
- Four concurrent remote operations per shared application HTTP client; deadline
  includes queueing. Budgets remain database-backed across processes.
- Synthetic opt-in smoke script, failure/regression tests, generated OpenAPI and
  TypeScript contracts, configuration/privacy/setup/deployment documentation.

## 3. Configured AI providers

`mock`, `xkiro`, `ollama`, `openai` remain supported. The effective native account
configuration selected `xkiro`; safe example/default production demo stays `mock`.
The factory always overrides the recruiter demo to deterministic MockAIProvider.
There is no silent provider or paid-model substitution.

## 4. xKiro model configuration

```dotenv
AI_PROVIDER=xkiro
XKIRO_API_KEY=
XKIRO_BASE_URL=https://api.xkiro.com/v1
XKIRO_MODEL_SMART=qwen/qwen3.8-max:free
XKIRO_MODEL_MULTIMODAL=qwen/qwen3.8-omni-flash:free
XKIRO_ALLOW_PAID_MODELS=false
```

The key above is intentionally empty. `XKIRO_REASONING_MODEL` and
`XKIRO_MULTIMODAL_MODEL` still work. In the same configuration source the new
spelling wins; explicit Python/process settings retain their normal precedence.
Routes remain server configuration. Free suffixes are preserved; non-free IDs
still require explicit operator model selection and spending authorization.

The request uses documented [Chat Completions](https://docs.xkiro.com/api/chat-completions/)
JSON-object formatting and an explicit schema in the prompt. [Structured-output
documentation](https://docs.xkiro.com/guides/structured-output/) says Qwen applies
the formatting as an instruction, so Pydantic and domain checks remain mandatory.
Unsupported parameters fail safely rather than being removed and retried blindly.

## 5. Real API smoke-test result

After **160 mocked provider/schema/config/rubric/concurrency tests passed**, ran
exactly **one** real request through `scripts/check_xkiro.py --live`:

- `qwen/qwen3.8-max:free`, harmless synthetic JSON acknowledgement only.
- 128-token cap, 60-second deadline, zero retries, no model fallback.
- **HTTP 200 in 3.86 seconds**; authentication, exact model identity, stopped
  assistant completion and strict JSON result validation succeeded.
- No resume, JD, repository, biography or saved answer was transmitted.
- No key, authorization header or raw provider output was printed or saved.

This verifies connectivity, authentication, model acceptance and parsing. It
does not establish evaluation quality, Omni compatibility, or future availability.

## 6. Automated verification

Final complete backend gate passed: **610 tests in 401.94 seconds**, fresh upgrade
through `0012_ai_context_reviews`, full downgrade/upgrade round trip, zero schema
drift, OpenAPI equality and legacy hashes/seeds. All databases created by these
verification runs were removed; existing application data was untouched.

- Focused corrected context/ownership/cascade/downgrade and smoke-script checks:
  **11 passed** on a disposable migrated PostgreSQL database.
- Backend Ruff lint and format: **205 files**; strict mypy: **192 source files**.
- Frontend: **162 tests across 18 files**, zero-warning ESLint, strict typecheck,
  repository Prettier check and final Next.js production build passed.
- Regenerated TypeScript contract was byte-equivalent on a second generation.
- Offline backend source-distribution and wheel builds passed.
- Tests block live HTTP and use fictional credentials. CI requires no xKiro key.
- The initial full run exposed a typo in a new test fixture (603 passed, one
  failed); that fixture was corrected and the focused rerun passed. Initial
  frontend spawn/cache permission failures were resolved through authorized
  local execution. No test, lint or type rule was weakened.

## 7. Security and privacy checks

- No actual `.env` files tracked now or found by filename in reachable Git
  history. Root/backend/frontend local env paths are ignored. This is a scoped
  tracking check, not proof that no credential was ever copied elsewhere.
- No configured xKiro key matches in the checked source or **23 browser JS
  bundles**; package artifacts were also checked. No frontend AI-key variable.
- Server account authentication and source ownership precede reads/dispatch;
  consent is bound to provider version and client-supplied owner IDs are rejected.
- Cache reuse, duplicate fencing, quotas, bounded explicit retries, deadlines,
  response/input limits and validated persistence remain in force. Ambiguous
  interrupted work is not automatically replayed.
- New review sources cascade saved receipts on deletion; receipts expire after
  30 days plus cleanup. They do not store raw input bodies, but generated text
  can quote private source content. Provider/backups have separate retention.
- AI generation requires a user action; React rerender does not repeat it. Errors
  preserve saved answers and source records. Simulation is explicitly labelled.
- Source scanning stays static; generated content is rendered as text, never run.

## 8. Known limitations

- Only the one Max-free synthetic request was live-tested in this phase. Other
  feature tests use network mocks; Omni/Ollama/OpenAI were not live-validated.
- Resume review covers retained evidence, not discarded full documents. Job
  responsibilities/topics are narrative structured fields, not a separate ontology.
- Roadmap suggestions cover six short topic labels, max 600 minutes; long labels
  are omitted. Project input is a bounded fact sample, not a complete code audit.
- AI results are suggestions, not predictive evidence or confirmed competence.
  Model syntax, latency and interpretation can fail; requests return safe errors.
- Concurrency is bounded per API client/process; shared quotas bound total
  attempts across replicas. Exactly-once upstream computation is not guaranteed.
- Large synchronous assessment batches can exceed the browser's 75-second wait;
  reload saved state before explicitly retrying. Existing interview work is durable.
- This phase did not repeat full browser/production-container harnesses or a live
  Clerk session; preceding phase results must not be presented as new results.
- Self-service account erasure/export and identity-provider deletion reconciliation
  remain existing release concerns; deleting a profile does not erase all history.

## 9. Remaining deployment blockers

Read-only local checks returned 200 for frontend, liveness and readiness, but the
existing API still reports **`0010_security_budgets`**, not the new source head.
No running service or existing application database was changed.

Before enabling these features in the running application: review/apply migrations
through **`0012_ai_context_reviews`**, refresh runtime grants, rebuild/recreate
backend services, and configure/test Clerk for account access. Compose needs
`--env-file .env --env-file backend/.env` when using the backend-local key.
Production should inject secrets through the backend environment store.

Public hosting, actual provider quota/retention review, HTTPS/origins/gateway
configuration, backups/restore and hosted account flows still require the release
procedure and separate authorization. The prepared public recruiter demo remains
mock-only. Nothing was pushed or deployed.
