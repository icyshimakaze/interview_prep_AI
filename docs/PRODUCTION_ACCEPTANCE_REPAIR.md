# Production acceptance repair — 30 October 2026

**Both failures were in the operator's acceptance runner. The application
runtime does not require a change for these findings.** Production remains
closed/demo; public GitHub signup has not passed live acceptance. The previously
created third account and its principal UUID are preserved.

## Callback mismatch: two authorizations in different tabs

The recovered production request metadata identifies two successful
`POST /api/auth/sign-in/social` requests on the same verified deployment:

| Event                                   | UTC timestamp, 29 October 2026 |
| --------------------------------------- | ------------------------------ |
| First initiation, HTTP 200              | 19:18:24.430                   |
| First pending state created             | 19:18:24.537                   |
| Second initiation, HTTP 200             | 19:20:12.573                   |
| GitHub callback, HTTP 302               | 19:20:24.534                   |
| Verified account created                | 19:20:26.025                   |
| GitHub account binding created          | 19:20:26.030                   |
| Application session bootstrap, HTTP 200 | 19:20:31.249                   |
| Account dashboard, HTTP 200             | 19:20:32.964                   |

These are 30 October in Asia/Calcutta. The callback's CDN request reference
matches the retained bounded server event `admission=public`, `reason=completed`
and the attempted deployment `dpl_8m3CbKEnmcD3oLtyd9k2LgJTqYsu`.

Read-only inspection recovered the original Android tab still on GitHub's
account-selection page. Its state hash exactly matches the **first** pending
database verification created at 19:18:24.537. That state expires at
19:28:24.537; it was not expired when the second callback succeeded. A separate
app tab's history contains a different authorization state and the return to the
dashboard. The successful callback consumed its state; the abandoned first state
remains.

The old runner called `waitForRequest` once and stored only the first state
hash. Its context-wide response listener saw the second tab's callback, compared
it with the abandoned first state, and reported `expected_state=false`. It then
waited until its first consent window expired instead of recognizing the second
observed authorization and adopting the returned app tab.

**Root cause:** a second real authorization, plus single-attempt correlation and
stale-tab instrumentation. No application CSRF/PKCE failure or expired state is
demonstrated. Historical callback hash and runner tab IDs were not persisted;
the reconstruction combines the two initiation timestamps, pending-state hash
match, separate retained navigation histories, callback/server request
reference, and database creation times. It does not invent an unavailable
historical hash or identify who opened the second flow.

The repaired observer records every app-origin initiation, its source-tab
reference, production deployment, timestamp, returned authorization state hash,
provider navigation and callback request references. It accepts only an exact
matching observed initiation/navigation/callback within four minutes. It handles
response-decoding order and adopts the correlated returned tab before accessing
the application. An unrelated or unobserved callback still cannot pass.

## Sign-out 422: request sent to GitHub

The retained resource timing in the abandoned GitHub tab records a `fetch` to
`https://github.com/api/auth/sign-out` at **19:22:23.554 UTC**, returning
**422**. The production request log contains no application `/api/auth/sign-out`
request in that window.

The old failure cleanup used `fetch(input.path)` from its stale `h.page`.
Reconstructing the executed helper gives method `POST`, JSON body `{}`, and
`Content-Type: application/json`; relative URL resolution, browser Origin and
same-origin session context belonged to **GitHub**, not Interview Prep. The
browser shared the app cookie jar across tabs, so `cookieState()` could see an
app cookie even though the selected document was still on the provider.

**Root cause:** wrong-origin relative fetch from the abandoned provider tab. The
422 is not an Interview Prep request-schema rejection. GitHub's internal
validation message/body was not retained and is not inferred. The app's pinned
wrapper separately rejects an empty/malformed JSON body with 422/`auth_input`
and a foreign Origin with 403; a valid owned `POST {}` signs out successfully.

The repaired helper constructs a fixed absolute app API URL, rejects a provider
tab before networking, rechecks the document origin inside the browser to close
a navigation race, and uses same-origin credentials/mode with redirects denied.
Cleanup requires a correlated app return and sends the exact `POST {}` contract.
It has no provider-origin fallback. Application CSRF, PKCE, linking, UUID and
JWT validation are unchanged.

## Focused verification

| Check                                                                              | Result                                            |
| ---------------------------------------------------------------------------------- | ------------------------------------------------- |
| Correlation, ordering, privacy, expiry, unsafe API paths and three-identity cohort | 15 Vitest tests passed                            |
| Isolated browser reproduction and origin/tab/race guards                           | 6 checks passed; no real provider request         |
| Pinned Better Auth/local PostgreSQL regressions                                    | 9 passed / 32 deselected; owned container removed |
| Frontend strict TypeScript and focused ESLint                                      | Passed                                            |
| Modified Python tests: Ruff/format and strict mypy with local source paths         | Passed                                            |

The pinned checks include separate states for two initiations, successful second
callback while the first remains pending, state/cookie/replay/CSRF rejection,
GitHub-only saved-work/isolation/revocation and returning identity behavior,
plus the valid/invalid sign-out contract. Tests use synthetic provider responses
and an owned disposable PostgreSQL database; they do not establish real live
signup.

Production inspection was read-only. It found schema `0013_better_auth`, three
auth users, preserved existing principal mappings and zero active owned test
sessions. The new runner's prior cohort includes **all three** identities and
their verified-email hashes. A fourth, genuinely new identity must have a
verified email distinct from all three. The last account is a returning account
and cannot satisfy the fresh-enrollment gate.

## Release decision

The exact runner and a single cutover runbook are being prepared for a separate
approval. No deployment, alias/configuration change, credential rotation,
migration, database cleanup or new provider login was performed by this repair.
Reuse the unchanged frozen application, existing infrastructure and compatible
rollback. Public signup can be declared LIVE only after the independent real
enrollment, ownership, persistence, normal Android restart, logout/revocation
and returning-login checks pass, followed by data and bounded callback-log
audits.
