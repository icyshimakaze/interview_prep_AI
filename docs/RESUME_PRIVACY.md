# Resume upload, evidence and privacy

23 October addition: upload/parsing remains local. A separate optional account
**Review resume evidence** action discloses the configured provider and requires
sharing consent before sending retained non-rejected claims/corrections and
excerpts. The raw PDF is never sent. xKiro routes through a third party/downstream
model; their retention policies apply. Saved feedback lasts up to 30 days plus
cleanup; evidence edits invalidate it and resume deletion cascades it. On Render
Free, cleanup runs at startup/hourly while awake; physical deletion is delayed
while sleeping or suspended. Review results expire from reuse after 30 days.
This feedback does not auto-confirm evidence. [Full provider/privacy details](XKIRO.md).

The Resume screen supports PDF upload, server-side text extraction, editable
evidence review, additions and deletion. The temporary workspace now also accepts
personal resumes through its isolated browser capability; account routes still
require Clerk authentication. Parsing uses no AI, OCR, external document service
or remote reference fetching. Temporary workspaces expose no external AI review.

Temporary access expires within 24 hours, with physical cleanup delayed while
free hosting sleeps. Losing the cookie loses access; there is no recovery or
cross-device login. **Exit and delete demo** erases the owned workspace and resume
records from active storage. Remove private details before upload. This feature
is live on both hosts at `cf08aa4`; see the [release report](RESUME_UPLOAD_RELEASE.md).

## Upload and processing

- Send a binary body with `Content-Type: application/pdf` to
  `POST /api/v1/account/resumes` or `POST /api/v1/demo/resume-library`, and a UTF-8 percent-encoded filename in
  `X-Resume-Filename`. This intentionally avoids multipart spooling or temporary
  files. Browser uploads use the original `File` as the request body.
- Require PDF MIME, a `.pdf` extension (case insensitive), PDF signature and
  successful strict parsing. Filename validation normalizes Unicode and rejects
  separators, drive/path syntax, leading dots and control/format characters.
  The filename is only an escaped display label, never a filesystem path.
- Limit 5 MiB (5,242,880 bytes), 1–20 pages, 100,000 extracted characters,
  2 MiB decoded content/filter streams and 100 retained evidence entries.
  Five resumes are allowed per workspace, including its seeded sample. Inputs and outputs are bounded separately.
- Two in-flight read/parse operations per API process; streamed reads have a
  15-second deadline. A short-lived Python/pypdf worker has a 15-second wall-time
  deadline and a 512 MiB OS memory limit (Linux address space or Windows Job
  Object committed process memory). Linux also applies a 12-second CPU limit.
  Failure to install limits fails closed. Timed-out workers are killed/reaped;
  cancellation retains the concurrency slot until the worker exits.
- The worker receives only PDF bytes through a private stdin pipe, without
  application credential environment variables. It returns only validated evidence
  and metadata through a private stdout pipe. Parser logging/warnings and stderr
  are suppressed; exceptions are replaced with allowlisted error codes. The API
  uses SQLAlchemy parameter hiding and never logs full text or upload bodies.
- This is resource isolation, not a claim of a complete OS security sandbox.
  Deploy the API as its existing non-root container user, with constrained ingress,
  container resources, maintained dependencies, and no request-body logging.
  Ingress/reverse-proxy buffering and operator diagnostics must not retain bodies.
  These operational release controls are not configured by this source phase.
- Encrypted PDFs are rejected without password collection. Corrupt, unsupported
  or excessive PDFs get recoverable errors and create no resume record. Empty or
  scanned PDFs can create an empty evidence record with a `no_text` explanation;
  users can add evidence or export a PDF with selectable text. OCR is unavailable.

Extraction uses pinned [pypdf 6.20.1](https://pypi.org/project/pypdf/6.20.1/).
Its [text extraction documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
explains content-stream memory costs and image-only limitations; file size alone
is therefore not the parsing safety boundary.

## What is retained

Raw PDFs and full extracted page text exist only in request/worker memory. They
are not written to a filesystem, database, object store, browser storage, or logs.
The worker exits after extraction. Request memory is released at completion; this
does not claim forensic zeroization of process memory or operating-system swap.

The database retains the validated display filename, checksum, byte/page counts,
extraction version/note, selected excerpts with page/normalized-text offsets,
categories, review status and supplied corrections/additions. `storage_key` is
null; `upload_deleted_at` records that the source was discarded. The pre-existing
upload deadline column remains for schema compatibility; there is no stored PDF
awaiting scheduled cleanup.

Each retained excerpt is at most 500 characters for automatic extraction.
Contact lines are not specifically collected, but a matched sentence or section
line can include personal information. Remove private details before upload, then
review and delete unwanted excerpts. No contact/demographic fields are created,
and parsing does not fill the profile, global `Skill` catalog, or job requirements.

## Evidence meaning and review

`lexical-sections-v1` detects explicit vocabulary mentions for languages,
frameworks, databases and tools. Projects/education/experience use recognized
section headings and conservative keywords. This is a finite deterministic
extractor, not semantic understanding, employment verification or an assessment.
Unknown terminology, unusual layouts and image text can be missed. Duplicate
category/claim mentions retain the first excerpt. A 100-entry cap is disclosed.

All extracted entries start **proposed**. Negative or aspirational mentions can
be included with their original context; users decide whether the claim belongs
in their evidence. There are no proficiency scores, inferred experience years,
missing-skill lists or automatically confirmed claims.

**“No evidence detected in resume” never means “Candidate does not know this.”**

Users can change the claim/category and confirm or reject it. Original excerpts
stay distinct from corrections. User additions have `origin=user` and no PDF
source fields, so they cannot masquerade as extracted evidence. Confirmation
means reviewed by the user, not independently validated. Rejected entries remain
visible for review but are excluded from dashboard preparation context.

## Account API and deletion

| Method and path (under `/api/v1/account`)                         | Behavior                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `GET /resumes`                                                    | Owned bounded collection, at most five resumes.                                 |
| `POST /resumes`                                                   | Validate/parse in memory and create resume, version and proposed evidence; 201. |
| `GET /resumes/{id}`                                               | Owned detail, metadata, revision and evidence.                                  |
| `POST /resumes/{id}/evidence`                                     | Add explicitly supplied evidence.                                               |
| `PUT /resumes/{id}/evidence/{evidence_id}`                        | Correct/category/review; immutable source fields cannot be supplied.            |
| `DELETE /resumes/{id}/evidence/{evidence_id}?expected_revision=N` | Delete the claim, correction and excerpt, returning refreshed detail.           |
| `DELETE /resumes/{id}?expected_revision=N`                        | Delete aggregate, all versions and evidence; 204.                               |

Evidence writes include `category`, `claim`, `review_status` and a positive
`expected_revision`. Every mutation locks the owned root and increments its
revision. Missing/foreign IDs are indistinguishable 404; stale writes are 409.
Owner/source/unknown input fields are rejected. The UI retains failed drafts and
offers explicit reload recovery and deletion confirmation.

Resume deletion is blocked with `resume_in_use` when retained assessment history
references its version. Individual evidence can still be erased. There is no
implemented assessment/history erasure UI yet; this limitation is disclosed.
Unreferenced resume deletion preserves the account/profile/jobs and leaves no
resume/version/evidence records. There is no account-evidence automatic expiry.
Operator backups, if configured, have separate retention and are not erased by
the active-database deletion control. Self-service full account erasure remains
unavailable.

## Migration and verification limits

The temporary library uses the existing owned resume tables without a migration.
Its operations mirror the account table above under `/api/v1/demo/resume-library`.
Every mutation requires the demo capability, exact allowed Origin and matching
CSRF token; the server derives ownership. The historical demo `/resumes/{id}`
summary route is unchanged. `is_sample` is derived from the server's extraction
version, never from a filename or a client assertion. Import quotas cover failed
parses and delete/reimport loops. Upload completion rechecks principal expiry.

Apply `0004_resume_evidence` after `0003_candidate_context` before starting the
updated API/frontend. The additive migration defaults old evidence to `other` /
`resume`, preserves original excerpts/IDs and adds revisions. Nullable source
fields are permitted only for explicit user-origin entries; compound ownership
constraints remain. Downgrade refuses populated new categories/origins, notes or
changed revisions rather than silently discard review data. Frozen earlier
migrations are unchanged.

Backend tests exercise actual PDFs in bounded workers and a fresh migrated
PostgreSQL database, using real signed JWTs with trusted test JWKS. Frontend tests
exercise SDK-authorized transport, file selection, review/correction, conflicts,
empty states and deletion. Browser form fixtures use actual component markup for
desktop/mobile layout and accessibility; they are labeled static test fixtures
and provide no account-authentication bypass. Live managed Clerk sessions require
configured credentials and are not established by these fixtures.
