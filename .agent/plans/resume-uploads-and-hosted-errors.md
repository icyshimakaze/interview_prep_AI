# Resume uploads and hosted errors

## Objective

Resolve the reported hosted interview failure and let visitors upload and review
their own PDF resumes instead of being limited to the fictional example. Preserve
the no-login, no-credit simulated walkthrough and existing account security.

## Scope and decisions

- Reproduce the hosted timeout with request timing in one retained disposable
  visitor; diagnose the cause before changing deadlines or retry behavior.
- Account upload already exists but production Clerk is unavailable. The user
  explicitly selected temporary personal uploads. Visitor uploads use the existing
  isolated cookie capability, CSRF, expiry and erasure boundaries.
- No new authentication provider, paid resource, real AI request, quota bypass,
  full production data export, unrelated refactor or default-branch change.
- New release-branch push requires authorization for the concrete tested change.

## Affected components

Interview client/server query paths and error handling; existing resume parser,
owned persistence and routers; workspace resume UI/context; privacy/retention and
deployment documentation. Reuse existing parser limits and components.

## Database changes

None: existing resume records already belong to account or demo principals. No
schema change or backfill is required. Preserve the 0012 runtime revision.

## API changes

The new `/api/v1/demo/resume-library` operations use the demo capability. Exact
Origin and CSRF protect mutations; existing services enforce ownership, revisions,
parser bounds and import quotas. Historical `/demo/resumes/{id}` summaries remain
unchanged. Additive `is_sample` metadata comes from extraction provenance. Account
routes keep Clerk verification. Refresh principal state at upload completion so
expiry/suspension during parsing fails closed.

## Frontend behavior

Upload, parsing, empty, evidence review/correction and deletion states should work
with real PDFs. Clearly distinguish uploaded context from the fictional sample
and simulated feedback. Explain temporary retention before upload; preserve drafts
on failure. Provide actionable timeout messages without unsafe automatic repeats.

## Security and privacy

Keep production Clerk checks intact. Untrusted PDFs remain bounded to 5 MiB and
20 pages in the existing isolated parser, with raw bytes/full extracted text
discarded. No document text sent externally. Demo access expires within 24 hours;
physical cleanup may wait for the sleeping host. Explicit exit erases the owned
workspace. Test foreign-resource access, CSRF, expiry and deletion.

## Implementation order

1. Reproduce and measure hosted interview failure; inspect matching server paths.
2. Implement the diagnosed reliability fix and meaningful failure regressions.
3. Implement the agreed resume path with ownership/privacy tests and UI checks.
4. Run lint, strict types, tests, generated-contract drift and production builds;
   run disposable integration/browser and production harness checks as needed.
5. Review diff/secrets, update status/runbook, then obtain exact push authorization
   if release is needed. Deploy only within existing free-tier authorization.

## Verification criteria

Backend Ruff/mypy/pytest and migration/OpenAPI gates via
`python scripts/check_backend.py`; frontend lint/typecheck/test/build and API
generation; real browser synthetic PDF upload, retained evidence after reload,
foreign visitor rejection and erasure. Re-run failed hosted flow after an
authorized release, within normal visitor quotas. Record exact outcomes and any
external blockers without treating incomplete tests as passes.

## Progress

- Observed a 502 before bootstrap and a 53.66-second Render cold start. Once warm,
  one retained hosted visitor completed interview creation/start, pause/resume,
  follow-up, completion and final review; its authenticated deletion returned
  204 and subsequent dashboard 401. The original Phase 24 creation timeout was
  not reproduced. A later request took 12.367 seconds in Chrome versus 178 ms in
  Render, supporting transport headroom without claiming a proven origin for
  every historical timeout. Vercel runtime logs remain unavailable (403).
- Implemented a bounded 75-second GET-only readiness wait, single bootstrap POST,
  30-second interview deadlines and safe timeout/network recovery messages.
- Frontend: 173 tests passed across 19 files; lint, strict types and production
  builds passed. Full local Chrome suite: 25 passed in 1.8 minutes, including real
  PDF upload/correction/reload, four upload-screen widths, accessibility, foreign
  reads and workspace erasure.
- Production TLS/container harness passed, including real PDF upload/isolation/
  deletion inside the non-root 512 MiB Linux backend with restricted DB grants.
  Owned containers and ephemeral credentials were removed.
- Initial backend run: 630 passed, two new expiry fixtures violated existing DB
  checks. Corrected the fixtures without changing constraints and added a stale
  principal revocation regression. Final complete gate passed: 633 tests in
  490.36 seconds, disposable migration down/up/drift, OpenAPI and legacy hashes/
  seeds. Its disposable DB was removed. Ruff (210 files) and strict mypy (197
  sources) pass, including the updated harness. Whole-repo Prettier passes.
- Security checkpoint: zero configured-secret/pattern findings in 477 tracked/new
  files and 23 browser JS bundles; no actual dotenv paths tracked or in history.
- User authorized the normal release-branch push and existing free-tier release.
  `cf08aa4` was pushed and remote SHA verified. All three jobs in GitHub Actions
  40099102208 succeeded. Render `dep-dbebdotg1s2s73f29oo0` became live at that SHA;
  HTTP health/readiness and protected library passed before creating Vercel
  `dpl_HJMVCGL5ziQK86VkijTAbdnP9sMs`, now READY at the same SHA/canonical alias.
- Hosted first-visitor checks passed the complete practice journey and real PDF
  upload/correction/reload, upload accessibility and all four widths. Desktop/
  mobile screenshots were inspected. After the natural quota boundary, foreign
  uploaded/sample resume, project and assessment reads returned 404. First UI
  deletion returned 204/landing redirect; a Node post-delete read hit ENOTFOUND,
  so the combined suite is recorded as 1 passed/1 failed. The second UI exit did
  not run; authenticated finally-cleanup erased that visitor. A read-only Chrome
  follow-up passed the browser/Node 401 checks in 4.7 seconds without a new
  visitor. Final workspace/session/resume/version counts are zero.
- HTTPS/gateway/CORS/closed-account checks passed. Twelve landing assets and 16
  public-route HTML scripts had zero configured private-value matches; temporary
  upload and retention copy were found. No migration, host variable change,
  quota reset, paid resource, real AI request or production data export occurred.
