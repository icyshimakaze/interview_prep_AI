# Public and workspace UI

Foundation implemented 2026-10-13. This phase builds the interface on the existing owned
account/profile and isolated demo APIs. It does not enable new ingestion, practice,
question publication, AI, export, or account erasure workflows.

Follow-up: [candidate profile and target-job CRUD](CANDIDATE_CONTEXT.md) is now
implemented in account mode, including optional background/interests, profile
deletion, target editing/deletion, filtering and pagination. The original phase
route behaviors below remain an archive of the UI foundation.

## Routes

| Public route           | Purpose                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `/`                    | Product explanation, how it works, feature overview, privacy, demo and sign-in links |
| `/privacy`             | Actual collection, retention, demo erasure and account-control limits                |
| `/status`              | Existing live API/database connectivity check                                        |
| `/sign-in`, `/sign-up` | Managed Clerk flow or explicit missing-configuration state                           |

| Account route      | Section            | Current behavior                                                                   |
| ------------------ | ------------------ | ---------------------------------------------------------------------------------- |
| `/app/dashboard`   | Dashboard          | Onboarding actions; saved profile context; no fabricated metrics                   |
| `/app/targets`     | Target Job         | Owned target records or a profile-first empty state                                |
| `/app/resume`      | Resume             | Owned evidence or explicit upload-unavailable state                                |
| `/app/assessments` | Assessments        | Recorded results table or honest empty state                                       |
| `/app/interviews`  | Interviews         | Recorded feedback or honest empty state                                            |
| `/app/questions`   | Question Bank      | Explicit unpublished/unavailable state                                             |
| `/app/roadmap`     | Roadmap            | Existing tasks and status filtering; no account task creation                      |
| `/app/projects`    | Project Defense    | Explicit unavailable state and preparation prompts                                 |
| `/app/progress`    | Progress           | Recorded events with evaluation context; no readiness predictions                  |
| `/app/settings`    | Settings / Profile | Persisted profile editing, validation, saving/saved/errors and privacy information |

`/app` redirects to the dashboard. `/app/profile` and `/app/practice` alias Settings
and Question Bank. All `/app/*` routes retain the existing authentication boundary;
without Clerk configuration they show the account-unavailable page.

The demo shares the same sections under `/demo/<section>`, with `/demo` as its
dashboard. Its profile is read-only, every section retains a fictional-data notice,
and results explicitly identify simulations. Sample task completion persists through
the existing CSRF-protected endpoint. Exit opens a deletion dialog; the action erases
only the current demo through the existing API. No simulated sign-in was introduced.

## Design and components

`frontend/src/app/globals.css` defines a warm paper/white/ink palette, restrained
green, subtle borders, system sans body text and Georgia editorial headings. Fonts
require no external request. No new packages, animation libraries or image assets
were added. Content uses sections, rules, lists and tables rather than pervasive cards.

`components/ui/` contains buttons and link buttons, labeled inputs/selects, form
sections, tables, badges, native modal dialog with focus wrapping/restoration,
line icons, empty states, skeletons and error displays. `components/public/` owns
the public shell and explicitly labeled interface preview. `components/workspace/`
owns shared navigation, responsive shell and small feature views.

The desktop sidebar and mobile dialog use semantic links and `aria-current`.
Route changes focus the main content; skip links, visible focus, reduced-motion
support, table scroll regions/hints and announced states support keyboard use.
Profile fields retain failed edits, include constraints and associated validation
messages, and carry the current server revision. Reload explicitly discards unsaved
edits. A subject change remounts private state; no account cache/local storage is added.

## Verification and limits

Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and `pnpm format:check`.
The browser suite retains real service and two-visitor demo isolation/persistence/
deletion checks. Additional UI tests use explicitly intercepted demo fixtures for
all section layouts, recovery, mobile navigation, modal focus and automated axe checks.
Account component tests mock the SDK/transport to test subject isolation and profile
behavior; they are not a substitute for live Clerk verification.

Use the isolated harness described in [DEVELOPMENT.md](DEVELOPMENT.md) for browser
checks. Screenshots/traces stay in ignored `frontend/test-results/`. Exact run results
and remaining deployment limits are in [PROJECT_STATUS.md](../PROJECT_STATUS.md).
