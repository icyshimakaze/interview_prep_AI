# Publish the Clerk integration to GitHub and Vercel

## Objective and authorization

On 25 October 2026 the user explicitly requested committing/pushing the local
Clerk changes to GitHub and making the update available on the existing Vercel
website. Release only reviewed Clerk/frontend/local-launcher/documentation work.
Preserve unrelated, uncommitted Phase 25 backend, parser and evaluation work.

## Verified baseline and scope

- Branch `rebuild/professional-v2`; HEAD `d23d276`. Existing Vercel production
  deployment `dpl_HJMVCGL5ziQK86VkijTAbdnP9sMs` serves `cf08aa4` at
  `https://interview-prep-ai-icyshimakaze.vercel.app`.
- Target project `prj_wsxEcvVC17paXs5pco4K9eHwWKgd`, account
  `team_vyOtLBqMjk5sQ9DTmzCcbwiN`, creator `icyshimakaze`; Node 24 / Next.js.
- Live environment-name inventory has gateway/origin/demo configuration and no
  Clerk keys. Production code requires live Clerk keys or the existing demo-only
  profile. A code push alone does not change that configuration or trigger the
  currently manual Vercel release.
- The previous local setup uses the selected existing Clerk development app.
  Production domain/instance requirements are pending user input. Do not publish
  development secrets, weaken the production guards, or claim hosted sign-in is
  enabled merely because the source is deployed.

## Components and data

Commit the existing Clerk components/layout/auth routes/navigation tests, native
launcher and associated docs/plans/status, plus this release record. No backend
source, dependencies, evaluation fixtures or Phase 25 files. No database/schema
change or migration for this release. Keep Render and Neon unchanged unless
production account configuration is separately established as necessary and safe.

## Execution

1. Confirm Git remote/branch, existing Vercel target/profile and hosted auth
   prerequisites. Obtain the user's owned-domain status while preparing the code.
2. Review the exact Clerk diff and use explicit staging/commit paths so unrelated
   working changes cannot be included. Do not read local environment files.
3. Verify the release in an isolated checkout without local Clerk keys or other
   uncommitted work: formatting, frontend lint/types/tests/build and relevant
   public/missing-key browser checks. Run existing CI after the authorized push.
4. Deploy the exact verified Git commit to the existing Vercel production project
   using authenticated MCP and its existing configuration. Verify build readiness,
   canonical alias, commit provenance, HTTPS/public routes/API readiness and the
   actual hosted auth state. Do not create a replacement project or paid resource.
5. Record exact commit, CI/deployment results and any remaining hosted-account
   prerequisite in status/runbook/report. The user's local app/data and unrelated
   edits remain intact. Use the preceding production deployment for rollback if
   the new release fails verification.

## Verification limits

No claim of production sign-up until a production Clerk instance, matching backend
trust and the required domain are configured and the real flow is exercised.
Keep account/demo ownership and secret-handling boundaries unchanged.

## Publication verification

The isolated Clerk-only checkout passed lint, strict types, production build and
all 177 frontend tests (20 files, 59.30s), plus four Chrome public/accessibility/
keyboard/readiness/missing-key checks (8.3s). No local configuration was copied.
Windows autocrlf initially changed baseline checkout line endings; formatting only
the isolated checkout normalized them and the full Prettier check passed, with
no additional Git source changes. Unrelated Phase 25 changes remain excluded.

Commit `c6dfda14be38fbb85cc9e267a43d2ef510794b51` was pushed to the current
release branch and all three jobs in GitHub Actions 40125359511 passed. Vercel's
exact-SHA production creation request then returned 403 requiring renewed team
access. The prescribed authorization tool issued a one-use link, presented to the
user; retry the same request after they complete that browser authorization.
The user confirmed no owned domain, so hosted account mode stays disabled.
