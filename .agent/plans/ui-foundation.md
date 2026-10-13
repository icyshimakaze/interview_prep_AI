# Public and authenticated UI foundation

Date: 2026-10-13. Status: implemented and verified.

## Objective and scope

Build a professional, responsive public site and ten-section preparation workspace.
Use typography, warm neutral surfaces, restrained green, semantic navigation and
reusable controls. New account dashboards lead with onboarding, never invented
scores or activity. Preserve existing account authentication, profile persistence,
demo isolation/disclosure, completion, reset and deletion behavior.

This phase is UI foundation. Unimplemented ingestion, assessments, interviews,
question publication, roadmap generation and Project Defense remain explicitly
unavailable. No fabricated records, local pseudo-persistence, new AI integration,
commit, push or deployment. Existing unrelated work remains intact.

## Affected components

- Next app routes, shared public shell, authenticated/demo workspace shell and
  feature-specific views; shared buttons, inputs, forms, tables, dialog and states.
- Account data provider and profile form use the existing API; demo uses existing
  cookie/CSRF flows. Route navigation replaces in-page section buttons.
- Component/browser tests and documentation. No new dependency is expected.

## Database / API

None: existing owned dashboard/profile and demo contracts suffice. No schema,
migration, API authorization or existing persisted data changes.

## Frontend behavior and accessibility

- Public product/how-it-works/features/privacy, demo/sign-in CTAs and useful footer.
- Dashboard, Target Job, Resume, Assessments, Interviews, Question Bank, Roadmap,
  Project Defense, Progress, Settings/Profile routes with deep links.
- Persistent desktop navigation, keyboard/mobile menu, visible focus, skip link,
  semantic headings, labeled fields with validation, readable overflow tables,
  skeletons, recoverable errors and an accessible destructive-action dialog.
- Profile save has pending/success/error feedback; stale revisions can be reloaded.
- Consistent empty states explain what exists and the next available action.

## Security and privacy

Keep secrets server-side, auth state subject-scoped, data uncached, demo visibly
separate. Do not add personal-data inputs without real supported persistence.
Public privacy copy describes actual retention and known limits without promises
about unimplemented export/deletion. No user content is executed or sent to AI.

## Implementation order

1. Tokens, UI primitives, public shell and public pages.
2. Workspace navigation, shared section views, account provider/profile form.
3. Demo integration and route-level loading/error/not-found handling.
4. Regression/component/browser checks; visual desktop/mobile inspection.
5. Exact verification results, remaining limits and next task in PROJECT_STATUS.md.

## Verification

Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, formatting and relevant
Playwright checks. Test navigation, truthful onboarding, profile saves/failures,
retry, dialog focus/Escape, demo persistence/deletion and responsive overflow.
Use existing isolated browser harness for real API checks when available. Live
Clerk sign-in remains unverified without credentials; never bypass production auth
to preview account pages. Inspect final diff and preserve original V1 files.

## Outcome

Public site and all ten account/demo sections are implemented. Existing account
profile persistence, auth boundaries and demo CSRF/isolation behavior are retained.
No dependencies, API/schema changes, fake metrics or production workflow simulations
were added. See `docs/UI_FOUNDATION.md` for the route and component map.

Lint, strict TypeScript, 29 frontend tests and production build passed. Eighteen
browser checks passed with zero axe violations in tested views. Browser verification
used optional isolated ports added to the existing harness, preserving running
Compose services. Temporary test processes/database were removed. Live Clerk remains
unverified without credentials. Exact results/remaining tasks are in PROJECT_STATUS.md.
