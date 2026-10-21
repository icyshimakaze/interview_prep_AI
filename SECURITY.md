# Security policy

For the current threat review, ranked findings, fixes, retention/deletion inventory
and deployment requirements, read [docs/SECURITY.md](docs/SECURITY.md).

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/icyshimakaze/interview_prep_AI/security/advisories/new)
when it is enabled for this repository. If that option is unavailable, arrange a
private channel with the maintainer before sharing exploit details. Do not put
secrets, bearer tokens, private repositories or real candidate documents into a
public issue or pull request.

Include the affected commit, configuration relevant to the issue, a minimal
fictional reproduction, expected/observed behavior and the potential impact.
Redact logs. There is no published response-time SLA or bug bounty.

## Supported scope

Security fixes target the current V2 code. There is no stable released production
version yet. The preserved Streamlit V1 source and legacy dependencies are archival
and must not be deployed as an alternative runtime. Passing CI is evidence for
the tested behavior; the production release gaps in the detailed review remain
explicit.
