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

Release CI is green. Added official Render, Vercel and project-scoped Neon remote
MCP entries using Codex CLI. Render requires its documented public OAuth client
ID `codex`; its initial default-registration attempt failed, then the documented
client configuration started OAuth successfully. All three browser authorization
flows are pending user completion. No credentials were printed or copied into
the repository. No hosted database or service was modified. Reload the extension
after authorization so the new account tools can be discovered and used.
