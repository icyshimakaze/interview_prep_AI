# Resume hosted deployment access

## Objective and scope

Continue the authorized free-tier deployment after publishing the release.
GitHub Actions run 39985334206 passed for c39d70a. Reuse the user's existing Free
Neon project and selected branch/database, recorded in private local configuration.
Preserve application data, existing configuration and secrets. No paid resources.

## Verified access and affected components

Render and Vercel plugins are installed but expose no callable hosting tools.
Neon is currently not installed; its previously visible tools were removed.
No hosting CLI credentials, linked Vercel project or direct hosting MCP servers
are configured. Configure missing official remote MCP entries through Codex CLI
without printing or copying credentials. User completes provider OAuth consent.
Changes outside this workspace require the normal sandbox approval mechanism.

## Database, API and frontend

No new application, API or schema changes. Once access is authenticated, inspect
existing resources before changes; migrate only the selected Neon target using
reviewed migrations and separate runtime credentials. Retain the public mock
profile for initial verification and existing Clerk/xKiro account prerequisites.

## Order and verification

1. Confirm release CI, Git status, provider access and current official setup docs.
2. Add missing direct provider MCP configurations without replacing existing ones.
3. Complete OAuth through user sign-in and verify read-only resource discovery.
4. Continue Neon migration, Render and Vercel setup when tools become available.
5. Record exact completed work and concrete remaining access prerequisites.

## Outcome

Updated 24 October 2026. All three provider OAuth logins are complete. Remote tools
are usable through the documented Codex app-server protocol without a model turn.
Neon was verified empty, initialized through 0012 and checked for zero schema
drift. Its first migration attempt timed out and rolled back; the bounded retry
passed. Published 29 reviewed versions, with zero repeat writes. Runtime role
creation, grants, verified TLS and actual application readiness passed. Owner
credentials remain in memory, and generated deployment secrets remain ignored.

Matched the Render default to the existing Singapore database. Release 12daed1's
complete hosted CI is green. Existing unrelated hosting resources were preserved.
Render's connector reports no selected workspace and explicitly requires a user
choice before creation. Awaiting confirmation of My Workspace and the personal
Vercel Hobby account; then provision/verify the two free-profile hosts. No hosted
backend or frontend for this app has been created yet.
