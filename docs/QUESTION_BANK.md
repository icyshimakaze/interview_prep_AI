# Production question bank

Implemented 2026-10-14. `/app/questions` and `/demo/questions` provide stored
published prompts, real database filters, bookmarks and owned attempt history.

## Catalogue and provenance

The original `questions.json` has 15 titles under Arrays, Linked List and Stack,
without prompts, difficulty or answer criteria. The original file and immutable
legacy export remain unchanged. `content/question-bank-v1.json` contains **23**
complete authored questions: 15 adaptations plus eight covering SQL, Operating
Systems, Computer Networks, OOP, Backend, Frontend, System Design and Behavioral.
Some legacy questions use Algorithms. The subsequent assessment phase adds six
authored prompts from `content/assessment-bank-v1.json`, including DBMS and
multiple-select content: **29** published questions across the two manifests.
No coverage is claimed for unpopulated categories. See [assessments](ASSESSMENTS.md).

Prompts specify constraints and edge cases; expected concepts, tags and role labels
support focused review. Difficulty is an editorial easy/medium/hard classification,
not a measured ability estimate. Roles indicate editorial relevance. Source
classifications support authored, legacy_adapted, external_reviewed and
fictional_demo; this catalogue uses the first two. No third-party answer text was
copied. `source_license` records “project-authored prompt and concepts”; it does not
assert a license for old titles. Original file/commit/topic provenance is preserved.

Validation checks complete content, unique IDs/titles, bounds, objective keys and
exact preservation of all 15 original titles. Published content retains existing
grading-specification checks. Conceptual rubrics describe concepts/constraints/
tradeoffs without fabricating automated scores. Independent curriculum review and
expansion should create new versions.

## Schema, publication and recovery

Migration `0005_question_bank` adds nullable category/subtopic/source classification
to frozen versions and tables for ordered concepts, tags, roles and owned practice
attempts. Null metadata preserves older drafts/published content without rewriting
it. Concept/tag/role rows obey the published-content freeze rules.

The bank requires complete metadata, reviewed provenance, prompt, difficulty/type
and concept/tag/role rows. It selects the latest **released** version: draft
successors are ignored. Published is active; retired is inactive. A retired latest
release never resurrects an older active version. Historical references survive.

Stable legacy question IDs and version-1 drafts are retained; adaptations are new
version-2 records. New questions begin at version 1. The explicit transactional seed
uses stable IDs and a publication lock. Reruns preserve retirements and later
editorial versions; collisions roll back rather than overwrite. Reads and demo
creation never seed the global catalogue.

Run in a reviewed target environment:

```sh
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend python -m interview_prep.modules.questions.seed
uv run --project backend python -m interview_prep.modules.questions.seed --apply
```

For Compose, after applying the reviewed migration, the optional tools profile
mounts `content/` read-only and sets `QUESTION_CONTENT_DIR=/app/content`. It does
not start during ordinary `compose up`:

```sh
docker compose --profile tools run --rm seed-questions
docker compose --profile tools run --rm seed-questions python -m interview_prep.modules.questions.seed --apply
```

Without `--apply`, validation performs no database writes. Publication is explicit
and supports production configuration. Existing application services/data were not
migrated or seeded during implementation. Readiness requires 0005. Deploy the
updated API/frontend after applying schema/catalogue. Downgrade refuses populated
new metadata or attempts; empty-catalogue rollback works. After publication retain
the schema and restore compatible code or use reviewed database recovery. Earlier
frozen migrations remain unchanged.

## Filters and pagination

Filters combine with AND **before PostgreSQL pagination** and restrict questions
to global or resolved-owner private content. Private facets are owner checked.

| Parameter              | Rule                                                                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| search                 | Case-insensitive literal phrase in title, prompt, category, subtopic or tags. Escapes `%`/`_`; never searches hidden concepts, keys or rubrics. |
| category / subtopic    | Exact taxonomy label; frontend Topic uses subtopic.                                                                                             |
| difficulty             | Exact easy/medium/hard match; selecting hard actually excludes other difficulties.                                                              |
| question_type          | multiple_choice, short_answer, written, design, behavioral.                                                                                     |
| role                   | Exact stored relevance label.                                                                                                                   |
| bookmarked / attempted | Optional owned yes/no states. A bookmark is not an attempt.                                                                                     |
| active                 | True selects active releases; false selects inactive releases. Default true.                                                                    |
| offset / limit         | Offset 0–100,000; limit 1–50. UI pages use 12 questions or 10 history entries.                                                                  |

Results include exact matching totals and title/ID ordering. Unchanged catalogue
pages do not overlap; concurrent publication can move ordinary offset pages.
Facets use accessible active content, bounded to 100 categories/roles and 200
topics. Invalid enums, unknown query fields and excessive inputs return 422.

## Attempts, concepts and bookmarks

Lists never expose concepts or keys. Detail exposes prompt and MCQ option text/IDs;
correctness flags and rubric anchors are never returned. Concepts stay null until
the owner has submitted a response for the **exact version** in the question bank,
an assessment or an interview. Older-version attempts mark the stable question as
attempted without unlocking a new release. Draft/skipped answers do not count.
Protected answer keys remain private even after a bank submission.

Bank submissions store owner, response, question version, timestamp, submission
key and result kind. Accounts use explicit `self_review`; demo uses `simulation`.
No AI call, code execution, automatic grade, confidence score or competence
validation occurs. MCQ practice stores selected option text for self-review. Real
deterministic assessment results remain a separate workflow.

Identical key retries return one attempt, including after retirement. Different
question/version/response with the same key returns 409. New submissions to stale
or inactive versions return 409. Owner locks and uniqueness handle concurrent
gestures and storage bounds. History combines owned submitted bank/assessment/
interview responses across versions, sorted by submitted time then ID. Submitted
answers in unfinished assessments count as attempts; unsent drafts do not.
Bookmarks survive content updates; removal deletes all owned version bookmarks for
the stable question.

## API, ownership and retention

Use `account` or `demo` for `{mode}`:

| Method / path                                                | Behavior                                         |
| ------------------------------------------------------------ | ------------------------------------------------ |
| GET `/api/v1/{mode}/questions`                               | Filtered page                                    |
| GET `/api/v1/{mode}/questions/facets`                        | Accessible filter choices                        |
| GET `/api/v1/{mode}/questions/{id}`                          | Detail and gated concepts                        |
| PUT / DELETE `/api/v1/{mode}/questions/{id}/bookmark`        | Idempotent state; PUT body `{}`                  |
| POST `/api/v1/{mode}/questions/{id}/attempts`                | question_version_id, submission_key, answer_text |
| GET `/api/v1/{mode}/questions/{id}/attempts`                 | Owned paginated history                          |
| DELETE `/api/v1/{mode}/questions/{id}/attempts/{attempt_id}` | Delete an owned bank practice response, 204      |

Accounts require verified bearer identity. Demo uses an expiring isolated cookie;
mutations require exact Origin/CSRF. Client owner IDs cannot select data. Foreign/
missing private questions and attempt IDs return 404. Responses use no-store.
Only bank attempts are deleted here; other channels retain their workflow controls.

Limits: 500 bookmarks and 1,000 bank responses per owner; 1–10,000 trimmed response
characters. Accounts have no automatic expiry. History confirms deletion; deleting
the last exact-version response removes concept access on next read unless another
submitted channel qualifies. Demo uses fictional responses erased on exit/expiry.
No external answer sharing or deliberate answer logging. Active deletion does not
erase operator backups; full account erasure/export remains separate work.

## UI and verification

Search submits explicitly. Filters reset pagination; clear filters restores defaults.
Stale requests cannot replace newer results. Failed answers and their retry keys
are retained; duplicate gestures are blocked. Changed text is a new submission
intention. Unsaved local responses are not durable drafts. Saved history survives
reload; account changes remount private state. Empty/loading/error states and
bookmark failures are explicit.

Tests cover real filters/difficulty/search/pagination, literal wildcards, bookmarks,
concurrency/ownership/storage bounds, draft versus submitted history, exact-version
concept gates, retirement/deletion, seed preservation and migration recovery.
Frontend tests cover request races, retained retries, history and authenticated
transport. Chrome uses a seeded disposable database for the actual flow and
desktop/mobile axe/screenshots. Exact results and live-Clerk limits are recorded in
PROJECT_STATUS.md.
