# Personalized roadmaps and progress analytics

These features use persisted account or demo records and deterministic editorial
rules. They call no AI provider and make no readiness or hiring-outcome prediction.

## Roadmap workflow

Open **Roadmap**, choose a saved target or general preparation, enter available
hours per week, and optionally set an interview date. Saved profile time/date
values prefill the form; a new workspace visibly defaults to four hours per week.
The submitted budget is explicit and does not modify the preparation profile.

Each task includes its topic, rationale, high/medium/low priority, objective,
estimated minutes, recommended activity, planned week and status. Expand **Why
this task?** for the evidence-based rationale. Complete and reopen controls persist
the change. Historical tasks without saved rationale remain labelled historical;
their missing rationale is never invented.

**Regenerate recommendations** saves a new version and archives the current one.
The earlier version and all its task rows remain visible in **Preserved history**.
Existing completion timestamps and append-only completion events are preserved.
Reopening changes a task to planned and clears its current completion timestamp,
but does not remove the earlier completion event. Completing it again creates a
new event. Completion records an activity, not demonstrated competence.

Completed recommendation keys are omitted from a new plan. Skill keys include
the topic, activity type and a fingerprint of evidence-source identities. Fresh
results can therefore justify a fresh task on the same topic without changing the
completed historical task. Defense keys also identify the latest answer record
and status. Reopening a previously completed activity makes its key eligible again
unless another completed task still fulfils that key.

Regeneration requires the current plan ID/revision. A stale mutation returns 409
without rewriting saved work. Generation command UUIDs are idempotent: retrying
the same request returns the saved workspace, while reusing its UUID with a
different request conflicts. Failed requests retain the saved plan and visible
history. The UI preserves a generation key for retries of the same form request.

## Recommendation policy: `personal-roadmap-v1`

Inputs are read on the server for the resolved principal:

| Input                            | How it affects recommendations                                                                                                                            |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Selected target and job priority | Only owned, non-archived targets can be selected; higher-priority targets appear first in the selector                                                    |
| Reviewed job requirements        | Existing skill-evidence rules distinguish Required/Preferred from unreviewed lexical Mentioned                                                            |
| Resume/profile evidence          | Identifies topics to validate; a mention or claim never proves competence                                                                                 |
| Assessment performance           | Latest eligible reviewed deterministic results guide practice versus maintenance                                                                          |
| Interview history                | Eligible deterministic results can guide skill actions; model/simulation feedback remains unvalidated; completed history also suggests explanation review |
| Project Defense                  | Latest run per project, up to two focuses per project: skipped, then draft, then submitted; these are unscored discussion tasks, not failed skill tests   |
| Weekly hours                     | Converted to whole minutes, bounded to 15–10,080 minutes per week                                                                                         |
| Optional interview date          | Bounds estimated capacity and leaves tasks that cannot fit queued                                                                                         |

The existing `skill-evidence-v1` matrix produces **Practice**, **Validate** or
**Maintain** actions. Required skills receive high priority for practice/validation.
A high-priority target also promotes Preferred/Mentioned skill actions to high.
Other practice/validation is medium; maintenance is low. Ties use topic name and
stable recommendation key. Missing context yields explicit baseline/target tasks,
not invented weaknesses. Questions without attributable skill mappings do not
establish a topic-level skill result.

At most twelve recommendations are saved per generation, with a notice when more
remain. Estimates are 60 minutes for high/medium activities and 30 for maintenance,
capped at the weekly budget. The schedule greedily fills weekly buckets starting
on the generation date. A date on an item means the **week beginning** that date;
this is not a daily appointment or deadline. Estimates are editorial and do not
measure a candidate's speed.

The start date uses the saved profile timezone, or UTC without a profile.
PostgreSQL's timezone data supplies the conversion on all platforms. An invalid
saved timezone must be corrected in Settings; it is not silently replaced.
Past interview dates must be changed or cleared. Before an interview, estimated
total capacity is `floor(weekly_minutes * inclusive_days / 7)`. Tasks that exceed
capacity or fall after the date keep their priority and remain unscheduled.
The greedy policy can leave unused time; it is not a calendar optimizer.

## Progress policy: `progress-analytics-v1`

The Progress page aggregates current persisted source rows when requested, rather
than using seeded percentages or synthetic progress-event scores. It shows:

- Objective assessment accuracy over time and category response counts.
- Comparable recorded interview rubric rating series, with provenance.
- Current and historical roadmap task completion and completion-event counts.
- Repeated objective misses and separately labelled model-suggested gaps.
- Recent assessment, interview and Project Defense sessions, including unfinished
  sessions.
- Validated strengths in tested scope and areas requiring further validation.

### Assessment accuracy

Count only submitted deterministic grades in completed attempts, with a recorded
grading version, reviewed non-draft objective question, consistent binary score
and `is_correct`. Multiple choice, multiple select and authored literal short
answers qualify. Accuracy is `100 * correct / graded`, rounded to one decimal.
The denominator excludes skipped, written, ungraded, simulated and incompatible
responses. Zero correct is a real zero; zero eligible responses yields null,
displayed as not assessed. Category totals count eligible responses, not unique
people, mastery or a readiness level. Repeated attempts remain real observations.

Assessment charts require three graded sessions on three distinct UTC dates and
one consistent recorded grading policy. Tables remain available with smaller or
mixed-policy histories. Question mix and difficulty can change between attempts;
an accuracy line is not evidence that overall skill improved.

### Interview rating series

Choose the newest evaluation version for each answer **before** checking whether
it can be plotted. A failed or pending newest version cannot resurrect a previous
successful rating. Only completed main answers with a valid `answer-rubric-v1`
structured result, `rubric_mean` basis, consistent stored score and known 0–4 scale
qualify. Model-assisted results need stored provider and model provenance.

Series are separated by result kind, provider, model, provider/evaluator version,
rubric version, profile and exact assessed dimensions. Each point is the arithmetic
mean of the recorded answer ratings for that session within that series, rounded
to two decimals, with its rated-answer count. This is a descriptive mean of ordinal
ratings, not calibrated competence. Simulations, old unscaled scores, malformed
results, unscored follow-ups and unavailable evaluations are counted as excluded.
Charts again require three comparable sessions on three distinct UTC dates.

### Repeated concepts and validation

An objective incorrect response contributes its authored canonical question
concept. A valid model-assisted structured evaluation contributes its recorded
missing concepts as **model-suggested gaps**. These two bases are never merged.
Simulation lexical misses contribute neither. A repeated gap requires observations
in at least two distinct sessions; duplicated source IDs and evaluation retries
do not inflate counts. Exact concept labels are used without semantic synonym
merging. A missed question does not prove that every part of a concept is unknown.

Strengths reuse the conservative skill matrix: current eligible outcomes must
support maintenance, include assessment validation, and have attributable reviewed
scope. A conflicting latest weakness prevents the strength label. Resume claims,
task completion, model judgments and defense submissions do not validate skills.
Demo principals and partial matrix inputs withhold validation. Missing evidence
never establishes inability. Unscored defense summaries explicitly ask for further
review instead of supplying a performance score.

### Coverage limits

- Assessment detail: latest 100 completed attempts, at most 1,200 response records.
- Interview detail: latest 100 completed sessions, at most 1,300 latest evaluations.
- Defense context: latest run per project, at most 50 answer statuses.
- Recent activity: up to ten recent rows per channel, merged to fifteen entries.
- Repeated gaps: ten entries; strengths and mapped validation gaps: twenty each,
  plus the optional unscored defense summary.
- Skill matrix: existing 1,000-record input bounds and partial-data notices apply.

Limits are disclosed when exceeded. Incomplete input withholds matrix validation.
Counts are observations within the declared windows, not lifetime guarantees or
comparisons to a hiring-company threshold. All charts include accessible tables.

## Persistence, ownership and rollout

Migration `0009_personal_roadmaps` adds nullable generation UUID/input JSON to
`roadmaps` and nullable recommendation JSON to `roadmap_items`. It preserves old
plans and tasks without backfilling invented rationale. Generation inputs are
bounded to 32 KiB; recommendation metadata to 8 KiB. Immutable metadata guards,
owned foreign keys and a unique active-generated-plan index protect consistency.
The version pins policy/context, selected target version/priority, profile
revision, source references, concise rationale, counts, budget, date and notices.

Every private lookup and mutation checks server-resolved ownership. Principal and
plan locks serialize mutations; revisions prevent stale overwrites. Demo mutations
also require the existing Origin/CSRF controls. The old demo completion endpoint
uses the same completion service, so its writes respect saved roadmap revisions.

Account roadmap generations and completion events have no automatic expiry or
individual generation-deletion control. There is a fifty-generation limit per
principal to bound retained history. Demo data expires/deletes with its principal.
Deleting a resume or source session does not rewrite already-saved roadmap reasons
or source identifiers; no raw answer or resume text is copied into the roadmap.
Analytics are computed from source records without a separate metric cache. No
new data is shared externally. Backups follow operator retention rules.

Apply migrations before starting the updated API. Downgrade refuses if generated
roadmap metadata would be lost; use an operator-reviewed backup/export and removal
procedure before rolling back populated data. The application database is not used
by the disposable test harness.

Account and demo routes have the same contracts under `/api/v1/{account|demo}`:
`GET /roadmap`, `POST /roadmap/generate`, `POST /roadmap/items/{id}` with
`{revision, action: complete|reopen}`, and `GET /progress`. The generated OpenAPI
and typed frontend parsers describe the complete request/response contracts.

See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for exact verification results.
