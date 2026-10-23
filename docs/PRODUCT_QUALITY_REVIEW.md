# Product quality and accessibility review

Reviewed 22 October 2026 (Asia/Calcutta). Scope: all 14 requested product areas.
Demo and Dashboard share `/demo`; Profile and Settings share `settings`, so these
are 12 distinct public/demo screens. This review assesses visible symptoms often
associated with generated interfaces; appearance cannot establish authorship.

## Method and limits

Inspected the running local application in installed Chrome at 1280 × 900,
375 × 812 and 320 × 812. Captured all 12 screens at each width, read the relevant
components and traced claims to actual persisted/demo responses. The browser
suite separately exercises real practice flows against a disposable PostgreSQL
database with mock evaluation and prevents external network requests.

Real Clerk sign-in is unconfigured. Profile, job-entry, PDF/evidence and skill
forms were reviewed using the actual components in explicitly labelled static
browser fixtures at desktop and both mobile widths. Their interactions and error
handling are covered by component tests; this does not establish a live account
session or verify a remote provider. No real personal data or external repository
was submitted. No paid AI request was made.

Before captures and machine-readable findings are retained locally in ignored
`.cache/product-review-before/`. Browser captures are under
`frontend/test-results/`; the public/demo after captures are in ignored
`.cache/product-review-after/`. These are local diagnostics, not published assets.

## Page-by-page findings

| Area                                | Finding and resulting change                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Landing `/`                         | Several interchangeable slogans, repeated descriptions of the same workflow, stale “in development” claims, decorative feature icons and oversized section gaps. Replaced the hero and section copy with concrete capabilities, corrected availability, removed redundant icons/paragraphs and tightened spacing. The labelled interface preview and fictional-demo disclosure remain.                                                                                                                     |
| Demo `/demo/*`                      | The shell already clearly distinguishes fictional data and simulated history, with privacy and expiry notices. Kept that disclosure. Loading now includes visible status text alongside skeletons. Tested the mobile navigation, deletion confirmation, failure recovery and focus return.                                                                                                                                                                                                                 |
| Dashboard `/demo`, `/app/dashboard` | Generic motivational headings, a large decorative icon, and saved-account guidance describing implemented practice as “upcoming.” Kept the candidate identity, used direct next-step copy, removed decoration, and linked a saved account to its actual roadmap. New accounts still receive profile setup. No readiness score was added.                                                                                                                                                                   |
| Profile `settings`                  | Existing form labels, optional-field descriptions, validation associations, invalid-field focus and revision recovery are sound. Strengthened shared control borders and used 16px mobile control text. The read-only demo now renders experience levels as human-readable labels.                                                                                                                                                                                                                         |
| Jobs `targets`                      | Demo content was clearly fictional but followed by a generic advice section. Removed that repetitive section. Account job forms retain required labels, validation, edit recovery and ownership-aware API behavior; shared input sizing and contrast improve their layout.                                                                                                                                                                                                                                 |
| Resume `resume`                     | Another generic advice section repeated what the evidence already showed. Removed it while retaining the claim-versus-competence warning. Reviewed actual PDF/evidence form fixtures and existing upload/error tests; upload limits, parsing and deletion behavior are unchanged.                                                                                                                                                                                                                          |
| Skill Evidence `skills`             | Long policy paragraphs pushed the useful evidence below the fold. Row headers inherited column-heading background and no-wrap styles. Kept a short interpretation warning, moved full policy notices into an accessible disclosure, corrected shared table row headers and retained individual source explanations.                                                                                                                                                                                        |
| Questions `questions`               | At mobile sizes, search was squeezed beside two buttons and eight filters delayed the results by nearly a screen. Search now gets a full row; a keyboard-operable filter disclosure shows the applied-filter count and preserves selections. Desktop filters remain visible. Kept semantic tables and self-review limitations.                                                                                                                                                                             |
| Assessments `assessments`           | Oversized rounded form/history containers, narrow format targets and technical provider class names. Flattened section boundaries, made format labels at least 44px tall, used a desktop format grid and plain provider-language disclosures. Corrected the written-answer hint that always claimed mock feedback even for configured AI providers. Grading, inventory, drafts and submission rules are unchanged.                                                                                         |
| Interviews `interviews`             | Controls mistakenly used the field-wrapper class, leaving selects and answer input without consistent borders/padding. Applied the shared input treatment, flattened history/review surfaces, replaced an undefined feedback-background token and allowed pagination to wrap. Provider disclosure and session behavior remain intact.                                                                                                                                                                      |
| Roadmap `roadmap`                   | Boxed notices and a card around every task created unnecessary visual layers; controls differed from the other forms. Used inline notices, divided task rows, consistent controls and shorter regeneration guidance. Recommendations, source explanations, completion/reopening and preserved history are unchanged.                                                                                                                                                                                       |
| Project Defense `projects`          | Title differed from navigation; the ZIP picker caused 15px of page overflow at 320px, and the URL input was squeezed on mobile. Matched the page title to navigation, bounded file controls, stacked narrow forms and used consistent errors. Reduced nested analysis cards and distinguished the main submit action from save, skip and navigation actions. Defense practice now has its own H1 and receives focus when opened. Static-analysis warnings, source provenance and unscored practice remain. |
| Progress `progress`                 | Mixed body sizes, repeated boxed demo warnings and cards around individual evidence items. Unified report typography, used a short inline simulation warning and separated evidence with rules. Confirmed that unavailable trends stay empty instead of showing fabricated scores; recorded task activity is not labelled competence.                                                                                                                                                                      |
| Settings `settings`                 | Shared Profile screen; read-only demo and privacy/account controls are distinct. Kept account export/deletion limitations, provider-sharing disclosures and the working privacy link. Simplified the eyebrow and humanized experience values; no pretend settings or unsupported controls were introduced.                                                                                                                                                                                                 |

## Cross-page assessment

The strongest generated-interface symptoms were repetitive motivational copy,
stale availability statements, arbitrary differences in form styling and card
containers introduced by newer modules. These received targeted fixes. The
existing serif/sans hierarchy, restrained green palette, navigation icons and
small control radii are coherent and were retained. No random gradients or
gratuitous page animations were found. Sparse source pages reflect the amount of
available evidence; the review did not fill them with placeholder content.

Tables retain captions, column and row scopes, a labelled focusable scroll
region and a mobile scrolling hint. Wide evidence/history tables scroll within
their region; the document itself must fit the viewport. Data and attribution
remain available instead of being removed to force every column onto a phone.

Fictional profiles, history and the illustrative project are explicitly labelled.
No fabricated testimonials, adoption metrics, interview outcomes or predictive
readiness percentages were found in the reviewed views. Empty analytical states
remain honest. Demo provenance is not evidence of real competence.

## Accessibility checks

- Keyboard: skip link, normal navigation, mobile filter toggle with Enter/Space,
  form controls, table regions and native disclosure elements.
- Focus: route changes focus the main landmark; mobile/deletion dialogs contain
  focus and return it on Escape; opening Project Defense focuses its H1. Existing
  profile validation focuses the first invalid input.
- Labels/names: form labels, icon-only buttons, active navigation, dialog titles,
  table captions, filter expanded state/control relationship and image names.
- Semantics: page H1s and subordinate headings, native buttons/forms/selects,
  real table headers and native modal dialogs. Fixed the missing defense H1.
- Contrast: axe text-contrast checks plus manual control-boundary inspection.
  Shared input borders changed from `#b8c2b8` to `#7c8b81` against white to exceed
  a 3:1 boundary contrast. Existing high-contrast focus outlines remain.
- Errors/loading: visible live loading labels, alert semantics, actionable retry,
  preserved drafts and field-level `aria-invalid`/descriptions. Tested service,
  workspace, deletion, profile, resume and repository failures.
- Reduced motion: browser emulation checks that the shared reduced-motion rule
  applies; no animation dependency was introduced.

Axe WCAG A/AA scans and accessible-name/focus assertions supplement visual and
source review. They are not a full WCAG conformance claim. No manual NVDA/VoiceOver
audio session, real mobile hardware or live Clerk/remote-AI session was tested.

## Verification and build finding

The required build exposed a Next.js security stop on 16.4.0. The
[official 14 October advisory](https://nextjs.org/blog/nextjs-security-update-october-14-2026)
identifies 16.4.1 as the patched release. Updated Next.js, the matching ESLint
configuration and their resolved packages only. No new dependency was added.
The production dependency audit subsequently reported zero known advisories.

Final results: lint, strict typecheck, **134 component tests**, **25 browser tests**,
native and Linux production builds, repository formatting and diff checks passed.
The refreshed local app passed **36 page scans** and **six additional repository/
defense scans** with no document overflow or axe A/AA violations. Its actual
frontend/API/database connectivity smoke also passed.

Full gate results and local-service verification are recorded in
[PROJECT_STATUS.md](../PROJECT_STATUS.md). The first component run caught three
dashboard-copy expectations; preserving candidate identity resolved them. The
first browser run passed 24/25, exposing a journey step that needed to open the
new mobile filter control. The step was updated while retaining its filtering
and persistence assertions. No test, lint or type gate was weakened.

Reproduce with `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` and
`pnpm check:e2e --api-port 18102 --frontend-port 13102` (Windows may need
`E2E_BROWSER_CHANNEL=chrome`). The browser runner owns and removes its test
database and temporary servers. No push or public deployment is part of this work.
