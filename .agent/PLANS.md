# Planning substantial changes

Before a substantial change (multiple components, schema/API changes, or meaningful behavior/security impact), read `PROJECT_STATUS.md`, relevant audit/design notes, and the affected implementation. Inspect Git status and existing checks. Base the plan on verified code, not documentation alone.

Write a short task-specific plan in `.agent/plans/<task>.md` before implementation. Scale detail to risk; small local changes need no separate plan. A plan does not expand the user's requested scope or authorize a push/deployment. Mark inapplicable areas `None` with a brief reason rather than inventing changes.

## Plan outline

| Area | What to record |
| --- | --- |
| Objective | User outcome, current problem, and measurable acceptance criteria. |
| Scope | Included work, exclusions, assumptions, and intentional behavior changes. |
| Affected components | Files/modules, dependencies, integration points, and existing behavior to preserve. |
| Database changes | Schema and ownership constraints, versioned migrations, backfill, data preservation, and rollout/recovery. |
| API changes | Request/response contracts, validation, authentication/authorization, errors, and compatibility. |
| Frontend behavior | User flow, draft/saved state, loading/empty/error states, and accessibility implications. |
| Security/privacy | Ownership boundaries, untrusted content, secret handling, AI output validation, personal data, retention, and external sharing. |
| Test strategy | Business rules, regressions, boundary/failure cases, ownership isolation, and appropriate integration/UI checks. |
| Implementation order | Small dependency-ordered steps, migration sequencing, and reviewable checkpoints. |
| Verification criteria | Actual lint/type/test/build commands, expected outcomes, user-visible checks, and known environment limitations. |

## Execution and completion

- Identify unresolved decisions early. Continue independent work; ask for clarification only when a missing decision materially affects correctness or scope.
- Implement within authorized scope, preserve existing work, and revise the plan when evidence changes assumptions. Record material decisions and deferred work.
- Add or update meaningful tests alongside behavior changes. Do not bypass quality checks to finish a step.
- Run the planned relevant checks and inspect the final diff for unintended behavior, secrets, and scope creep. Distinguish verified results from blocked or unrun checks.
- Update `PROJECT_STATUS.md` after the phase and record the plan's outcome and remaining work. Push or deploy only with explicit user authorization.
