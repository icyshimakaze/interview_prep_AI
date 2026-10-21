# Security and privacy review

Reviewed 21 October 2026; verification finalized 22 October 2026 against the actual
working tree, including the previously
uncommitted evaluation, Project Defense and roadmap features. This is a source,
configuration, history and regression-test review of the Next.js/FastAPI/PostgreSQL
application. It is not a penetration-test certification or authorization to expose
the local Compose stack publicly. Archival `app.py` is outside the V2 runtime and
must not be deployed as an alternative API.

## Portfolio reading guide

Documentation was cross-checked with the current implementation on 22 October 2026. This refresh preserves the dated review/findings below; it is not a new
penetration test or a renewed live dependency audit. Start with the
[current architecture](ARCHITECTURE.md), then inspect the findings and
[privacy/deletion inventory](#privacy-and-deletion-inventory). Report suspected
vulnerabilities using the [root security policy](../SECURITY.md).

Key design decisions are server-resolved ownership plus database constraints,
pre-parser/request/HTTP budgets, isolated expiring demo principals, transient raw
uploads, text-only generated-content rendering and optional server-side AI with
validated provenance. Simulation/model judgments never establish validated skill
performance. Project Defense performs static in-memory analysis without source
execution or provider dispatch.

Open production requirements include full account erasure/export and identity
reconciliation, trusted ingress/TLS/client IP handling, separate database roles,
backup/log retention and stronger parser OS isolation. The worker subprocess and
prompt boundaries reduce authority but are not complete sandbox/injection proofs.
The [testing guide](TESTING.md) distinguishes local/mocked/live browser coverage;
dated passing tests do not establish hosted CI, live provider quality or compliance.

## Findings and disposition

Severity reflects exploit prerequisites and confidentiality, integrity,
availability or financial impact. One Critical dependency finding and two High
application findings were confirmed and fixed in the working tree. Deployment
needs rebuilt images and migration `0010_security_budgets`. Absence of another
finding is not proof of absence.

| ID     | Severity      | Finding                                                                                                                                                                                            | Disposition                                                                                                                                                                                                                                                           |
| ------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SEC-14 | Critical      | Locked certifi 2026.7.22 trusted the emSign ECC Root CA - G3 affected by compromised intermediate keys (GHSA-6q48-6c7w-9gw2 / PYSEC-2026-4320). An on-path attacker could compromise outbound TLS. | Fixed: targeted lock/environment update to certifi 2026.10.19; actual HTTPX trust-store regression. Rebuild deployed backend images to consume the patched lock.                                                                                                      |
| SEC-01 | High          | JSON bodies were buffered/decoded before field limits or authentication, allowing unauthenticated memory/connection exhaustion.                                                                    | Fixed: pre-parser byte, time and concurrency limits.                                                                                                                                                                                                                  |
| SEC-02 | High          | Failed assessment submissions could repeatedly invoke paid evaluation; successful earlier answers were lost on rollback. Paid calls lacked shared spending limits.                                 | Fixed: durable result receipts, bounded retries, shared owner/global budgets and paid-assessment concurrency.                                                                                                                                                         |
| SEC-03 | Medium        | Generic error responses hid messages from clients, but Starlette re-raised exceptions to the server logger. Exception messages could contain candidate text or integration secrets.                | Fixed: outer exception boundary emits only a random request ID.                                                                                                                                                                                                       |
| SEC-04 | Medium        | AI/JWKS response byte checks occurred after automatic HTTP decompression. JWKS discovery had only an inactivity timeout, allowing slow-drip key discovery to hold the verifier lock.               | Fixed: identity encoding, rejection before reading encoded bodies, pre-append limits and a total JWKS deadline.                                                                                                                                                       |
| SEC-05 | Medium        | Import concurrency and saved-record caps did not limit repeated failed parsing/downloads or delete/reimport loops.                                                                                 | Fixed: persistent per-owner and global hourly import budgets, including failures.                                                                                                                                                                                     |
| SEC-06 | Medium        | Settings and authentication documentation incorrectly said real uploads and AI processing were disabled.                                                                                           | Fixed: disclosures now match current resume, repository and provider workflows.                                                                                                                                                                                       |
| SEC-07 | Medium        | Full account erasure/export and identity-provider deletion reconciliation remain unavailable; some referenced source records cannot be deleted individually.                                       | Open release limitation: provide an operator erasure process and lifecycle reconciliation before accepting sensitive production data. Existing granular deletion and demo erasure are verified; profile deletion must not be represented as account erasure.          |
| SEC-08 | Medium        | Parser subprocesses impose resource limits but share the service OS identity; they are not a filesystem/network sandbox against a parser exploit.                                                  | Partly hardened: PDF worker now uses isolated Python imports and an empty temporary cwd like the repository worker. Dedicated restricted parser execution remains a production deployment requirement. No demonstrated parser code-execution vulnerability was found. |
| SEC-09 | Medium        | Compose hardcoded development mode, ignoring an operator's APP_ENV; migration/runtime share one DB role and public ingress/TLS/backup controls are absent.                                         | Fixed environment override; default stays local development. Remaining deployment controls must be configured before public release.                                                                                                                                  |
| SEC-10 | Low           | Frontend lacked an explicit CSP for object embedding, document base changes and framing.                                                                                                           | Fixed baseline CSP. A tested nonce-based script policy with the configured Clerk instance remains future defense in depth.                                                                                                                                            |
| SEC-11 | Low           | GitHub repository suffix normalization allowed dot-only names after removing `.git`.                                                                                                               | Fixed: reject the normalized names. Fixed hosts/no credentials already prevented arbitrary-host SSRF.                                                                                                                                                                 |
| SEC-12 | Informational | JWT revocation is bounded by the accepted 60-second lifetime plus 5-second leeway, not instantaneous at Clerk sign-out.                                                                            | Documented; local suspension is checked per request.                                                                                                                                                                                                                  |
| SEC-13 | Informational | No credential match was found by the scoped source/history/browser-asset scan.                                                                                                                     | Evidence and limits below; this is not a comprehensive secret-scanner guarantee.                                                                                                                                                                                      |

## Concrete fixes and regression evidence

### SEC-14: compromised certificate authority trust

The live OSV check of all **43 locked PyPI packages** found one vulnerability,
reported under two alias IDs. The application's HTTPX integrations use certifi
for GitHub, JWKS and optional remote AI TLS validation. The affected bundle
therefore protects credentials, candidate data and authentication key discovery.
Exploitation requires an attacker with a compromised intermediate key and network
interception capability; this review found no evidence of an actual compromise.
The upstream advisory rates it Critical. The lockfile and local test environment
now use **certifi 2026.10.19**, without unrelated dependency upgrades. The regression
inspects HTTPX's actual trusted CA certificates and rejects the affected root.
Existing images keep their old trust bundle until rebuilt; this review did not
deploy or update running application images. [Reviewed advisory and patched range](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).

Production npm audit returned zero advisories for **121 dependencies including
optional packages**. The initial network/approval failure was resolved and the
lookup completed; post-update Python results are recorded in project status.
These advisory databases can miss new vulnerabilities and do not scan OS/image
packages, Python's system trust store or archived V1 dependencies.

### SEC-01: enforce limits before JSON decoding

Previously, a large body sent to `/api/v1/account/session`, even without a valid
token, reached FastAPI's body decoder before Pydantic could reject it. Field
`max_length` checks cannot protect that earlier allocation.

`core/request_security.py` now caps every non-upload HTTP body at **256 KiB**,
whether length is declared, absent, understated or the MIME type is unexpected.
It checks before appending each chunk, imposes a **10-second total read deadline**
and permits **32 concurrent buffered reads per API process**. Compressed request
bodies are rejected. Exact POST PDF/ZIP routes retain their authenticated bounded
streaming paths: **5 MiB/15 seconds** for PDFs and **10 MiB/20 seconds** for ZIPs,
with two PDF slots and two project-import slots per API process. Unsupported multipart input is rejected.

Tests: `test_security_boundaries.py` exercises unauthenticated oversized bodies,
chunked/false lengths, compressed uploads, read deadline and exhausted slots.
Gateway limits are still needed for connection floods, header sizes, proxy
buffering and aggregate traffic across API processes.

### SEC-02 / SEC-05: reserve resources durably

`core/quotas.py` uses atomic PostgreSQL upserts in independent transactions. The
reservation commits before expensive work, so failure, rollback, process restart
or deleting an imported record does not refund consumed budgets. No in-memory
counter is presented as a distributed limit.

| Work                                              | Limit                                                                       |
| ------------------------------------------------- | --------------------------------------------------------------------------- |
| PDF, ZIP, GitHub and example imports combined     | 10 per principal per UTC hour; 200 globally per UTC hour                    |
| Model-assisted evaluation/follow-up HTTP attempts | 60 per principal/hour; 200 per principal/day; 2,000 globally/day by default |
| Paid assessment submissions                       | Two concurrent submissions per API process                                  |
| Interview worker execution                        | Two loops per API process, existing durable work claims and leases          |

AI settings are `AI_OWNER_HOURLY_CALLS`, `AI_OWNER_DAILY_CALLS` and
`AI_GLOBAL_DAILY_CALLS`. Each dispatch reserves `1 + AI_MAX_RETRIES` units, the
maximum possible transport attempts; unused retries are deliberately not refunded.
These are request ceilings, not currency budgets. Set provider-side spend limits
for the actual configured model. All instances must share the quota HMAC key and
database; rotating the key resets the application buckets. Time windows can admit
bursts at boundaries. A global quota can be exhausted by abusive accounts, but
cost remains bounded and new dispatch fails closed. Simulation does not consume
provider quota. An unavailable quota database does not permit paid dispatch.

`modules/assessments/receipts.py` binds cached paid feedback to the owner,
assessment/question allocation, complete input, provider/model/version and prompt
version. It persists only validated results before the assessment transaction can
roll back. Resubmitting reuses successful results. A recorded failure permits one
further explicit submission; a started/ambiguous interrupted dispatch is never
automatically replayed. Input changes and new assessments still consume the shared
budgets. This does not claim exactly-once upstream billing: provider transport
retries remain bounded, and uncertain calls may have been billed.

Receipts store an input digest, attempt/state, expiry and validated feedback;
they do not store another raw prompt/answer copy. Feedback can quote answer text.
They expire after **48 hours** and are removed by the existing hourly cleanup.
Principal deletion cascades to receipts. Quota identifiers are keyed hashes,
contain no raw IP or answer text, and expire at the hourly/daily boundary; hourly
cleanup removes them. Removing imports does not erase active abuse counters.

Tests: `test_security_budgets.py` covers concurrent reservations, cross-session
enforcement, rollback resistance, global limits, expiry, receipt reuse, owner/input
separation, cascade erasure, failed/interrupted dispatch and populated downgrade
refusal. Existing assessment/interview suites cover concurrent commands, saved
drafts, revision conflicts, follow-up limits, leases and stale-worker fencing.

### SEC-03 / SEC-04: errors and external HTTP

Unexpected errors are caught before Starlette can re-raise them to Uvicorn. The
only application error log contains a random request ID, without exception text,
traceback, request body, URL, authorization header or provider body. Normal HTTP,
validation and database errors retain sanitized response envelopes, `no-store`
and `nosniff`. Tests use the default ASGI transport that re-raises server exceptions
and confirm a private sentinel reaches neither response nor captured logs.

HTTPX automatically decodes compressed bodies before yielding decoded bytes;
counting those bytes alone is insufficient to bound the decompressor's allocation.
AI and JWKS transports now request identity encoding and reject nonidentity
responses before consuming them. GitHub already did so. The tests use a response
stream that raises if read to prove early rejection. [HTTPX response decoding](https://www.python-httpx.org/quickstart/#binary-response-content).

JWKS discovery has a **3-second total deadline**, in addition to the read timeout,
a **64 KiB** response ceiling, bounded keys and failure cooldown. AI transport has
a configured **0.1–60 second total deadline**, **256 KiB** wire-response budget,
bounded structured output and **4,096 output-token** request cap. Post-send read
timeouts are not transport-retried. Redirects and environment proxy inheritance
are disabled. Provider/JWKS URLs are operator configuration or fixed hosts; token
headers and document content cannot select an endpoint. Ollama's operator-selected
origin can intentionally be local; users cannot supply it through an API.

## Review coverage

| Area                      | Actual implementation reviewed and evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Token/session validation  | `identity/verification.py`, dependencies and signed-token tests: RS256 only, trusted issuer JWKS, exact issuer/audience/azp, required integer temporal claims, bounded lifetime, forbidden token key URLs, pending-session rejection, cache rotation/outage and suspension. Custom API JWTs are not instant-revocation sessions.                                                                                                                                                                                                                                                                             |
| Authorization / IDOR      | Account routes derive the owner from verified issuer/subject; demo routes use hashed opaque cookie credentials and reject Authorization headers. Lists/details/mutations in profile, targets, resumes, questions, assessments, interviews, projects, roadmaps and progress filter by the resolved owner. Private parent/child relationships use compound owner FKs; missing/foreign IDs return 404. Existing integration suites exercise cross-account/demo IDs and forged owner fields.                                                                                                                     |
| API input                 | Unknown request fields are rejected, strings/lists/counts/revisions are bounded, UUIDs and enums are typed. The new pre-parser guard complements domain schemas. File limits are checked against actual streamed bytes.                                                                                                                                                                                                                                                                                                                                                                                      |
| PDF                       | MIME, signature and normalized display filename checks; reject separators/control characters; strict pypdf parser; encrypted/invalid PDFs rejected; 20 pages, 100,000 text characters, decoded-stream limits, 512 MiB worker memory and 15-second wall limit. Filename is never a disk path. No OCR, attachments, scripts, URLs or embedded actions are executed. Worker stdout is schema/provenance validated. Real PDF tests exercise limits and failure paths.                                                                                                                                            |
| Repository URL / SSRF     | Only public HTTPS `github.com/owner/repo` identifiers; no credentials/query/fragment/branch or arbitrary host. Fixed `api.github.com` and `codeload.github.com`, no redirects, tokens or inherited proxies; bounded metadata/download and total deadline; pinned commit provenance. No shell/git clone command. Job source links are validated HTTP(S) display links and never fetched.                                                                                                                                                                                                                      |
| ZIP / filesystem          | No extraction to disk. Reject absolute/traversal/drive/backslash/control/Unicode-ambiguous/reserved-name paths, duplicate/case-conflicting paths, file/directory conflicts, symlinks/special files, encrypted/unsupported entries and excessive expansion. Max 3,000 entries, 40 MiB declared expanded data, 256 KiB analyzed member, 500 analyzed files; process resource/time bounds defend malformed headers and parsers. Uploaded code/manifests/hooks are never imported, installed or executed. Tests execute the real trusted isolated worker on hostile archives.                                    |
| SQL / raw queries         | Application ORM filters bind input parameters. Runtime raw SQL is static health SQL and bound timezone lookup; content seeding uses a constant advisory lock. Dynamic database identifiers occur in trusted disposable-test tooling with safe generated names. No client input is concatenated into runtime SQL. Database trigger/constraint and migration tests protect ownership, history and cascades.                                                                                                                                                                                                    |
| XSS / generated content   | React text rendering for resume excerpts, repository facts, answers and provider output. No `dangerouslySetInnerHTML`, dynamic eval or Markdown/HTML execution sink was found. Generated text is not turned into links. External job links validate HTTP(S) and use `noopener noreferrer`. Added hostile-provider rendering regression. Baseline CSP, nosniff, frame denial and referrer policy apply at Next.js.                                                                                                                                                                                            |
| CORS / CSRF / redirects   | Exact allowed origins; no wildcard origin with credentials. Demo mutations require exact Origin plus the session-bound CSRF hash. Account APIs require an explicit bearer token and do not authenticate from cookies, so ambient-cookie CSRF is not the account API mechanism. Managed Clerk cookies remain SDK responsibility. Application redirects are fixed routes; Clerk live redirect behavior still requires integration verification.                                                                                                                                                                |
| Browser storage / secrets | API tokens obtained through Clerk and held in memory; no application localStorage/sessionStorage persistence of candidate records or tokens found. Account subject changes remount private UI; API/browser fetches use no-store. The Clerk publishable key and public API origin are intentionally public. Database/provider/Clerk secret keys remain backend/server configuration.                                                                                                                                                                                                                          |
| AI injection / leakage    | Versioned trusted instructions are separate from JSON-serialized untrusted input. No model tools, repository execution or arbitrary fetch capability. Explicit schemas reject unknown fields, oversized payloads, invalid scores/concepts/provenance and inconsistent aggregates before persistence. Output is still untrusted coaching: schemas do not prove factual correctness or defeat all semantic prompt injection. Prompts contain no credentials; their instructions/rubrics are not a secrecy boundary. Existing attack fixtures test role delimiters and requests to reveal keys or award points. |
| Background ownership      | Interview dispatch and finish recheck principal status/expiry and owned session/work/turn associations. Leases and tokens fence late results; cancelled/deleted work cannot repopulate results. External requests already dispatched cannot be recalled by a later deletion or suspension.                                                                                                                                                                                                                                                                                                                   |
| CI / builds               | Frozen dependency locks, digest-pinned images and commit-pinned actions; read-only GitHub contents permission; checkout does not persist credentials. No secret-valued build args; public Clerk key is intentional. Runtime containers are non-root and local ports bind to loopback. Production npm and all locked PyPI advisories were checked; OS/base-image packages remain outside this scan.                                                                                                                                                                                                           |

## Privacy and deletion inventory

| Data                                            | Sharing and retention                                                                                                                                                                                                                                                | Deletion behavior                                                                                                                                                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Raw resume PDF/full extracted text              | Request/worker memory only; no raw file store, OCR service or AI dispatch. Not forensic memory/swap zeroization.                                                                                                                                                     | Released after processing; no download endpoint or pending stored upload.                                                                                                                                |
| Resume label/hash/metadata/excerpts/corrections | Private database, no automatic account expiry. Excerpts can contain personal details.                                                                                                                                                                                | Owned resume deletion cascades versions/evidence unless referenced history blocks it; individual evidence can still be removed. Historical reasons/IDs are not retroactively rewritten.                  |
| Profile and job descriptions                    | Optional profile fields; versioned job context stays local. Source URLs stored, never fetched.                                                                                                                                                                       | Profile deletion affects profile only. Unreferenced jobs delete with versions; referenced jobs can be archived.                                                                                          |
| Repositories                                    | GitHub sees public repository identifiers and server requests. ZIP bytes/source bodies remain local and transient. Static output retains paths, hashes, declarations/facts and provenance; exclusions are not a complete secret scanner.                             | Owned snapshot deletion removes analysis, generated questions and defense sessions/answers. Account snapshots have no automatic expiry.                                                                  |
| Practice/assessment/interview/roadmap data      | Private persisted responses, evaluations and historical reasons. Optional account AI receives the submitted answer, question and authored criteria; follow-ups also include recent prompts. No resume/project/profile is sent by these current evaluation workflows. | Question-bank responses/bookmarks have deletion controls. Account assessment/interview/roadmap history currently lacks individual or full-account self-service erasure; retain this explicit limitation. |
| AI providers                                    | Default is deterministic mock; recruiter demo always uses mock. Optional OpenAI uses `store: false`; Ollama uses the operator-configured server. This is not a promise of zero upstream retention.                                                                   | Application controls cannot erase already transmitted provider data or third-party logs; operator/provider policies apply.                                                                               |
| Demo records                                    | Fictional seeded candidate; user-entered demo responses/imports can still contain real personal data. Interface asks users to use fictional data.                                                                                                                    | Session expires within 24 hours; hourly cleanup deletes the principal and owned records. Explicit demo exit deletes immediately. No public/shared demo owner.                                            |
| Logs / backups / identity                       | No application body/access logging in the provided backend container; error logs use request IDs. Clerk, gateways and operator backups have separate policies.                                                                                                       | Active-row deletion does not delete backups or the Clerk account. Configure retention, erasure handling and identity deletion reconciliation before production.                                          |

## Secrets review

Reviewed `.gitignore`, both Docker build contexts, examples, Compose, CI, frontend
environment references, reachable Git history including reflogs, and generated
browser assets. The read-only scanner checks exact current local secret values
without printing them, plus private-key, GitHub-token, AWS-key and provider-key
patterns. Initial scan: **382 working files, 541 historical blobs, 24 browser
assets, two nonempty local secrets; zero matches**. Final post-build counts and
test results are recorded in [PROJECT_STATUS.md](../PROJECT_STATUS.md).

Examples contain placeholders or explicitly disposable test credentials. No real
credential was identified for rotation in this scope. The scan does not cover
remote-only refs, unreachable/pruned objects, hosted CI logs, provider accounts,
external backups, arbitrary token formats or encoded secrets. Credentials must
never be copied into bug reports or audit output. If exposure is found later,
revoke/rotate it first; rewriting history alone does not revoke a credential.

## Rollout, recovery and verification

Apply `0010_security_budgets` after the existing migrations before running the
updated API. It adds quota and receipt tables without rewriting candidate data.
Readiness requires this revision. All application instances must use the same
database, quota key and budget settings, with hourly cleanup running. A downgrade
refuses while unexpired quota/receipt rows exist, so rollback cannot silently
refund budgets or discard retry state. Stop dispatch, let the maximum 48-hour
receipt interval expire, run cleanup, then downgrade if necessary. Back up the DB
and review the prior application's loss of protection before rollback. The
application database was not migrated as part of this review.

Relevant commands: `backend/.venv/Scripts/python.exe scripts/check_backend.py`
(or the documented uv equivalent), `pnpm lint`, `pnpm typecheck`, frontend Vitest,
`pnpm build`, `pnpm api:types`, `pnpm format:check`, `git diff --check` and the
scoped credential scan. The backend harness creates disposable PostgreSQL DBs and
checks lint, strict types, tests, migrations in both directions, metadata drift,
OpenAPI and legacy preservation. See current exact outcomes and any unavailable
checks in [PROJECT_STATUS.md](../PROJECT_STATUS.md).

Not established by this review: live Clerk account flows/revocation, live AI
accuracy or provider retention, live GitHub behavior, production gateway policy,
hosted CI, complete OS sandboxing, OS/base-image vulnerability status, forensic
deletion, load resistance or a guarantee against semantic prompt injection.
