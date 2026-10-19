# AI-provider architecture

- Objective: a typed six-operation AIProvider interface with deterministic mock,
  optional local Ollama and optional OpenAI Responses structured output. No key,
  model server or external network required for local defaults, CI or recruiter demo.
- Preserve: uncommitted adaptive implementation, objective grading, evidence
  eligibility, ownership, saved drafts and demo isolation. No new product workflow,
  upload-to-AI endpoint, database migration, dependency, commit or deployment.
- Components: backend `ai` package (schemas, prompts, policy validation, providers,
  HTTP transport, factory); assessment compatibility adapter; application lifecycle;
  settings/env/Compose/CI; privacy disclosure and architecture documentation.
- API/database: no schema migration. Keep assessment response contracts and
  simulation/model-assisted provenance. Six operations are internal typed services;
  only existing conceptual assessment evaluation is connected to a user workflow.
- Security: bounded untrusted data in user messages only; fixed trusted prompts;
  no tools, URL following, code execution or document instructions. Server sets
  provenance; validate schemas, spans, concepts and roadmap limits. No raw provider
  errors, documents or secrets logged/returned; explicit remote opt-in and disclosure.
- Failure policy: bounded deadline/response size and transient-only retries; no
  silent cloud-to-mock fallback. Missing optional configuration yields a safe
  unavailable error on use, never blocks mock/demo. Invalid provider name rejected.
- Tests: protocol conformance, all operations for all implementations using fake
  HTTP, determinism, limits, schema/domain/provenance rejection, timeout/cancellation,
  transient/nontransient retries, unavailable configuration/server, injection-like
  text, demo pinning and existing assessment failure/ownership regressions.
- Verification: Ruff, strict mypy, focused and full PostgreSQL backend checks,
  frontend lint/types/tests/build for disclosure updates, contracts, formatting and
  preservation. No real paid API requests or model downloads.

Outcome: implemented all six operations across mock, Ollama and OpenAI; integrated
conceptual assessment evaluation, configuration and sharing disclosures. Added 80
passing AI tests. Broad backend run passed 375 tests with one existing migration
timeout; that unchanged test passed on focused rerun, along with migration roundtrip,
contracts and preservation checks. Ruff, strict mypy, frontend lint/types, 81 frontend
tests, production build and Compose validation passed. Exact results and remaining
integration/live-provider limitations are recorded in PROJECT_STATUS.md.
