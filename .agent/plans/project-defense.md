# Project Defense Mode

## Objective and scope

Import public GitHub repositories or source ZIPs, show cited deterministic facts
and explicitly inferred architecture, and run saved project-specific interview
practice with question/answer history in account and recruiter demo workspaces.
Preserve the preceding evaluation work. No commit, push, deployment, repository
execution, dependency installation, private GitHub access or LLM requirement.
Optional AI enrichment is not enabled in this phase; deterministic questions and
authored reflection prompts work offline, including a labelled demo fixture.

## Architecture and data

- Reuse owned ProjectRepository/ProjectAnalysis/SourceFile/ProjectFact and private
  draft ProjectQuestion/citations. Never publish inferred repository content as
  reviewed curriculum. Retain facts/paths/hashes, not archives or source bodies.
- Add bounded snapshot summary JSON and owned defense run/answer tables in 0008;
  explicit revisions, current-question state and transactional writes. Refuse a
  lossy downgrade when populated. Existing general mock interview state is intact.
- New account/demo project endpoints: list/import/example/detail/delete and
  start/read/save/submit/skip/pause/resume/end defense runs. Every lookup/mutation
  scopes owner on the server. Demo mutations retain Origin/CSRF enforcement.
- Principal locks serialize quota, import deduplication, deletion and session
  commands. Project deletion also removes its private generated questions/history.

## Security boundaries

- Strict HTTPS github.com owner/repo URLs only. Fixed GitHub API and codeload
  hosts, no caller credentials, proxy inheritance, recursive fetches or redirects.
  Public metadata/default-branch commit resolution, strict commit SHA and bounded
  streamed responses under total deadlines. Failure never silently uses a fixture.
- ZIP inspection only: reject traversal/absolute/drive/UNC/control/ambiguous paths,
  duplicates, links/special files, encryption, unsupported compression and bombs.
  Bound compressed/uncompressed/member/total sizes, ratio, file/fact counts and
  worker memory/time/concurrency. No archive extraction, subprocesses from source,
  shell evaluation, scripts, macros, Git hooks, symlink following or remote includes.
- Trusted parser worker uses isolated Python mode, stripped environment and an
  empty temporary working directory. No source file is materialized. Shared memory
  limit helper may be reused; limitations of OS sandboxing are documented honestly.
- Ignore secrets, VCS metadata, binaries, vendors, generated artifacts and nested
  archives; never persist manifest values, raw source or remote error bodies.
  Only allowlisted technology identifiers and bounded safe static names/routes.

## Frontend

Replace Project Defense placeholder with Project Repository page: URL/ZIP/example
input, import progress/errors, snapshot list and deletion; analysis/architecture/
technology/directory views with evidence paths/lines and observed/inferred labels.
Defense practice: one question, cited context, explicit save/submit/skip,
pause/resume, early end, reload recovery, completion review and question history.
No numeric competence claims; source evidence is not proof of authorship. Include
questions about AI-assisted contributions, validation, trade-offs and ownership.

## Verification and delivery

Implement boundaries/analyzer first, then persistence/migration/owned APIs, then
frontend and documentation. Test malicious ZIPs/URLs, resource bounds, deterministic
extraction/questions, provenance, imports/replay/errors, concurrent revisions,
ownership/demo isolation/deletion, session persistence and UI states. Run Ruff,
strict mypy, disposable PostgreSQL harness/migrations, OpenAPI/client generation,
frontend lint/types/tests/build, formatting/diff checks. Document exact results,
retention, supported heuristics/limits and next task in PROJECT_STATUS.md and
docs/PROJECT_DEFENSE.md. Live GitHub verification is optional and read-only.

## Outcome

Implemented the deterministic GitHub/ZIP/example pipeline, versioned migration,
owned saved defense sessions, repository/architecture/technology/history UI and
security/retention documentation. Source paths retain their wrapper directories
rather than guessing which directory is disposable. Optional AI enrichment remains
disabled; no source bodies or archives are stored. Prior evaluation changes remain.

Verification: 469 full backend tests, then 39 focused tests with two additional
cases (471 tests covered across runs); Ruff 161 files; mypy 152 files; migration
round-trips/drift, populated downgrade refusal, OpenAPI and legacy checks passed.
Frontend 112 tests, ESLint, strict TypeScript and production build passed.
Application database rollout, live GitHub/AI/Clerk and browser E2E were not run.
See PROJECT_STATUS.md for operational limits and the next task.
