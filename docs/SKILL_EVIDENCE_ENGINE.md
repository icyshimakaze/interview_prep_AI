# Skill evidence engine

Policy: `skill-evidence-v1`. This deterministic preparation aid does not predict
hiring success, proficiency, or job readiness. No ML, model calls, embeddings,
probabilities, hidden weights, or readiness percentages are used.

## Implementation map

The pure [state engine](../backend/src/interview_prep/modules/skills/engine.py)
consumes facts loaded by [owned context adapters](../backend/src/interview_prep/modules/skills/context.py)
and the [performance eligibility adapter](../backend/src/interview_prep/modules/skills/performance.py).
The [service](../backend/src/interview_prep/modules/skills/service.py) assembles
the response; the [Skill Matrix UI](../frontend/src/components/workspace/skill-matrix.tsx)
renders explanations and sources. [Current architecture](ARCHITECTURE.md) explains
where this read-only engine feeds assessment/interview selection and roadmaps.

For example, a resume mention of Python plus a latest eligible incorrect objective
result yields **Some evidence** in the resume column and **Needs additional
practice** in competence. Without that eligible grade it yields **Needs assessment
validation**. A simulated/model grade does not change either case into validation.
These are rule examples, not reported candidate outcomes.

## Independent evidence states

Each row separates job importance, resume mentions, demonstrated competence and
next action. A resume can mention Python while an assessment shows a need for
practice. An assessment can validate a tested concept absent from the resume.

| Column / state              | Exact rule                                                                                                                                                                   |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Resume: Some evidence       | At least one non-rejected, resume-origin mention from a current resume version. Proposed entries count only as mentions.                                                     |
| Resume: No resume evidence  | No such mention in included sources. Never means the candidate lacks the skill.                                                                                              |
| Needs assessment validation | No eligible demonstrated result exists.                                                                                                                                      |
| Some evidence (competence)  | Interview success for one concept, no current negative result, no assessment validation.                                                                                     |
| Validated by assessment     | Assessment success, no current negative result, fewer than two distinct successful concepts. Validation covers only tested scope.                                            |
| Strong evidence             | Current eligible successes for at least two distinct concepts, across either channel, with no current negative result. A breadth rule, not calibrated confidence or mastery. |
| Needs additional practice   | At least one current eligible assessment or interview result needs practice. Takes precedence over positive states.                                                          |

`assessment_validated` independently means at least one current assessment success
and no current assessment failure. An interview weakness can coexist with it. The
UI shows both. Resume claims, user confirmation, education, seniority and interests
never establish competence. Collections of resume claims are not “Strong evidence.”

## Inputs and eligibility

- **Profile:** supplied interest/technology labels add rows. Exact case-insensitive
  full-label aliases resolve known skills; unfamiliar phrases remain one supplied
  label. No inference from degree, name, graduation date, role or study budget.
- **Resume:** latest version per owned resume, excluding rejected entries. Use an
  explicit skill link when available, otherwise lexical matches in claim/excerpt.
  Corrections replace matching text and supersede old skill links; original
  excerpts remain disclosed. User additions are user claims, not PDF evidence.
  Negative/aspirational text can match: a mention is not an affirmative claim.
- **Job:** one explicitly selected owned target, latest description version only.
  Archived targets remain selectable. Job-level priority is not skill importance.
- **Assessments:** submitted graded answers in completed attempts, with a
  deterministic result, grading version and `is_correct`. True meets the tested
  criterion; false needs practice.
- **Interviews:** evaluated turns, submitted answers, completed sessions. Consider
  only the latest evaluation version per answer, even if it failed. Require a
  completed deterministic evaluation, evaluator version and matching rubric
  version. Every authored criterion must have one evaluable dimension, with no
  extra or missing criteria. Every dimension must meet anchor **3 or 4** on the
  existing **0–4** scale; any lower dimension needs practice. Overall stored
  scores and criterion weights are not used. Missing/not-evaluable dimensions
  withhold validation.
- **Question scope:** content must be reviewed and published or retired, have a
  nonempty canonical concept, and map to exactly one skill. Multi-skill results
  remain visible but cannot validate individual skills without attribution.
- **Excluded:** simulations, self-review, model-assisted output, drafts, incomplete
  work, absent grades and invalid rubric coverage cannot validate. Demo mode
  disables all validation even if a record is accidentally marked deterministic.
  History without a skill mapping cannot produce skill evidence.

Sources expose IDs, original/corrected text, review status, question/rubric/grading
versions, concept, completion date, eligibility and outcome. Assessment/interview
answers are not returned. Earlier assessment attempts remain visible; superseded
interview evaluation versions are replaced by the latest version.

## Vocabulary and job importance

Reviewed `skills`/`skill_aliases` combine with the resume extractor's finite
language/framework/database/tool vocabulary. Literal aliases are escaped and
bounded by word boundaries; explicit aliases include Postgres/PostgreSQL and
Kubernetes/k8s. Python does not match Pythonic; Java does not match JavaScript.
No fuzzy matching or global skill writes occur. Unknown profile phrases are not
split into inferred skills. Unmatched skills can be absent: this is not a complete
skills audit.

| Importance    | Rule                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------ |
| Required      | Confirmed `essential` linked requirement in latest job version.                                  |
| Preferred     | Confirmed `desirable` linked requirement in latest job version.                                  |
| Mentioned     | Proposed linked requirement or lexical match in job text, including unreviewed negative phrases. |
| Low relevance | No included job evidence for this skill, or no target selected. Not a judgment of general value. |

Confirmed/rejected linked requirements suppress automatic extraction for that
skill/version. Rejected entries do not contribute. Null skill links cannot establish
reviewed importance. New description versions do not inherit old decisions.
Highest included importance wins. Raw “required” prose is not promoted: negation,
alternatives and headings need explicit review. The schema supports reviewed
Required/Preferred; a production requirement editor is outside this phase and
its absence is disclosed in the UI.

## Transparent prioritization and numbers

1. Group eligible results by channel and canonical concept. Choose the latest
   completion timestamp, breaking equal timestamps by lexicographically greatest
   source ID. This tie-break has no evidence weight.
2. Eligible retakes replace older results for the same concept/channel. Repeated
   versions/attempts of one concept never satisfy breadth. Incomplete or ungraded
   later work does not erase an earlier completed grade.
3. Current failure in either channel wins over positives. Passing another concept
   does not erase a weakness. No automatic time decay; dates remain visible and
   historical results do not imply current mastery.
4. Compute the states above. Sort by importance, then action, then casefolded skill
   name, then stable skill key. Every row explains its ordering.

Internal ordinal positions: Required **0**, Preferred **1**, Mentioned **2**, Low
relevance **3**. Actions: Practice **0** for practice needs; Validate **1** for no
validation or interview-only Some evidence; Maintain **2** for positive validation
states. Positions are never summed or normalized. Required/Maintain intentionally
precedes Preferred/Practice. The only evidence count threshold is **two distinct
concepts** for breadth. These are declared editorial rules, not empirical estimates.

## API, ownership and resource limits

`GET /api/v1/account/skill-evidence?target_id=<UUID>` uses verified account identity;
`GET /api/v1/demo/skill-evidence?target_id=<UUID>` uses the isolated demo cookie.
Omitting target gives profile/resume/performance context. Responses include policy
version, mode, selected target, all target choices, ordered rows and notices.
Foreign/missing targets both return 404; absent identity returns 401. No client
owner input can select another account.

All private reads scope the resolved owner, including private question content.
Each input category reads **1,001** records to detect overflow and includes at most
**1,000**. This is a resource bound, not evidence weight. Overflow yields explicit
partial-result notices and disables all competence validation, so omitted failures
cannot produce positive verdicts. Rubric rows are fetched in batches.

Job excerpts contain the first lexical match with up to **100 characters** of
context on either side. This is a display bound only and has no effect on priority.

No writes, schema migrations, cached snapshots, external sharing, new dependencies
or new retention stores. Source deletion/rejection/correction affects the next
read; existing retention policies apply. Responses use `no-store`. Embedded
instructions are plain text, never code or model instructions.

## Frontend and verification

Skill Matrix is available in account/demo navigation with target selection,
refresh, loading/empty/error/retry states. Target changes immediately hide previous
results; stale responses cannot replace new context. Account changes remount the
private workspace. Semantic headers, keyboard scrolling, native source disclosures
and textual states support mobile/keyboard use without relying on color.

Concrete tests cover conflicts, missing/repeated evidence, breadth, retakes,
importance, aliases, excluded provenance, ownership, source versions, rubric
boundaries, malformed responses and UI races/retries. Exact verification is in
[PROJECT_STATUS.md](../PROJECT_STATUS.md). Saved assessment and interview creation
are implemented in their own services; this engine consumes eligible persisted
results and never manufactures them to populate an empty matrix. Current interview
providers produce simulation/model-assisted feedback, so they do not create the
deterministic interview evidence accepted by the existing eligibility contract.
