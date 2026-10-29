# GitHub-only launch attempt — 30 October 2026

**Production website: ROLLED BACK. Public GitHub signup acceptance: FAILED.**
The public demo is working at <https://interviewprepai.webredirect.org>. Account
access is closed. No DNS change, purchase, Google activation, default-branch
change, production-branch merge, new migration or credential rotation occurred.

## Exact deployments

| Artifact                        | Verified result                                                                                                              |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Frozen source                   | 464 files; ZIP SHA-256 `37bbc9a517aa9c3ea236735aa5d0ce9ccc3134f2bc40b98f284d7707fba2eac7`                                    |
| Published temporary branch      | `release/github-only-public-2026-10-30-37bbc9a5`                                                                             |
| Published commit                | `dbbe982186373ccaea1c7a34bd60a3d9f0f5d3a3`                                                                                   |
| Attempted frontend              | `dpl_8m3CbKEnmcD3oLtyd9k2LgJTqYsu`, hosted production build READY                                                            |
| Attempted deployment URL        | <https://interview-prep-ai-icyshimakaze-fssm381xn-icy-shimakaze.vercel.app> (deployment protection may require owner access) |
| Backend activation              | `dep-dbhpnb1srm7s738f7ij0`, LIVE; reused tested artifact `dep-dbhnlao8v5cc738v5kpg`                                          |
| **Current canonical frontend**  | **`dpl_A5RrDr2ro6Qw52ipZCcvWgyzNBLu`**, closed/demo, alias verified                                                          |
| Current frontend deployment URL | <https://interview-prep-ai-icyshimakaze-n31wrsfvl-icy-shimakaze.vercel.app> (deployment protection may require owner access) |
| **Current backend**             | **`dep-dbhpqbui0phs73f0jrtg`**, LIVE; reused compatible artifact `dep-dbh6t7l9fdbs7384h740`                                  |
| Database                        | Existing production Neon branch, additive revision `0013_better_auth` retained                                               |

All 464 archive files match the published commit byte for byte. Vercel's
uploaded source matches 462 of these files by SHA-1; its source packaging
excludes the root `.dockerignore` and `.gitignore`. No runtime file differs. The
dirty working tree was not used for the application build. The hosted build was
created with domain assignment skipped, verified READY/source-matched, then
promoted through the approved invited JWKS bridge and compatible backend
restoration.

## Acceptance result and limits

The physical Android preflight passed HTTPS/TLS 1.3, anonymous Terms/Privacy 200
and footer links, GitHub-only signup UI, no password signup fields, Google
initiation rejection (400), email signup/recovery rejection (404), anonymous
token and account denial (401), public RSA-only/no-store JWKS, and readiness
200/0013. These legal-page changes belong to the attempted candidate; rollback
restores the older closed frontend.

The real authorization requested only `user:email`, used the exact canonical
callback and S256 PKCE, and had a state parameter. A callback returned 302 to
the application and the server recorded the bounded event `admission=public`,
`reason=completed`. Database inspection confirms one additional verified account
with email different from both previous identities. Its account and UUID are
retained.

**That callback did not match the fresh state tracked by the acceptance
runner.** No matching callback arrived within its four-minute window. The first
mandatory step failed as `real_callback_completed`. This is an
acceptance/correlation failure; it does not establish provider refusal, an
application state-validation vulnerability, or the underlying reason for the
mismatch.

Saved-work, refresh, normal Android restart, logout with unexpired-JWT
revocation, returning login and new-account cross-owner checks were **not
reached in this attempt**. Earlier restricted-account results remain historical
evidence and do not substitute for this gate. Public registration is therefore
not declared working. No second production attempt or staging phase was started.

## Rollback and preservation

- Re-promoted the exact closed frontend and restored the original five-variable
  frontend environment. Removed only the 13 introduced auth bindings; preserved
  canonical origins and the gateway-secret version.
- Restored the saved post-rotation closed backend environment and reused the
  compatible rollback artifact. Waited for LIVE; schema readiness remains 0013.
- Final physical checks: home 200, auth routes 503/closed, protected dashboard
  403 without private data, readiness 200/0013.
- The runner's automatic sign-out returned 422. Cleanup then matched the exact
  phone-origin session using a one-way token hash and revoked **only that one
  proven test session**. No account, provider binding or business record was
  deleted.
- Read-only row-hash comparison preserved **all 399 pre-launch business rows in
  52 public business tables**, including the existing UUID mappings and saved
  interview. All three auth users, including the new account, remain.
- Both encrypted backups retain their verified SHA-256 hashes and protected
  keys. No backup was restored over newer data, no schema downgraded, and no old
  password restored.
- Final physical public-demo smoke: create/read/dashboard 200, same workspace,
  owned deletion 204, read after deletion 401. Only owned ADB forwarding was
  removed.

The source publication scanned 563 tracked files against retained real secret
values and found zero matches. No caches, private operator files, database
connections or backups were published. This is a bounded credential check, not a
complete security audit. Original source/protected backup hashes and resource
identities/plans were verified before mutation; existing Hobby/Free resources
were reused.

## Portfolio work and next action

The portfolio README, actual product screenshots, setup/security/testing
guidance and repository-presentation recommendations are prepared on the
separate local branch `docs/portfolio-homepage-2026-10-30`, based on the modern
frozen source. The deployed release source stays unchanged. Documentation
publication and a GitHub PR are held because the user conditioned that phase on
verified live release. No merge or default-branch change occurred.

Before another release, resolve why the observed callback did not match the
runner's fresh authorization and why its cleanup request returned 422. Any retry
must preserve the retained account/UUID and use a fresh, human-controlled flow;
do not relabel the account as never enrolled. The original requirement for a
genuinely new independent identity remains unmet by a completed acceptance run.

## Portfolio verification

- Markdownlint CLI2 0.20.0: 12 Markdown files, zero errors. Prettier formatting
  checked for the documentation changes. HTML is intentionally allowed for the
  README gallery; the other default Markdown rules remain enabled, with a
  120-character prose limit and code/table exceptions.
- 259 relative file/heading/image references resolve across the changed guides,
  status, README and preserved reference; 10 referenced PNG files have valid
  dimensions. The README's six screenshot assets and Mermaid architecture render
  in a local browser preview at desktop/mobile widths, including expanded
  galleries, without horizontal overflow. GitHub styling may differ.
- 12 of 14 external URLs returned 200 from Windows. The canonical homepage and
  `/demo` returned transport errors there; separate read-only physical Android
  checks returned HTML/200 for both. No TLS check was disabled.
- Four public remote tip trees were inspected: 1,611 entries / 640 unique blobs,
  zero retained known-credential matches and zero private artifact paths. This
  checks current tips and prepared documentation, not every historical commit or
  every possible unknown secret.
- The documentation branch changes only Markdown and two sanitized screenshots.
  Application source, dependencies and migration bytes remain those of the
  frozen release commit. No new full lint/type/unit/E2E application suite is
  claimed for these documentation-only edits; the hosted build and executed live
  results above are reported separately.

Suggested repository About text, topics, social preview and the safe
default-branch transition are documented in the prepared presentation guide. No
settings were changed and no GitHub PR was published. The old Python `main`
remains the default until a separately authorized transition.

## Subsequent repair and documentation publication

The [focused investigation](PRODUCTION_ACCEPTANCE_REPAIR.md) recovered two
authorizations in different tabs and the wrong-origin GitHub cleanup request.
The operator runner is repaired locally; the application release is unchanged.
The user subsequently authorized documentation-only branch publication and a
reviewable PR. That approval supersedes the historical publication hold recorded
above. No merge, repository-setting change or further production cutover is
authorized. Public registration remains unlaunched.
