# Candidate profile and target jobs

Implemented 2026-10-13. These workflows use real account authentication and owned
PostgreSQL records. The recruiter demo remains fictional and read-only for profile
and job context. No AI, skill inference, file upload, or source fetching is involved.

## Candidate profile

Use **Settings / Profile** at `/app/settings`. Required preparation context is target
role, experience level, timezone and study budget. Display name, a short education
description, graduation year, technologies/interests and interview date are optional.
No institution, grades, birth date, contact information or demographic fields are
requested. Empty optional text is stored as null; clearing interests removes the
associated rows. Existing profile data is preserved by the migration.

| Field                  | Validation / storage                                                                         |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| Display name           | Optional; up to 150 characters                                                               |
| Education              | Optional; short supplied description, up to 300 characters                                   |
| Graduation year        | Optional whole year, 1900–2100                                                               |
| Target role            | Required, 1–200 nonblank characters                                                          |
| Experience             | Student, entry, mid or senior                                                                |
| Technologies/interests | Optional; up to 20 distinct supplied labels, 1–80 characters each; no competency mapping     |
| Preparation hours/week | UI converts hours into whole minutes; 15–10,080 minutes stored                               |
| Interview date         | Optional calendar date, years 1900–2100; stored in the existing profile `target_date` column |
| Timezone               | Existing preparation timezone; editable, checked by the browser's timezone formatter         |

`GET /api/v1/account/profile` returns the owned profile or null. `PUT` saves the
complete profile. Edits include `expected_id` and `expected_revision`; creation uses
null for both. The profile ID prevents stale edits from reaching a different profile
after deletion/re-creation. All mutations serialize against the resolved owner.
`DELETE /profile?expected_id=<id>&expected_revision=<revision>` removes only the
profile and its interests. It preserves target jobs, assessments, other history and
the account. Missing data returns 404; stale changes return 409.

The form retains failed edits, announces saves, disables duplicate submissions and
offers explicit reload recovery. Reload discards unsaved edits. Deletion requires a
keyboard-accessible confirmation and clears the visible form after success.

## Target jobs

Use **Target Job** at `/app/targets`. Title (up to 200 characters) and description
(up to 30,000) are required. Company (200), source URL (2,000), and notes (5,000) are
optional. Priority is low/normal/high; status is saved/applied/interviewing/archived.
Default values are normal and saved. HTTP(S) source links cannot contain credentials,
whitespace or backslashes. They are stored as supplied and are never fetched. Clicking
the explicit source link opens the external site in a new tab.

| API                                                 | Behavior                                                                                             |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `GET /api/v1/account/targets`                       | Owned list; limit 1–20, offset 0–10,000, optional status filter; returns items, total, offset, limit |
| `POST /targets`                                     | Creates a supplied job and description version; at most 100 jobs per account                         |
| `GET /targets/{id}`                                 | Owned metadata and latest description, or 404                                                        |
| `PUT /targets/{id}`                                 | Full edit with `expected_revision`; locks the owned record and increments revision                   |
| `DELETE /targets/{id}?expected_revision=<revision>` | Deletes an unreferenced job and description/requirement children; stale edits return 409             |

Description changes append a version instead of mutating source context. Metadata-
only edits do not add duplicate description versions. No `Skill` or
`JobSkillRequirement` is created from profile interests or job text. Text remains
untrusted input and is rendered as text in the UI.

A job referenced by retained assessment, interview or roadmap context cannot be
deleted: the API returns safe `target_in_use` conflict feedback and the UI offers an
archive edit. Archive preserves all context/history; it does not free the 100-job
storage limit. Missing and foreign IDs both return 404. Body schemas reject unknown
fields and every query/mutation uses the authenticated principal. Account/demos
remain separate.

## Migration, rollout and retention

Revision `0003_candidate_context` adds optional profile columns, normalized
`profile_interests` with compound owner/profile foreign key and cascade erasure,
and target metadata/revision with neutral defaults and database bounds. No existing
profile/job/description is rewritten. Update the schema before starting the updated
API (`alembic upgrade head` through the documented backend environment). Readiness
requires `0003_candidate_context`; old running services need an intentional update.
Apply to a backup-tested environment using the existing migration/runtime process.

Downgrade refuses to discard populated new context fields, interests, nondefault
target metadata or changed revisions. Recovery should roll forward; empty/neutral
rollback and re-upgrade are verified only on disposable databases. Old migrations
remain frozen. Account context has no automatic retention period. Profile deletion
and unreferenced job deletion work now; full account export/erasure, backups and
identity-provider lifecycle reconciliation remain later work.

Exact checks and current rollout limits are in [PROJECT_STATUS.md](../PROJECT_STATUS.md).
