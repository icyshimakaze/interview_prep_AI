# Production question bank

## Objective and scope

Implement owned account/demo question browsing, search, category/subtopic/difficulty/
type/role filters, stable pagination, bookmarks and submitted attempt history.
Preserve 15 legacy drafts; publish newly authored, versioned adaptations plus a
small breadth sample. Practice uses explicit self-review; no scoring/AI/code execution.
The latest user request restored question-bank scope after an interrupted turn.

## Database and rollout

Migration 0005 adds nullable question metadata, frozen concepts/tags/roles and
owned append-only practice attempts. Preserve all old versions and history.
Publication is active; retirement is inactive. Refuse lossy downgrade. Separate
validated transactional seed command publishes content; no live migration/seed,
commit, push or deployment is authorized in this phase.

## API and privacy

List/detail/facets/history, idempotent bookmarks and submitted practice/delete APIs.
Every private query resolves/scopes server ownership; demo mutations require CSRF.
Never return answer keys/rubric anchors. Concepts unlock after owned submitted work
for the exact version. Include submitted assessment/interview history across
versions, excluding drafts/skips. Bound requests, pagination, storage and metadata.
Retry keys must match the original payload. Personal responses remain owned,
deletable and excluded from competence validation. No external calls.

## Frontend

Replace the Question Bank placeholder with search, filters, pagination, bookmark/
attempt status, detail, self-review submission and history. Loading/error/empty,
retained failed drafts and retry keys, stale-response and duplicate-gesture guards,
semantic labels and desktop/mobile support.

## Verification

Implement schema/content first, then API, contracts and UI. Test real filtering,
search, difficulty, stable pagination, bookmarks/ownership/concurrency, versioned
attempt history, disclosure gates, migration preservation/recovery and seed quality.
Run backend lint/format/mypy/full tests/migrations/contracts and frontend lint/types/
tests/build. Isolated Chrome flow plus axe/screenshots. Record exact results and
limits in PROJECT_STATUS.md. Preserve existing uncommitted skill-engine changes.

## Outcome

Completed. Versioned metadata and safe migration, 23-question authored catalogue,
explicit native/optional Compose publication, owned APIs and the frontend bank are
implemented. Legacy titles/drafts and preceding uncommitted skill work are preserved.
No live migration, seed, commit, push or deployment occurred.

Verification: 221 backend tests (28 new bank/content/migration tests), 68 frontend
tests and 23 Chrome browser tests passed. Backend/frontend lint and strict types,
production builds, schema/migration round trips, API contracts, original hashes,
formatting and Compose configuration passed. Browser checks exercise actual filters,
bookmarks, attempt-first concepts, persistence and deletion in the existing two-demo
visitor scenario. Mobile overflow was fixed; desktop/mobile screenshots inspected
with no axe violations in tested views. Live Clerk credentials remain unavailable.

Scored assessments and durable unfinished drafts remain outside this question-bank
phase. Required rollout and retention behavior are recorded in docs/QUESTION_BANK.md
and PROJECT_STATUS.md.
