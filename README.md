# Interview Prep V2

A Next.js, FastAPI, and PostgreSQL foundation for evidence-based interview
preparation. The current phase provides a public product site, a responsive
workspace, typed contracts, a normalized relational model, Clerk account integration
and an isolated fictional recruiter demo. Accounts can save preparation profiles,
manage target jobs, upload PDF resumes and review editable candidate evidence.
The Skill Matrix separates resume mentions from demonstrated results and explains
deterministic preparation priorities without readiness percentages.
The Question Bank provides search, working filters, bookmarks, submitted history
and attempt-first concept review. Assessments now save real responses, score
objective questions deterministically, and offer clearly labelled MockAIProvider
conceptual feedback, review and history. The shared [AI-provider architecture](docs/AI_ARCHITECTURE.md)
defaults to `AI_PROVIDER=mock`; optional account providers support local Ollama and
OpenAI Responses. No AI credentials are needed for local defaults, tests, CI or
the recruiter demo, which always uses mock.
The [mock-interview workflow](docs/MOCK_INTERVIEWS.md) adds persisted adaptive
sessions, typed answers, optional contextual follow-ups, pause/resume and final
review across seven interview types. Answers are saved before optional evaluation.

```text
frontend/    Next.js App Router, React, strict TypeScript, Tailwind, UI primitives
backend/     FastAPI, Pydantic, async SQLAlchemy, Alembic, pytest, Ruff, mypy
content/     Preserved legacy drafts and a small authored question catalogue
docs/        Architecture, audit, and development instructions
scripts/     Configuration, content migration, contracts, and verification
.github/     CI quality gates and dependency updates
```

Use Node 24 LTS (24.15 or newer), pnpm 12.8.1, Python 3.12, uv 0.12.24, and Docker
with Compose. Dependencies are pinned and resolved in `pnpm-lock.yaml` and
`backend/uv.lock`.

From the repository root:

```sh
python scripts/init_env.py
pnpm install --frozen-lockfile
uv sync --project backend --frozen
docker compose up --build -d
uv run --project backend python scripts/smoke_stack.py
```

Open [localhost:3000](http://localhost:3000) and use **Try Interactive Demo** to
explore a fictional candidate, sample history and interactive roadmap without an
AI key. **Verify connection** on [Service status](http://localhost:3000/status)
checks actual service connectivity. The API's
[liveness endpoint](http://localhost:8000/health) and
[readiness endpoint](http://localhost:8000/api/v1/health/ready) expose separate
process and database/schema checks. All published Compose ports bind to localhost.
No cloud credentials are required for the demo. Real account sign-up/sign-in uses
Clerk and requires [the documented configuration](docs/AUTHENTICATION.md).

For native hot reload, quality gates, database migrations, configuration, and
troubleshooting, see [development instructions](docs/DEVELOPMENT.md). The
[approved architecture](docs/V2_ARCHITECTURE.md), [current status](PROJECT_STATUS.md),
and [engineering rules](AGENTS.md) define later phases. See the
[relational model, seed command and migration recovery](docs/DATA_MODEL.md).
The [UI foundation guide](docs/UI_FOUNDATION.md) maps routes, reusable components,
interaction patterns and the boundary between available and planned features.
The [candidate context guide](docs/CANDIDATE_CONTEXT.md) describes the implemented
profile and target-job CRUD, optional data, validation, authorization and retention.
The [resume privacy guide](docs/RESUME_PRIVACY.md) describes secure PDF ingestion,
deterministic evidence, review/deletion, API limits and migration 0004.
The [skill evidence engine guide](docs/SKILL_EVIDENCE_ENGINE.md) specifies evidence
states, source eligibility, job importance, prioritization and every numerical rule.
The [question-bank guide](docs/QUESTION_BANK.md) covers migration 0005, explicit
catalogue publication, protected concepts, filters, bookmarks and attempts.
The [assessment guide](docs/ASSESSMENTS.md) covers migration 0006, saved attempts,
answer protection, objective scoring and the mock evaluation-provider boundary.
The [interview guide](docs/MOCK_INTERVIEWS.md) covers migration 0007, durable work,
recovery, follow-up limits and the approved state-machine contracts.

The root `app.py` retires the V1 slider workflow and directs users to V2. Original
source bytes remain in `content/provenance/streamlit-v1.txt` and Git baseline
`48fcd90`; `questions.json` and `requirements.txt` are unchanged. The original
dependencies are outside the V2 runtime. The migration script preserves 15 question titles
and 24 roadmap suggestions as drafts, without importing unsupported metrics or
classifier labels. See [legacy migration notes](docs/LEGACY_MIGRATION.md).
