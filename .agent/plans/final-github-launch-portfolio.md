# Final GitHub launch and portfolio

## Objective and authorization

Execute the user's 30 October 2026 explicitly approved GitHub-only cutover in
`docs/BETTER_AUTH_GITHUB_PUBLIC_RELEASE.md`, then prepare a truthful portfolio
homepage for the modern application. Public signup requires the independent
new-account Android acceptance gate; any critical failure requires closed
rollback.

## Scope and preservation

- Publish only the frozen 464-file ZIP (SHA-256
  `37bbc9a517aa9c3ea236735aa5d0ce9ccc3134f2bc40b98f284d7707fba2eac7`) on a
  temporary branch.
- Reuse exact existing Vercel/Render/Neon resources, retained secrets,
  compatible backend artifact, and verified rollback. No dirty-tree application
  build.
- Google and public password registration/recovery stay disabled. No DNS,
  purchase, production-branch merge, default-branch change, or unrelated
  feature.
- Portfolio changes use a separate modern-source branch; preserve meaningful
  documentation. A clean PR may be published only after the live-release gate,
  as requested. Prepare local reviewable artifacts even if the release fails.

## Affected components

Operational environment/alias settings and retained artifacts; isolated release
checkout; README, sanitized screenshots/provenance, architecture/setup/testing/
security/contribution links and repository-presentation guidance. Frozen runtime
files remain unchanged. Existing working-tree changes remain in place.

## Database and API

No schema, grant, password, API-contract, UUID, or data migration. Check 0013,
restricted roles, existing mappings and old business-row fingerprints read-only.
Preserve all existing/new accounts and saved work. Never restore over newer
rows.

## Frontend and security/privacy

Build production with domain assignment skipped; verify READY, source identity,
resource ownership and rollback before promotion. Temporarily reuse only the
approved invited JWKS bridge when restoring the tested backend. Human controls
provider passwords, consent and 2FA. Store secrets only in ignored protected
operator storage; persist only bounded acceptance evidence. Screenshots use
fictional demo data and no authentication/provider UI or tokens.

## Order and verification

1. Re-read runbooks, verify archive/backup hashes and private artifact ACLs;
   inspect live resource identities/plans, canonical alias, compatible rollback,
   database revision/grants/data and physical phone/new-account prerequisites.
2. Create isolated exact-source branch, verify every archive file, scan secrets;
   publish that branch only. Configure approved profile and create hosted build
   with `--prod --skip-domain`. Require READY and matching source/commit.
3. Restore approved backend via tested artifact/JWKS bridge, promote candidate,
   check Terms/Privacy/demo/provider policy and protected-route failures.
4. Run prepared state-correlated independent Android enrollment, saved work,
   restart, logout/revocation, returning login and cross-account denial checks.
   Verify DB/email independence and safe callback reason. Roll back on failure.
5. Inspect modern source and draft README claims; capture sanitized real product
   screenshots, prepare documentation on a separate local branch, run Markdown,
   relative-link/image/external-link and tracked-secret checks. Publish a clean
   PR only if the live-release condition is met; never merge/change defaults.
6. Update PROJECT_STATUS and final report with exact deployment IDs, checks,
   limitations and remaining human actions.

## Outcome

Executed the authorized attempt and verified the exact rollback. Frozen commit
`dbbe982186373ccaea1c7a34bd60a3d9f0f5d3a3` and hosted candidate
`dpl_8m3CbKEnmcD3oLtyd9k2LgJTqYsu` were verified before promotion. The real
callback completed a distinct-email account enrollment, but did not match the
runner's fresh state. The four-minute acceptance gate failed; downstream account
checks were not reached. No second attempt was started.

Closed frontend `dpl_A5RrDr2ro6Qw52ipZCcvWgyzNBLu` and backend
`dep-dbhpqbui0phs73f0jrtg` are verified; all 399 pre-launch business rows,
existing UUID mappings, three auth users, rotated credentials and both backups
remain. Exactly one phone-cookie-proven session was revoked after automatic
cleanup 422. Final physical closed-route and demo smoke passed.

Portfolio work is prepared on local branch `docs/portfolio-homepage-2026-10-30`.
It includes the polished README, source-verified stack/feature descriptions,
architecture, walkthrough, setup/testing/privacy/troubleshooting guidance,
sanitized real screenshots with provenance, preserved historical technical
README and GitHub presentation/default-branch recommendations. Markdownlint: 12
files, zero errors. Relative links: 259 valid. README diagram and six screenshot
assets: rendered at desktop/mobile widths. External checks: 12/14 returned 200
on Windows; the two canonical URLs hit transport errors there and returned 200
on physical Android. Four remote tip trees: 1,611 entries / 640 unique blobs,
zero known credential matches or private artifact paths (bounded scan, not full
history).

Documentation PR publication is held under the user's successful-live-release
condition. No merge, default change, DNS change, purchase or frozen runtime
edit. Before a separately authorized retry, resolve callback correlation and
cleanup 422; retain the newly enrolled account and do not call it a fresh
identity again.
