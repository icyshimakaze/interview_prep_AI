# Clerk integration code release — 25 October 2026

The user authorized committing/pushing the local Clerk changes and updating the
existing Vercel website. The code is deployed at
**https://interview-prep-ai-icyshimakaze.vercel.app**. Hosted account authentication
remains disabled: the user has only the `vercel.app` address, and no production
Clerk instance/domain/keys have been configured for this public profile.

## Release identity

| Item                   | Verified result                                                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub branch          | `rebuild/professional-v2`                                                                                                                       |
| Code commit            | [`c6dfda14be38fbb85cc9e267a43d2ef510794b51`](https://github.com/icyshimakaze/interview_prep_AI/commit/c6dfda14be38fbb85cc9e267a43d2ef510794b51) |
| CI                     | [40125359511](https://github.com/icyshimakaze/interview_prep_AI/actions/runs/40125359511), all three jobs successful before deployment          |
| Vercel project/account | `prj_wsxEcvVC17paXs5pco4K9eHwWKgd` / `team_vyOtLBqMjk5sQ9DTmzCcbwiN`                                                                            |
| Deployment             | `dpl_53VkStbwKUFnBnoigpBv28hhJNeN`, production, READY, Singapore                                                                                |
| Source and alias       | Deployment-ID and canonical-hostname reads both confirm the exact code SHA; no alias error                                                      |
| Build                  | Vercel build log reports completion in 10s                                                                                                      |
| Rollback candidate     | Previous production deployment `dpl_HJMVCGL5ziQK86VkijTAbdnP9sMs`                                                                               |

The initial deployment request returned 403 for expired/missing Vercel account
scope access. The user completed Vercel's prescribed authorization recovery, then
the identical request succeeded through the same connection. Consent URLs and
credentials are not stored in this report. GitHub API polling reached its public
rate limit; the fresh public run page confirmed every named job completed
successfully before deployment.

## Scope and preservation

Released the existing Core 3 provider placement, auth-screen Suspense, conditional
public/account navigation, session-state regression checks and native launcher
fixes. Kept current SDK versions and server ownership/token contracts.

Only explicit Clerk/frontend/local-launcher/docs paths were committed. Unrelated
Phase 25 backend/parser/evaluation changes remain uncommitted and untouched.
Local environment files, keys and user sessions were not copied into the isolated
release checkout or GitHub. No hosted environment values, Render resources, Neon
schema/data, public account mode or paid resources changed. The backend tree is
identical to the already deployed `cf08aa4` backend, so no backend release was
needed. Documentation-only commits record release progress separately.

## Verification

| Check                | Actual result                                                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Isolated frontend    | Lint, strict types, build, launcher syntax, formatting and whitespace checks passed; 177 tests in 20 files passed in 59.30s         |
| GitHub Actions       | Frontend gate, backend tests/migrations, and production-build browser/container gate all passed                                     |
| Isolated Chrome      | Four public/accessibility/keyboard/readiness/missing-key checks passed in 8.3s                                                      |
| Hosted Chrome        | The same four checks passed on the canonical website in 15.2s                                                                       |
| Hosted visual check  | Unedited desktop/mobile landing screenshots inspected; browser screenshots remain under the ignored release checkout's test results |
| HTTPS/public routes  | Landing/security headers, sign-in/sign-up/account fallback screens, and missing-static-asset 404s passed                            |
| Backend              | Same-origin readiness returned 200, connected PostgreSQL, schema `0012_ai_context_reviews`                                          |
| Account gate         | Account API returned intentional 403 with code `demo_only` and `Cache-Control: no-store`                                            |
| Public bundles       | Thirteen landing script assets checked; zero private Clerk key pattern matches                                                      |
| Runtime observations | Error/fatal counts filtered to the new deployment in the queried 30-minute window returned no recorded groups                       |

Windows checkout CRLF conversion initially failed Prettier. Normalizing only the
isolated checkout restored the existing check, without additional committed source
changes. A baseline HTTPS request before deployment timed out during TLS; its
targeted retry and the final post-release checks succeeded with normal TLS
validation. No quota resets, account creation, demo bootstrap or uploads were used
for these read-only hosted checks.

## Remaining boundaries

Clerk's local account setup is still usable separately. This release does not
activate hosted sign-up: production needs an owned domain/DNS, matching live keys,
production JWT template and backend issuer/origin configuration described in
[the deployment runbook](DEPLOYMENT.md#h-configure-clerk-production-authentication-manually).
Live production sign-up, profile save/sign-out and two-account isolation were not
run. Existing privacy/account-erasure/lifecycle/CSP release limitations remain.

The runtime query is a bounded observation, not a long-term monitoring result;
drains were not inspected. The key check uses recognizable private-key patterns,
not decrypted production secret values or a complete security audit. Render and
Vercel releases still use the documented manual process; a future Git push alone
does not automatically deploy the site.
