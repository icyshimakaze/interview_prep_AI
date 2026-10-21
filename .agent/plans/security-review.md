# Application security and privacy review

## Objective and scope

Review the actual V2 runtime, including existing uncommitted evaluation, Project
Defense and roadmap work. Produce `docs/SECURITY.md` with reproducible, ranked
findings; fix legitimate high-value issues; add meaningful regression coverage;
rerun checks and update project status. Preserve prior work and archival V1 files.
No push, deployment, live provider calls or real candidate-data ingestion.

## Review and affected components

Trace authentication and account/demo authorization through every route and worker;
inspect request schemas, SQL and deletion constraints, parsers and outbound HTTP,
AI prompts/output validation, frontend rendering/storage, environment/build/CI and
reachable Git history. Verify documented privacy claims against persisted data.
Investigate resource exhaustion as well as confidentiality and integrity.

Database changes: `0010_security_budgets` adds short-lived shared quota counters
and owner-scoped paid-evaluation receipts. No candidate backfill/rewrite. Active
budget/receipt rows prevent downgrade; cleanup removes expired rows. Runtime
readiness and migration expectations follow the new revision.
API changes: preserve contracts except justified security restrictions; keep
sanitized errors. Frontend changes: preserve saved drafts and accessible recovery.
Dependencies: no additions. The live advisory lookup demonstrated a Critical
certifi trust-bundle issue; update only that locked dependency to 2026.10.19.

## Implementation order

1. Inventory trust boundaries and existing checks; reproduce concrete failures.
2. Apply focused fixes and regression tests for confirmed security/privacy gaps.
3. Write severity-ranked findings, remaining deployment limits, retention and
   provider disclosure, and a coverage/evidence matrix.
4. Run the disposable PostgreSQL backend harness, frontend lint/types/tests/build,
   API contract generation, formatting and diff checks. Inspect generated bundles
   and Git history without emitting secrets. Record exact results and limitations.

## Acceptance and verification

No known Critical/High application finding left unexplained. Important fixes have
negative/failure-path tests. Relevant existing ownership, parser, AI, migration and
frontend checks remain meaningful and pass, or failures are explicitly recorded.
External identity/provider integration, production ingress and hosted CI are
reported as unverified unless actually exercised.

## Outcome

Confirmed and fixed pre-schema request exhaustion, unbounded paid retry costs,
loss of successful paid results on assessment rollback, raw exception logging,
HTTP decompression/slow JWKS gaps, repeated import abuse, misleading privacy copy,
PDF import isolation and normalized dot-only repository identifiers. Added a
baseline CSP and hostile provider-text rendering regression; Compose now honors
APP_ENV. Patched certifi's compromised-root advisory with a targeted lock update
and an HTTPX trust-store regression. No dependencies were added.

`docs/SECURITY.md` records ranked evidence, retention and remaining production
requirements. Final verification passed. An initial concurrent frontend /
backend run suffered resource-contention timeouts; the separate frontend run
passed all 123 cases using two workers, without changing assertions or timeouts.
The final backend harness passed all 510 cases, with one documented CA parsing
deprecation warning, plus all lint/type/schema/contract checks. The built
frontend passed a privacy-page/security-header HTTP smoke check; whole-repository
formatting and the scoped source/history/browser/log credential scan also passed.
Network access was resolved: the production npm audit checked 121 packages and
the post-fix OSV scan checked 43 locked PyPI packages, both with zero advisories.
Final exact results and the scoped credential scan are recorded in project status.
No push, deployment or application database migration was performed.
