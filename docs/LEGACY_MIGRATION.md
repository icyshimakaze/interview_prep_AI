# V1 content preservation

The root `app.py` is now a retirement notice directing users to V2. It no longer
runs self-rated sliders, invented metrics or the legacy classifier. The exact
original source bytes are retained in `content/provenance/streamlit-v1.txt` and
Git baseline `48fcd90`. `questions.json` and `requirements.txt` remain unchanged.
V2 uses separate packages and dependency environments; do not run the provenance
fixture as an application.

```sh
python scripts/export_legacy.py
python scripts/export_legacy.py --check
```

The deterministic exporter verifies SHA-256 hashes, parses question JSON and the
Python AST without executing the legacy application, and writes
`content/legacy-v1.json`. It preserves 15 unique titles, their original topics,
and 24 original roadmap strings, with stable IDs and source provenance. OS and
Operating System map to the same normalized topic.

Question entries are unpublished drafts with no fabricated prompt, difficulty,
answer, or rubric. Roadmap strings are editorial seeds, not scheduled/completed
tasks or previous user activity. License/provenance review and authored rubrics
are required before publishing any item during the learning phase. No metric,
self-rating history, classifier training label, timestamp, or outcome is invented
as user history. There was no durable V1 user database to migrate.

The relational phase now loads the 15 title drafts, six normalized skills and
seven aliases into PostgreSQL transactionally and idempotently, preserving stable
IDs and source provenance. It does not publish the drafts or fabricate grading.
After `alembic upgrade head`, run:

```sh
uv run --project backend python -m interview_prep.seeding
```

The loader validates the exact count, source digest and schema before writing;
re-runs preserve editorial edits. It is disabled in production. Development/demo
candidate history is seeded separately and explicitly fictional. See
[the implemented data model](DATA_MODEL.md).

Updating an original source fixture invalidates the hash check. Review the new source and
its Git provenance deliberately before updating the exporter; do not bypass the
check to make CI pass. The current generated seed format is version 1. Future
database schema/import changes must preserve versioning, idempotence and reconciled counts.
