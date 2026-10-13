# Relational data model

Implemented by Alembic revision `0002_relational_model` on PostgreSQL. There are
36 new domain tables and three preserved demo infrastructure tables; Alembic also
maintains its own version table. SQLAlchemy models live in small domain modules
under `backend/src/interview_prep/modules/`, with explicit registration in
`db/models.py`. The schema supports the requested entities without implementing
the later assessment, ingestion, inference, or project-analysis workflows.

## Entity mapping

| Requested entity    | SQLAlchemy class / PostgreSQL table                                            | Relationship                                                               |
| ------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| User                | `User` / `principals`                                                          | Account issuer/subject or expiring demo identity                           |
| Profile             | `Profile` / `candidate_profiles`                                               | One per principal                                                          |
| TargetJob           | `TargetJob`, `TargetJobVersion` / `job_targets`, `job_target_versions`         | Owned target with immutable description versions                           |
| Resume              | `Resume`, `ResumeVersion` / `resumes`, `resume_versions`                       | Owned document with input digest, extraction status and retention deadline |
| Skill               | `Skill`, `SkillAlias` / `skills`, `skill_aliases`                              | Global vocabulary and normalized aliases                                   |
| ResumeSkillEvidence | `ResumeSkillEvidence` / `resume_skill_evidence`                                | Owned version, optional skill, cited claim and review state                |
| JobSkillRequirement | `JobSkillRequirement` / `job_skill_requirements`                               | Owned target version, optional resolved skill and exact source span        |
| Question            | `Question`, `QuestionVersion` / `questions`, `question_versions`               | Stable global/private identity and versioned authored content              |
| Question grading    | `QuestionSkill`, `QuestionOption`, `ShortAnswerKey`, `QuestionRubricCriterion` | Normalized skills, options, accepted answers and weighted criteria         |
| Bookmark            | `Bookmark` / `bookmarks`                                                       | Unique owner/question-version pair                                         |
| Assessment          | `Assessment` / `assessments`                                                   | Frozen owner, resume/target versions and policy/context versions           |
| AssessmentQuestion  | `AssessmentQuestion`, `AssessmentQuestionOption`                               | Ordered question versions and actual presented option order                |
| AssessmentAttempt   | `AssessmentAttempt` / `assessment_attempts`                                    | Owned assessment, attempt number, idempotency key and lifecycle times      |
| QuestionAttempt     | `QuestionAttempt` / `question_attempts`                                        | Answer tied to both its attempt and allocation within the same assessment  |
| InterviewSession    | `InterviewSession` / `interview_sessions`                                      | Owned mock/project interview with frozen context/provider versions         |
| InterviewQuestion   | `InterviewQuestion` / `interview_questions`                                    | Ordered versioned content; bounded follow-up and project references        |
| InterviewAnswer     | `InterviewAnswer` / `interview_answers`                                        | One draft/final answer per allocated turn                                  |
| AnswerEvaluation    | `AnswerEvaluation`, `EvaluationDimension`                                      | Versioned evaluation, result kind, rubric scores and evidence spans        |
| Roadmap             | `Roadmap` / `roadmaps`                                                         | Owned context, schedule, timezone, budget and revision                     |
| RoadmapItem         | `RoadmapItem` / `roadmap_items`                                                | Ordered owned task, skill/resource, effort and completion state            |
| ProgressEvent       | `ProgressEvent` / `progress_events`                                            | Deduplicated completion fact referencing actual owned work                 |
| ProjectRepository   | `ProjectRepository` / `project_repositories`                                   | Canonical GitHub coordinates or uploaded archive origin                    |
| ProjectAnalysis     | `ProjectAnalysis`, `SourceFile`, `ProjectFact`                                 | Owned immutable snapshot identity with bounded source text and cited facts |
| ProjectQuestion     | `ProjectQuestion`, `ProjectQuestionCitation`                                   | Private versioned question with snapshot/file/line citations               |

Supporting grading and source tables use descriptive plural names. See the model
registry for their exact identifiers. The existing `demo_workspaces`,
`demo_sessions`, and `demo_creation_limits` remain compatible with the foundation.

## Ownership, history and integrity

- Domain records use UUID primary keys and UTC `created_at`/`updated_at` server
  defaults. Database triggers update timestamps and reject changes to identity,
  owner and creation time. Authentication identity kind/issuer/subject is immutable.
- Every private aggregate has `owner_id` referencing `principals`. Compound
  `(owner_id, parent_id)` foreign keys prevent attaching another owner's child.
  Question attempts additionally bind allocation and attempt to the same assessment.
  Owner-first creation/status/time indexes support scoped dashboard/history reads;
  parent, skill and uniqueness indexes support joins and duplicate prevention.
- Global catalog records have no user owner. Questions explicitly select global
  or private visibility. Their content/option/rubric children inherit visibility
  through the question rather than repeat a nullable owner. Database reference
  guards permit published global content or that principal's private content;
  draft global titles cannot be bookmarked or allocated.
- Enum values use named SQL CHECK constraints and Python `StrEnum`, making future
  additions explicit migrations without PostgreSQL native-enum replacement.
  Lengths, byte/page budgets, scores, sequence numbers, source spans, URL/path
  forms, lifecycle timestamps and parent/version uniqueness are constrained.
- Publishing requires complete content and grading: accepted short answers,
  correct multiple-choice options, or weighted authored rubric criteria. Published
  content and grading children are immutable. Retiring a version does not rewrite
  retained attempts. Attempted assessments freeze allocations/options/context.
- Submitted/skipped answers and terminal evaluations cannot be edited. A new
  evaluation version may supersede an earlier version of the same owned answer.
  Evaluation dimensions must use that question's rubric and valid answer offsets.
- Result kinds distinguish deterministic, model-assisted, simulation and self-review
  evidence. Resume claims are reviewed source evidence, not competence scores.
  Progress events are append-only, deduplicated facts with matching completion times.
- Project facts/questions reference the same owned analysis and actual file line
  bounds. Project interview turns require a cited private question from that analysis.
  Paths cannot escape the snapshot; this phase does not fetch or execute repositories.
- Only evaluation provider-usage metadata and optional progress details use JSONB.
  Both must be objects bounded to 8 KiB. Identity, answers, skills, relationships,
  criteria, schedules, results and citations are relational columns/rows.

Private aggregate children cascade with their parent. Historical context/content
references use deferred `NO ACTION`: deleting an isolated referenced source fails
at transaction commit, while deleting an entire principal cascades its private
graph. Global skills use restrictive references and survive user erasure. Privacy
erasure is the intended exception to immutable history. A future source-deletion
service must erase all affected quotations/derived history in one transaction;
there is no public source/account erasure or export API yet. ORM collection
relationships are read-only with explicit loading; creation/deletion uses services
and the database constraints, avoiding implicit ownership-changing ORM cascades.

## Migration and recovery

```sh
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend alembic -c backend/alembic.ini check
```

The additive migration backfills principals from existing demo workspace IDs,
creation times and expiry. Session/CSRF hashes remain unchanged. Trigger SQL is
frozen alongside this revision in `backend/alembic/relational_guards.sql`; future
guard changes require a new migration after this revision is released.

Rollback refuses any populated new domain table, including seeded content or
candidate profiles. Compatibility-only legacy demos can return to revision 0001.
Do not bypass the guard or downgrade application data to roll back code. Back up
the database and prefer compatible forward fixes. Empty database rollback and
re-upgrade are tested separately from populated-database refusal and legacy backfill.

## Development seeds

```sh
uv run --project backend python scripts/export_legacy.py --check
uv run --project backend python -m interview_prep.seeding
```

The transactional idempotent loader validates `content/legacy-v1.json`, including
the baseline source digest/schema and **exactly 15 unique title drafts**. It creates
six skills, seven aliases and versioned provenance links with stable UUIDs. Re-runs
preserve editorial edits. Titles have no invented prompt, difficulty, answer or
rubric; publication requires actual authoring and provenance review. The 24 legacy
roadmap suggestions stay in the editorial manifest, not fabricated candidate history.
The seed CLI is disabled with `APP_ENV=production`; production content publication
is a separate reviewed operation. A container invocation needs the manifest mounted
and `--manifest` pointing to that mount; normal development uses the native command.

Recruiter demo initialization is separate: each expiring principal gets its own
fictional profile, target, resume evidence, three authored private questions, two
simulated assessment attempts, one simulated interview, three roadmap tasks and
four initial progress events. IDs are stable within that owner, never across visitors.
Repeated bootstrap is idempotent. It makes no inference call and uses no real user
records. See [authentication and demo behavior](AUTHENTICATION.md).

## Database verification

```sh
uv run --project backend python scripts/check_backend.py
```

The script creates a previously nonexistent random `interview_prep_<hex>_test`
database, runs lint/format/types, upgrades, checks metadata, runs all tests,
downgrades that empty test database to base, upgrades again and checks contracts.
It removes only its created database afterward. Tests also construct independent
clean databases for migration/backfill/recovery cases. The application database
is never truncated or downgraded by this script.
