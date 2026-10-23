# xKiro provider integration

Objective: make xKiro the recommended real provider using its OpenAI-compatible
Chat Completions API and the requested free Qwen models. Preserve the zero-key
mock default/public demo and optional Ollama/OpenAI providers. Do not deploy or
use real credentials/API calls during verification.

Scope: typed provider and model routing, strict response/domain validation,
bounded transport errors/retries, existing per-owner budgets, persisted opt-in
resume-evidence analysis and Project Defense answer feedback. Existing extraction,
objective grading, repository scanning and practice state transitions remain local.
Multimodal support is a bounded image-input adapter capability, not an unsolicited
new upload interface. No automatic remote resume sharing.

Configuration/security: XKIRO_API_KEY is backend-only SecretStr; fixed HTTPS base
origin, default reasoning/omni free IDs, per-operation routing and explicit paid
model authorization. Missing keys fail safely without fallback. Never read or
edit actual local secret files. Demo factory override precedes real configuration.

Database/API: versioned migration adds owned analysis receipts with bounded JSON,
input/provider/prompt/resource digests, concurrency fencing and expiry cleanup.
Account-only, server-resolved resource ownership and explicit sharing consent;
no caller owner IDs. Reuse completed validated results before budget/dispatch.
Resume revisions participate in cache identity; unique dispatch tokens fence both
success and failure writes against replacement receipts after invalidation/expiry.
Foreign-key cascades remove analyses with their source/owner. Existing APIs remain
compatible; additive routes and generated OpenAPI/TypeScript updates only.

Frontend: disclose xKiro and downstream third-party sharing before evaluation.
Optional resume-evidence and saved Defense-answer review show simulation/model
provenance, actionable errors and saved results. No browser credentials or provider
selection. Public-demo flow remains unchanged.

Verification: mocked HTTP success across operations and routing, malformed/truncated
JSON, refusals, limits, deadlines, rate limiting, missing keys, no paid fallback,
strict schemas, secrets, ownership, concurrent/repeated analysis, quotas, expiry.
Run backend lint/mypy/tests/migration and contract checks; frontend lint/type/tests/
build and appropriate browser regression. Update README, environment examples,
provider/deployment/privacy docs and PROJECT_STATUS.md with exact results/limits.

Order: provider/configuration; owned persisted opt-in analysis; minimal disclosure
and review UI; mocks/security tests; gates and documentation. No dependencies added.

Outcome: complete; implemented and locally verified with mocked inference.

Completed configuration/routing, validated Chat Completions and inline-image
adapter, opt-in owned persisted reviews, migration/cleanup, sharing UI and
documentation. Fixed late-response replacement races, keyboard focus transitions
and safe actionable AI error display. No real key was printed/changed and no live
inference/deployment occurred.

Final checks passed: 589 backend tests (29 xKiro and nine saved-analysis cases),
backend lint/format (198 files), strict mypy (186 sources), migration round trip/
drift and contracts/legacy checks; frontend lint/types, 158 tests across 18 files,
formatting and generated-contract equality; complete production builds and 25
browser/accessibility tests. The local production harness passed at 0011 with
mock AI, no AI credentials, TLS, restricted grants, idempotent seeding, secure
cookies/CORS/gateway/quota/cleanup checks. The ordinary native build target was
restored. Current owned temporary resources/credentials were removed; three older
test databases of unconfirmed origin were preserved on the pre-existing server.
Earlier resource-blocked attempts are superseded by these successful checks.

Operator key setup/migration and live provider/auth/hosted checks remain the
documented next steps, not something mocked tests can establish. No application
data migration, Compose image replacement, public deployment or push occurred.
