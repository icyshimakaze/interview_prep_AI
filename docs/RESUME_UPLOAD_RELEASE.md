# Personal resume upload release — 24 October 2026

The user authorized publishing `cf08aa4` and final verification documentation to
`origin/rebuild/professional-v2`, then releasing the existing free services. Both
hosts now serve `cf08aa49cc02a311a4637c2ba5770f13056bbb82`. No default-branch merge,
force push, paid resource, hosting-variable change or production migration occurred.

| Component     | Release                                                                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Website       | [interview-prep-ai-icyshimakaze.vercel.app](https://interview-prep-ai-icyshimakaze.vercel.app)                                     |
| Resume upload | [Open Resume](https://interview-prep-ai-icyshimakaze.vercel.app/demo/resume)                                                       |
| Backend       | [interview-prep-api-icyshimakaze.onrender.com](https://interview-prep-api-icyshimakaze.onrender.com/health)                        |
| Render        | Free, Singapore; `dep-dbebdotg1s2s73f29oo0`, live                                                                                  |
| Vercel        | `dpl_HJMVCGL5ziQK86VkijTAbdnP9sMs`, READY; canonical alias verified                                                                |
| Database      | Existing Neon `neondb`, revision `0012_ai_context_reviews`, restricted runtime role                                                |
| CI            | [40099102208](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40099102208), all three jobs succeeded before release |

## User experience and privacy

Choose **Upload your resume** on the landing page or dashboard, or open Resume
from the workspace navigation. No sign-in is required for this temporary flow.
Upload a PDF with selectable text, up to 5 MiB and 20 pages. The application parses
the actual file on its server; it does not substitute the fictional resume.
Review, correct, reject, add or delete retained evidence. Uploaded files and the
fictional sample have separate labels derived from server provenance.

The raw PDF and full extracted text are discarded after parsing. Selected
excerpts, corrections and metadata remain in the owned database workspace.
Remove private contact details first. Access expires within 24 hours; physical
cleanup can be delayed while free hosting sleeps. **Exit and delete demo** erases
the workspace from active storage. Losing the session cookie loses access; there
is no cross-device login or recovery for this mode. Operator backups have separate
retention. See [resume processing and privacy](RESUME_PRIVACY.md).

Feedback remains clearly simulated. Temporary uploads offer no external AI
review, and resume content is not sent to xKiro. Account routes retain Clerk
verification and remain disabled on the hosted public profile.

## Reliability changes

A controlled check observed HTTP 502 before bootstrap and a 53.66-second Render
cold start. The frontend now waits up to 75 seconds on a read-only readiness probe
before sending one workspace-creation request. It does not automatically repeat
writes. Interview requests allow 30 seconds, preserve existing idempotency keys
and show safe timeout/network recovery guidance. A separate hosted request took
12.367 seconds in Chrome versus 178 milliseconds in Render processing.

The original Phase 24 creation timeout was not reproduced in a retained visitor
before this release, and the new live interview journey passed. Its historical
root cause is not proven; Vercel runtime-log reads still return 403. Free hosting
and network availability remain practical limits, and failures beyond the bounded
wait still require an explicit retry.

## Verification

| Check                        | Actual result                                                                                                                                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Complete backend gate        | 633 tests passed in 490.36 seconds; Ruff 210 files, strict mypy 197 sources, disposable migration down/up/drift, OpenAPI and legacy hashes/seeds passed                                                                                              |
| Frontend                     | 173 tests across 19 files, lint, strict types, production builds and repository formatting passed                                                                                                                                                    |
| Local Chrome                 | 25 tests passed in 1.8 minutes, including actual PDF upload/correction/reload, four widths, accessibility, visitor isolation and erasure                                                                                                             |
| Production container harness | Passed TLS, restricted role, non-root 512 MiB runtime, actual PDF parsing/upload/isolation/deletion, gateway/CSRF/quotas and cleanup                                                                                                                 |
| Exact release CI             | Frontend, backend and browser/container jobs all succeeded                                                                                                                                                                                           |
| Hosted HTTPS/API             | Canonical frontend and backend health/readiness 200; direct protected backend 403, unauthenticated resume library 401, accounts 403; exact CORS accepted and foreign CORS rejected                                                                   |
| Public scripts               | 12 landing assets and 16 scripts from public route HTML scanned; zero configured private-value matches; new upload/retention disclosure found                                                                                                        |
| Hosted first visitor         | Candidate context, questions, assessments, interview pause/follow-up/completion/review, Project Defense, roadmap/progress and personal PDF upload/correction/reload passed                                                                           |
| Hosted isolation and exit    | Foreign sample/uploaded resume, project and assessment reads returned 404. First UI deletion returned 204 and redirected home; the second visitor was erased by authenticated cleanup. Final Neon workspace/session/resume/version counts were zero. |

The main hosted suite returned **1 passed, 1 failed** in 9.5 minutes, including a
normal wait across the hourly quota boundary. Its failure was `getaddrinfo
ENOTFOUND` in the operator's Node API client when checking dashboard access after
the first UI deletion had already returned 204 and redirected home. The second UI
exit sequence did not run; its authenticated finally-cleanup returned 204. This
run is not counted as green. A separate **read-only Chrome follow-up passed** in
4.7 seconds: browser dashboard/library/workspace reads and the Node dashboard read
all returned 401, the public upload link was present, and no capability cookies
or JavaScript page errors remained. No new visitor was created. The first journey
captured 126 API responses, no 5xx responses and no JavaScript page errors; upload
returned 201 in 6.558 seconds. This verifies the listed application behaviors
without claiming the original combined test passed or that all transient network
failures are eliminated.

The first backend run found two invalid new expiry-test fixtures; those were
corrected to respect existing database constraints, then the complete gate passed.
The finishing-upload regression also checks a principal revoked during parsing.
The synthetic PDF is committed as binary to preserve its cross-reference offsets
on Windows checkouts. No production user data was exported for these checks.
The final release/documentation scan found zero configured-secret/pattern matches
in 480 tracked/new files and 23 local browser JS bundles. No actual dotenv file
is tracked or found by filename in reachable history. Final site/readiness checks
returned 200 and anonymous resume-library access returned 401 after cleanup.

## Remaining boundaries

Production Clerk accounts and real hosted xKiro remain disabled. Enabling them
still requires owned-domain/production Clerk setup and the documented account
export/erasure, identity deletion reconciliation and script-CSP work. The user
previously deferred a full-data backup/restore drill; this release does not run it.
Render still uses its existing TCP platform health check; explicit HTTP checks
passed. Automatic Render deploys remain off, and Vercel has no automatic Git link.
