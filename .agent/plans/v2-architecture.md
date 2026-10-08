# V2 architecture design

## Objective and scope

Design a portfolio-quality interview preparation platform and eventual Project Defense Mode. Produce `docs/V2_ARCHITECTURE.md`, update project status, and publish the documentation on `rebuild/professional-v2` as explicitly requested. No application implementation, dependency changes, deployment, or default-branch merge.

## Affected components

Read `AGENTS.md`, `PROJECT_STATUS.md`, `.agent/PLANS.md`, the full audit, and all three V1 source/data/dependency files. Preserve the existing audit and engineering guidance. Include these previously uncommitted documentation artifacts in the documentation commit after review.

## Design considerations

- Database: specify owned records, immutable attempts/content versions, Alembic migrations, jobs, retention, and deletion; execute no migration.
- API: specify typed contracts, auth, authorization, errors, idempotency, concurrency, and asynchronous jobs; create no endpoints.
- Frontend: specify routes, state ownership, recovery, provider labels, and accessible learning flows; build no UI.
- Security/privacy: define backend identity verification, visitor isolation, untrusted document/repository processing, AI output validation, secret boundaries, and external processing consent.
- Test strategy: define future unit, PostgreSQL integration, provider, migration, security, and end-to-end checks. For this phase verify document coverage, links, diagrams structurally, and unchanged V1 file hashes.

## Implementation order for this documentation task

1. Inspect repository, instructions, Git identity, remote owner, and contributors.
2. Verify official authentication/provider documentation and record concrete architecture decisions.
3. Write the architecture with all 20 requested areas and a concluding list of 10 decisions.
4. Update status, review internal consistency, and verify documentation/source integrity.
5. Commit reviewed documentation using the configured `icyshimakaze` identity with no co-author trailer; push only the current rebuild branch and verify the remote commit.

## Verification criteria

- All requested architecture sections are covered with implementable contracts and explicit scope limits.
- Mock responses are labeled simulations; real AI is optional and never silently substituted.
- Every private resource and job has an ownership boundary; unsafe code execution is excluded.
- Original `app.py`, `questions.json`, and `requirements.txt` hashes match the audited baseline.
- Documentation whitespace/local links and staged diff pass review; no `.env`, credentials, or application changes are staged.
- Commit author/committer match the existing user identity; remote branch matches the local commit after push.
- Application lint/type/test/build commands do not yet exist for V2 and are not claimed as executed.

## Outcome

Design and documentation verification completed on 2026-10-09: all 20 requested areas, ten concluding decisions, and five structurally reviewed Mermaid definitions are present; local links and whitespace checks pass; all three V1 file hashes match the baseline. V2 application checks and diagram rendering were not run. Publication is authorized only for the reviewed documentation on the current rebuild branch, under the existing user identity, with remote-ref verification after push. The application remains unchanged; deployment remains out of scope.
