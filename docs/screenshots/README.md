# Product screenshot provenance

These are unedited PNGs copied from retained Playwright artifacts of the successful
22 October 2026 full local quality run, on the implementation subsequently committed
as `59e3507`. The original `frontend/test-results/.last-run.json` reports passed;
the full gate's results are recorded in [PROJECT_STATUS.md](../../PROJECT_STATUS.md).
The screenshots were visually inspected before inclusion. No fresh browser capture
or hosted deployment is implied by copying these artifacts into documentation.

| Published image                              | Capture source                                        | Data / boundary                                                                                       |
| -------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| [landing.png](landing.png)                   | `ui-foundation.spec.ts`, `landing-desktop.png`        | Actual public page. Its embedded workspace illustration is labelled interface preview by the product. |
| [skill-matrix.png](skill-matrix.png)         | `demo.spec.ts`, `skill-matrix-live.png`               | Actual local API and disposable PostgreSQL; fictional seeded candidate, no validated demo competence. |
| [assessment.png](assessment.png)             | `assessment-flow.ts`, `assessment-answer-desktop.png` | Live demo journey; persisted fictional response, local objective grading.                             |
| [interview-review.png](interview-review.png) | `interview-flow.ts`, `interview-review.png`           | Live demo journey; mock lexical feedback, saved practice and unscored follow-up.                      |

Source helpers/specs live in [frontend/tests/e2e](../../frontend/tests/e2e).
All four images have an original width of 1280 pixels; full-page heights differ.
Demo record IDs and timestamps describe disposable test data, not real users.
There are no real credentials, provider output or personal resume uploads here.

## Reproduce

Follow the [testing setup](../TESTING.md), then run from the repository root:

```sh
pnpm check:e2e --api-port 18101 --frontend-port 13101
```

The runner builds the production frontend, creates/seeds/migrates a disposable
database, forces mock AI, runs smoke and browser tests, and removes its owned
servers/database. Windows can select installed Chrome using
`$env:E2E_BROWSER_CHANNEL = 'chrome'` in PowerShell. PostgreSQL must already be
available; normal application services need not be running.

Find the named PNGs under `frontend/test-results/`, inspect them for private data
and simulation labels, then copy the originals into this directory. Avoid adding
traces, reports, environment files or arbitrary screenshots to the repository.
Update this provenance when recapturing; dynamic IDs/times may differ. Account-form
static fixtures and intercepted dashboard states are not presented as live account
integration screenshots.
