# Project Status

Updated: 2026-10-09 (Asia/Calcutta).

## Current phase

V2 architecture design complete, following the current-state audit and engineering/planning guidance. Working branch: `rebuild/professional-v2`; application baseline: `48fcd90`. V2 implementation has not started. The user explicitly authorized publishing the documentation to this rebuild branch; application deployment and a default-branch merge are not authorized by this task.

## Completed work

- Inspected repository branch, status, remotes, history, and all three existing content files: `app.py`, `questions.json`, and `requirements.txt`.
- Created the rebuild branch from a clean `main` working tree in the preceding repository preparation task.
- Completed [the current-state audit](docs/CURRENT_STATE_AUDIT.md), covering architecture, state, content, assessment, AI claims, UI, security/privacy, persistence, dependencies, testing, deployment, and migration.
- Identified content and concepts worth retaining and components to replace without preserving unnecessary complexity.
- Added this status document. Application source, question data, and dependencies remain unchanged.
- Added root [engineering rules](AGENTS.md) and [substantial-change planning guidance](.agent/PLANS.md), covering typing, product integrity, ownership, untrusted input, migrations, verification, and release authorization.
- Created [V2_ARCHITECTURE.md](docs/V2_ARCHITECTURE.md): all 20 requested design areas, five Mermaid diagrams, implementation phases, and ten concluding decisions.
- Recorded the [architecture task plan](.agent/plans/v2-architecture.md). Reviewed real/demo identity boundaries, provider failure behavior, state transitions, evidence provenance, ingestion isolation, and deletion races.

## Architecture

Current: one 277-line Streamlit script with seven sidebar-selected views. A local JSON file contains 15 question titles in three topics. Three application session-state keys hold the latest six self-ratings, name, and role. pandas/Matplotlib display summaries; scikit-learn fits a decision tree to eight hardcoded examples for a readiness label. Roadmaps are fixed text and questions are randomly sampled.

V1 has no database, durable user history, authentication, API layer, answer grading, generative AI, or separate domain/service structure.

Designed V2: Next.js/React with strict TypeScript, Tailwind and selected shadcn/ui components; a modular FastAPI backend with Pydantic, SQLAlchemy, Alembic and PostgreSQL; Docker Compose; a worker from the same backend package with PostgreSQL-backed jobs. Clerk provides real account authentication, verified in FastAPI. Recruiter demo visitors receive separate expiring workspaces without cloud credentials. `AIProvider` supports deterministic labeled mock responses, optional local Ollama, and optional server-side OpenAI. Project Defense uses bounded static analysis of immutable source snapshots with cited evidence. These are design decisions, not implemented capabilities.

## Key decisions

- Keep this phase limited to architecture and documentation; do not change application behavior or implement V2 yet.
- Preserve the existing source and Git baseline. The current user request authorizes a documentation commit/push on `rebuild/professional-v2`; no force push, default-branch merge, or deployment.
- Treat current ratings as self-reported confidence, not demonstrated skill or validated readiness.
- Record accurately that a machine-learning classifier exists while roadmap generation, question selection, and skill summaries are not AI implementations.
- Recommend removing unsupported metrics and replacing the toy classifier with transparent evidence-based feedback; these recommendations are not yet implemented.
- Preserve the workflow and review the 15 question titles and 24 roadmap suggestions as content seeds. Do not migrate fabricated metrics or hardcoded labels as historical/training data.
- Use the specified web/Python/PostgreSQL stack as a modular monolith. No microservices, Kafka, Kubernetes, vector database, artificial ML, or agent orchestration.
- Keep adaptation and roadmap scheduling deterministic; separate objective results, model-assisted feedback, simulations, self-review, and confidence.
- Default public demo to MockAIProvider; never silently substitute mock for real AI or send local/private inputs to a cloud provider without explicit processing consent.
- Enforce owner-scoped data/jobs and validated AI output; never execute uploaded source. Introduce account uploads only after authentication, ingestion isolation, retention, and deletion checks pass.
- Follow `AGENTS.md` and `.agent/PLANS.md` for future work. Pin exact dependency versions and choose/evaluate the local model during implementation.
- Use the configured `icyshimakaze` author/committer identity without co-author trailers. GitHub's public owner/contributor check showed that account as owner and sole listed contributor; no ownership or collaborator changes are part of publication.

## Verification performed

- Read all V1 source/data/dependency files and the audit, status, engineering rules, and planning guidance; inspected tracked/untracked inventory before each phase.
- Python AST parsing and in-memory compilation passed. JSON validated: 15 unique nonempty titles, five each for Arrays, Linked List, and Stack.
- Recorded local package versions and probed imports. The unchanged app failed Streamlit AppTest startup at the pandas import due to NumPy binary incompatibility. Matplotlib also failed its import probe; scikit-learn was absent.
- Used an in-memory Streamlit AppTest harness with only pandas, Matplotlib, and scikit-learn imports omitted to check unaffected widget flows. Confirmed profile/slider reset behavior, session-only saved values, assessment guards, roadmap threshold behavior, cosmetic difficulty selection, and disappearing question output.
- Reviewed the actual classifier code and literal training examples; did not execute the classifier or populated dashboard/progress integrations.
- Compared SHA-256 hashes and Git diffs to verify all three original files stayed unchanged and only the requested documentation was added.
- Reviewed the engineering rules against all requested constraints and the planning outline against all requested areas; checked local links and documentation formatting. No application checks were rerun for this documentation-only phase.
- Checked official Clerk authentication, Ollama/OpenAI structured output, PostgreSQL job-locking, and GitHub archive documentation. Source links are in the architecture.
- Architecture review covers the 20 requested areas, ten final decisions, local links, Markdown/fence structure, and the five Mermaid diagram definitions. Diagrams were reviewed structurally, not rendered in a browser.
- Checked Git author/committer identity, remote branch state, and public GitHub owner/contributor metadata. Original source/data/dependency SHA-256 values still match the audit baseline.

No dependency installation, application implementation, real-browser visual/accessibility audit, deployment, performance test, or security vulnerability scan was performed. V2 lint/type/test/build commands are design requirements and do not yet exist; they were not executed. Detailed V1 evidence and limitations are in the audit.

## Known issues

- Local startup is blocked by pandas/NumPy incompatibility, a Matplotlib import failure, and missing scikit-learn. Dependencies and Python runtime are not pinned by the project.
- Homepage usage/success numbers have no supporting records; `500+` questions conflicts with the actual count of 15.
- Assessment is self-rating only. The eight-example readiness classifier has no real outcome data or validation.
- Roadmaps are fixed strings; question difficulty has no selection effect; profile role has no personalization effect.
- There is no durable progress history, complete profile saving, or restored assessment draft. Default ratings can trigger an “Excellent Performance” message.
- Queue, DBMS, and OS lack question-bank coverage. Existing entries lack statements, answers, rubrics, difficulty metadata, and provenance.
- There are no baseline tests, CI, deployment instructions, explicit privacy/retention policy, or verified production operating configuration.
- The V2 architecture addresses these issues in design only. Clerk integration, model quality, parser sandbox compatibility, quotas, and deployment recovery still require implementation and verification.

## Next task

On a subsequent implementation request, plan and execute architecture phase 1: a minimal monorepo foundation, strict types, Compose, PostgreSQL/Alembic, CI, health checks, and one isolated demo workspace. Then deliver a real objective-assessment slice before expanding context, AI, or Project Defense. No V2 implementation begins as part of this design task.
