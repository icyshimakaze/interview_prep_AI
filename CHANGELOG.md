# Changelog

Significant changes are recorded here. V2 is under development; entries below
describe implemented source changes, not a published production release.

## Unreleased

### Added

- Full-stack quality pipeline with real PostgreSQL tests, migration round-trips,
  frontend lint/types/component tests, production build and Playwright journeys.
- Self-contained browser setup, deterministic mock AI, network guards, JUnit
  reports and failure diagnostics; contribution and security reporting guidance.
- Static public GitHub/ZIP repository analysis and saved Project Defense practice.
- Personalized, explainable roadmaps with preserved versions and completion events;
  progress analytics from persisted evidence with explicit sample-size limits.
- Structured answer evaluation with rubric profiles, validated provenance,
  simulation labels and safe rendering of untrusted feedback.

### Changed

- CI separates backend, frontend and browser gates and tests the frontend build
  produced by the frontend job. Frozen installs and pinned actions remain required.
- Dependabot covers workspace JavaScript, locked Python, Dockerfiles, Compose
  images and GitHub Actions. Minor/patch package updates are grouped for review.
- Browser form accessibility fixtures render directly instead of depending on
  artifacts written by the component test suite.
- Interview commands tolerate two worker-only revision changes with bounded
  retries while preserving draft/turn conflict checks. Repository lists expose
  loading and retryable errors before declaring an empty result.

### Security

- Request limits before JSON decoding; durable shared import/provider budgets;
  bounded paid-evaluation retries and validated result reuse across rollback.
- Sanitized unexpected error logging, bounded uncompressed outbound HTTP, total
  JWKS deadlines, PDF worker isolation, CSP and corrected privacy disclosures.
- Targeted certifi trust-store update to 2026.10.19 and an actual TLS trust-store
  regression. See [the security review](docs/SECURITY.md) for severity and remaining
  production requirements.

### Migration requirements

- Apply migrations through `0010_security_budgets` before running the updated API.
  Review documented populated-downgrade guards; these checks do not authorize
  destructive production rollback. Rebuild images to consume the updated lockfile.
