# Project Defense Mode

Project Defense helps candidates explain projects they built, including work
created with AI assistance. It is deterministic source inspection and interview
practice, not a code audit, authorship detector, competence score or ML prediction.

## Using the feature

Open **Project Defense → Project Repository** in the account or recruiter demo
workspace. Choose one of:

- A public `https://github.com/owner/repository` URL, optionally ending in `.git`.
  The server resolves the current default-branch commit and fetches that commit's
  archive. The snapshot shows the repository URL, commit SHA and analysis time.
- A source ZIP, up to 10 MiB. Uploads use raw `application/zip`, not multipart.
  Remove secrets and unnecessary generated/vendor files before uploading.
- **Load illustrative demo project**. This authored task-tracker fixture passes
  through the same parser and persistence pipeline, without network or AI calls.
  It is explicitly labelled illustrative, not an audited application or evidence
  of a real candidate's work. Failed imports never silently substitute the fixture.

The repository analysis contains an architecture summary, technology view, tests,
CI, Docker and documentation signals, and an archive-relative file list. Paths
preserve directories, including any GitHub/export wrapper directory. Every
reported fact has a file and line citation. The app does not provide raw source
downloads. Compare the citations against your own checkout.

Start a ten-question defense, save a draft, submit or skip a question, pause and
resume, or end early. Submitted and skipped answers are immutable. Question
history includes saved text, status and submission timestamps; unasked questions
remain drafts, not invented answers. Early end preserves the current saved draft.
Reloading the page lets you reopen a saved repository and session from history.
Unsaved edits exist only in page memory. Save or pause before navigating away.

Questions cover framework choice, architecture, authentication/authorization,
persistence, scale/failures, security boundaries, testing, dependency trade-offs,
ownership/AI assistance, and change/reflection. Questions use a cited static clue
and conditional wording when behavior is unknown. Source presence does not prove
authorship. Candidates should explain which code they wrote, which was generated,
how they validated it, and what they corrected without inventing results.

## Observation versus inference

**Observed** means a bounded file, declaration or dependency name was found.
It does not mean the declaration is used or the dependency is installed.
**Inferred** means a heuristic suggests a possible role or behavior that the
candidate must verify. The UI labels these separately:

| Output                  | Method                                                | Meaning and limits                                                                                          |
| ----------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Languages               | Source filename extensions; counts of inspected files | Not lines of code, runtime usage or proficiency                                                             |
| Manifests/dependencies  | JSON/TOML parsing and bounded text patterns           | Dependency names only; specifications, URLs and scripts are discarded                                       |
| Frameworks              | Known dependency names                                | Observed declaration; no proof the framework runs                                                           |
| Backend/frontend        | Known framework role lookup                           | Inferred probable components, not verified deployment topology                                              |
| Database                | Driver/ORM names; Compose image/Prisma provider clues | Inferred technology; an ORM alone does not establish the database engine                                    |
| Authentication          | Known auth dependencies                               | Inferred implementation clue, not proof of secure authentication                                            |
| API routes              | Python AST decorators; method-call text patterns      | Inferred route-shaped declarations; mount paths, prefixes, exposure and dynamic registration are unverified |
| Models/schemas          | Python class bases and bounded declaration patterns   | Inferred model-shaped code; field semantics, constraints and actual persistence are unverified              |
| Tests, CI, Docker, docs | Paths and filenames                                   | Presence only; nothing is executed and no pass/security claim is made                                       |
| Directory structure     | Accepted archive paths                                | Partial tree of inspected files; skipped files are not exposed                                              |

Manifest support includes `package.json`, `composer.json`, `pyproject.toml`
(project/optional and Poetry dependencies), `Cargo.toml`, requirements text,
`pom.xml`, `Gemfile` and `go.mod`. This is deliberately partial static coverage:
Gradle, all .NET manifests, lockfile resolution, generated routes, arbitrary
framework plugins, runtime imports and recursive includes are not implemented.
Malformed manifests can yield no dependency facts. Text heuristics can match
comments or dead code. Missing evidence never establishes absence.

## Versions, storage and ownership

- Analysis version: `project-static-v1`; deterministic question generator:
  `project-prompts-v1`; generation method: `deterministic`.
- Existing owned project tables store snapshot metadata, file path/hash/size/
  language/line count, cited facts and exact generated prompts/evidence.
  Raw ZIPs, full source bodies, scripts and manifest value payloads are not
  retained. Source hashes are SHA-256 of accepted member bytes.
- Private generated question versions remain **draft**, with provenance not
  reviewed. They never enter published/reviewed question-bank inventory.
- `project_defense_runs` and `project_defense_answers` store owned practice
  state, revision, answer text and timestamps separately from scored interviews.
  No model is called and no evaluation or numerical ability score is fabricated.
  Optional AIProvider enrichment is **not enabled** in this version.
- Every read and mutation resolves the authenticated account or demo principal
  server-side. Request-supplied owner IDs are not accepted. Composite foreign
  keys enforce ownership among analyses, questions, runs and answers.
  Demo mutations also require the existing allowed-Origin and CSRF checks.
- A principal row lock serializes imports, quota checks, deletion, starts and
  answer commands. Start command keys are idempotent; a reused key with a
  different configuration conflicts. Answer commands require the current
  revision; a stale command returns 409 without overwriting saved answers.
  Database guards prevent identity changes, answer rewriting and run reopening.
- Identical archive bytes, analysis version and source provenance deduplicate
  within one owner. Uploading the example as a ZIP does not relabel it as the
  built-in demo. Public imports record commit identity separately.
- Five retained snapshots per owner; twenty practice sessions per snapshot.
  Delete a snapshot to remove its facts, generated private questions and all
  defense sessions/answers from active storage. Account snapshots have no
  automatic expiry. Demo expiry and **Exit and delete demo** remove owned data
  through existing principal cascades. Operator backups have separate retention.
- Import/worker/network failures do not modify an existing snapshot or answer.
  New snapshots commit atomically after validation. There is no provider call
  in the answer-saving path.

## Security boundaries

Repository contents, filenames, documentation and embedded instructions are
untrusted data. They cannot alter analysis policy or invoke tools.

### Network

Only strict HTTPS `github.com/owner/repository` URLs are accepted. Queries,
fragments, credentials, ports, branch paths, encoded path segments and arbitrary
hosts are rejected. Requests are constructed against fixed `api.github.com`
and `codeload.github.com` origins; redirects are refused, including redirects to
other GitHub locations. Repository metadata must say public. Commit identifiers
must be 40 lowercase hexadecimal characters.

The application sends no GitHub token, cookies or user-supplied credentials.
The production HTTP client disables environment proxy inheritance and redirects.
No submodules, Git LFS objects, package dependencies or links in source are fetched.
GitHub response bodies and errors are never returned verbatim or logged by this
feature. Metadata/commit responses are capped at 64 KiB each; archives at 10 MiB.
Encoded HTTP responses are rejected; streaming and total deadlines bound reads.
Moved repositories, unavailable archives, GitHub unauthenticated rate limits and
large metadata/commits may require the ZIP alternative.

This remains dependent on trusted DNS, TLS verification and GitHub's services.
It is not a general URL fetcher or a network namespace sandbox. Endpoint behavior
is based on GitHub's [repository content documentation](https://docs.github.com/en/rest/repos/contents)
and [commit documentation](https://docs.github.com/en/rest/commits/commits).

### Archives and parser worker

ZIPs are inspected **in memory and never extracted**. Reject:

- Absolute, traversal, drive/UNC, backslash, control/bidi, Unicode-normalization
  changing, Windows reserved and ambiguous paths, including file-prefix
  conflicts and case-insensitive duplicates.
- Symlinks, special files, encrypted members, unsupported compression, malformed
  archives, and entries exceeding expansion limits. Only stored/deflated ZIP
  members are supported. Directory entries are checked too.

| Bound                                | Value                                          |
| ------------------------------------ | ---------------------------------------------- |
| Archive upload/download              | 10 MiB                                         |
| ZIP entries                          | 3,000                                          |
| Declared total uncompressed content  | 40 MiB                                         |
| Any declared member                  | 10 MiB                                         |
| Expansion ratio per member           | 200:1                                          |
| Inspected member text                | 256 KiB                                        |
| Retained inspected file metadata     | 500 files                                      |
| Fact output                          | 600 facts                                      |
| Dependencies considered per manifest | 80 unique names                                |
| Path length                          | 500 characters                                 |
| Worker memory                        | 512 MiB using the shared platform limit helper |
| Worker wall timeout                  | 15 seconds                                     |
| Worker CPU limit                     | 12 seconds on POSIX                            |
| Concurrent imports                   | 2 per API process                              |
| Request body upload deadline         | 20 seconds                                     |
| GitHub total fetch deadline          | 40 seconds                                     |
| Answer length                        | 10,000 characters                              |

VCS metadata, dependency/vendor directories, common generated artifacts, nested
archives, binaries, non-UTF-8 text and common secret filenames are skipped.
Large accepted-type files are skipped, not partially read into misleading facts.
The report exposes skipped counts and truncation; it is not exhaustive.

A subprocess runs only trusted parser code using isolated Python (`-I`), a
stripped environment and an empty temporary working directory. The source is
passed over stdin; the parser returns schema-validated bounded JSON. No uploaded
code is imported, evaluated or executed. No package script, Git hook, test,
Docker build, macro, external XML entity or dependency installation is run.
The parser does not resolve input paths or open arbitrary filesystem files.
Worker stderr is discarded; errors use predefined safe messages.

This is **not a complete operating-system sandbox**. The worker's trusted Python
runtime/modules are installed outside its temporary directory, and the host
process still has its ordinary OS privileges. Resource limits reduce parser
denial-of-service risk but do not prove immunity to interpreter/library flaws.
Production operators should also enforce request-size/rate/concurrency limits at
the gateway and run the API/parser with least privilege and network restrictions.
The two-slot limit is per process, not a distributed quota or per-user rate limit.

### Privacy and trust limitations

Secret filename filtering is not comprehensive secret scanning. Accepted paths,
route literals, schema names or package names can still contain private data.
Remove secrets before upload; use fictional repositories in recruiter demos.
The UI renders evidence as text, never executable markup. Source instructions
cannot become system instructions; no LLM is used in this workflow.

No static report proves correctness, security, test coverage, deployment,
scalability or ownership. Static evidence should initiate a discussion, not
become a hiring or competence metric.

## API and migration

Account routes use `/api/v1/account/projects`; demo routes use
`/api/v1/demo/projects`, with the same contracts:

| Method/path                  | Action                                                        |
| ---------------------------- | ------------------------------------------------------------- |
| `GET /`                      | List saved snapshots                                          |
| `POST /github`               | Import `{"url":"https://github.com/owner/repository"}`        |
| `POST /zip`                  | Import raw ZIP                                                |
| `POST /example`              | Analyze labelled offline fixture                              |
| `GET /{id}` / `DELETE /{id}` | Read / erase owned snapshot and history                       |
| `GET /{id}/defense`          | Saved session/question history                                |
| `POST /{id}/defense`         | Start with UUID `command_key`, optional `question_count` 1–10 |
| `GET /defense/{run}`         | Restore saved session                                         |
| `POST /defense/{run}`        | `revision`, `action`, optional `answer_text`                  |

Actions: `save`, `submit`, `skip`, `pause`, `resume`, `end`.
The UI uses ten questions; the API defaults to eight when count is omitted.

Migration `0008_project_defense` adds nullable JSON summary/context columns to
existing project tables and two new owned tables with constraints/guards.
Existing snapshots and legacy demo data remain untouched; the new feature lists
only its own versioned snapshots. Apply migrations before starting updated APIs.
Downgrade refuses when new snapshots/defense records would be lost. Back up first,
export data through an operator-managed process if needed, then explicitly erase
new snapshots before downgrade. There is no automatic destructive rollback.

## Verification

Tests cover malicious paths, symlinks, duplicate/prefix paths, ZIP expansion,
network host/redirect/public-only boundaries, deterministic extraction and
questions, worker isolation, resource bounds, source minimization, owner isolation,
demo CSRF, deduplication/provenance, quotas, revision conflicts, durable answers,
failure preservation, deletion, database guards and UI behavior.

Run the disposable backend harness (`backend/.venv/Scripts/python.exe
scripts/check_backend.py`) and frontend lint, typecheck, tests and build.
The backend harness never migrates the application database. See
[PROJECT_STATUS.md](../PROJECT_STATUS.md) for exact completed gates and limitations.
