# Production relational data model

Date: 2026-10-09 (Asia/Calcutta).

## Objective and scope

Implement the explicitly requested domain persistence with PostgreSQL, typed
SQLAlchemy models, versioned Alembic migrations, and idempotent development seeds.
Preserve the uncommitted foundation and existing demo identities. This request
supersedes the design's incremental table-scaffolding guidance; it does not add
product APIs, authentication, ingestion, inference, or user interfaces.

## Design

- Use one account/demo principal (`User`), with the existing demo workspace as a
  compatibility child. Backfill existing workspace IDs without replacing tokens.
- Divide models into identity/context, curriculum, assessments, interviews,
  roadmaps/progress, and projects. Register all metadata explicitly.
- UUID identities, UTC server timestamps, database-enforced bounded enums/checks,
  owner-first indexes, and composite ownership/aggregate foreign keys.
- Normalize versioned resume/job/question content, options, rubric criteria,
  evaluation dimensions, project files/facts/citations. Use JSONB only for bounded
  algorithm/provider metadata rather than application state.
- Distinguish global curriculum from owner-private content. Database guards and
  explicit owner-scoped reads protect polymorphic curriculum references.
- Cascade private aggregate children and principal erasure; protect historical
  content/source references. Document deletion and rollback requirements.

## Migration and seeds

Add an additive revision after `0001_demo_foundation`. Preserve existing data;
guard destructive rollback when domain data exists. Only disposable test
databases may undergo rollback. Import the existing validated seed manifest
transactionally and idempotently, retaining exactly 15 title-only drafts and
their provenance. Do not create fictional users, attempts, metrics, or outcomes.

## Verification

Use real PostgreSQL and a newly created, randomly named `_test` database. Run
Ruff lint/format, strict mypy, all backend tests, metadata drift checks, seed
reconciliation and reruns, and clean upgrade -> safe rollback -> upgrade again.
Cover cross-owner/nested-parent failures, bounded scores/enums, uniqueness,
immutable submitted/history records, cascades/restrictions, legacy loading,
existing-demo migration preservation, and clean schema reconstruction. Refresh
health revision/OpenAPI/generated types; verify the running stack after migration.
Run affected frontend contract/type checks and formatting. Update architecture,
development/migration instructions and PROJECT_STATUS.md with exact results.

## Security/API/frontend

No new public feature endpoints. Owner IDs remain server-resolved; model/query
helpers do not establish authentication. No secrets or actual personal data in
seeds/logs. Data-only migration does not execute legacy code. Uploaded projects
and source content are never executed. Production ingress/auth/retention workers
remain separate implementation work.

## Order

1. Define typed domain models and ownership constraints.
2. Generate/review migration, timestamps/history guards, and demo backfill.
3. Add validated seed loader and scoped curriculum query.
4. Add relational/migration/seed tests and clean-database verification.
5. Run checks, apply additive app migration, verify services and update docs.

## Outcome

Implemented all requested entities with 36 normalized domain tables, explicit
ownership/history guards, additive demo backfill and safe rollback refusal.
The development seed loaded exactly 15 legacy drafts twice without duplicates.
The fresh PostgreSQL suite passed 86 tests, including clean upgrade/rollback/upgrade,
metadata drift, seed validation, ownership, relationships and constraints. The
application upgraded to revision 0002 without a downgrade. Backend lint/format/types,
generated contracts and unchanged legacy source checks passed. See PROJECT_STATUS.md
and docs/DATA_MODEL.md for exact verification and later workflow boundaries.
The subsequent account/demo request was implemented on this schema in its own plan.
