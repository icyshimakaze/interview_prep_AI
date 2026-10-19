# Adaptive question selection

Policy `adaptive-v1` is an explainable, deterministic scheduling algorithm. It
does not train a model, estimate competence probabilities, predict interview
outcomes, or treat simulation scores as evidence. All constants below are
editorial heuristics awaiting curriculum review and evaluation.

## Integration and inputs

Every new account/demo assessment uses the engine. Existing attempts retain their
frozen questions. Selection happens once at assessment start; results influence
the next assessment. The pure `select_questions(SelectionInput)` function can also
select a single question for a future interview workflow. It performs no I/O and
has no clock, mutable global state or random-number dependency.

| Input                       | Source and interpretation                                                                                                                                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inventory                   | Latest reviewed, published global/owned question versions, stable question ID, canonical concept, category/topic, mapped skills and editorial easy/medium/hard difficulty.                                                                            |
| Target job                  | Optional `target_id` on assessment configuration. Server checks ownership and uses the target's latest version. No automatic guess from job title.                                                                                                    |
| Skill importance            | Existing skill-evidence policy: confirmed Required/Preferred requirements; unreviewed lexical mentions are Mentioned; other skills are Low relevance. No target means no job evidence, not lack of usefulness.                                        |
| Candidate evidence          | Existing skill matrix determines practice/unknown/maintain. Resume mentions, interests and self-reports never establish ability or increase difficulty. Missing evidence is unknown, not failure.                                                     |
| Assessment performance      | Only completed, submitted, graded deterministic results from reviewed, single-skill questions with canonical concepts. Missing grades, skipped/draft responses, simulation and self-review are excluded.                                              |
| Interview performance       | Existing adapter requires a completed session, latest completed deterministic evaluation, matching complete rubric, evaluated turn and submitted answer. Success requires every dimension at anchor 3 of 4; invalid/missing evaluations are excluded. |
| Exposure/difficulty history | Owned assessment/interview allocations, including abandoned/skipped work, plus submitted bank practice. Exposure uses stable question identity across versions. Difficulty uses the actual historical version's level.                                |
| Topic coverage              | Counts in the last 20 exposures; full owned allocation count preserves the exploration cadence across truncated windows.                                                                                                                              |
| Seed                        | Assessment submission UUID. SHA-256 resolves otherwise equal choices reproducibly; this is not statistical random sampling.                                                                                                                           |

Eligibility is shared with [skill evidence](SKILL_EVIDENCE_ENGINE.md), rather than
implemented with looser duplicate rules. Multiple-skill questions can be selected,
but their outcomes cannot establish individual skill competence. Demo history
affects repetition/coverage only; demo results never adjust difficulty or establish
weakness. Text supplied in resumes, jobs and answers is never executed or used as
an instruction by the selector; no external service is called.

## Difficulty adjustment and cold start

Difficulty is per skill, not one global candidate rating. Without eligible
history, use **easy as a diagnostic**. The engine does not infer a high starting
level from seniority labels, a resume, or the job's seniority.

With history, initialize at the earliest eligible observed level in the bounded
window (easiest level for a tied first timestamp) and replay results in
timestamp/source-ID order. This allows previously
tested candidates to begin around their recorded difficulty. Then:

1. Two consecutive eligible successes on **distinct canonical concepts**, at or
   above the current target, raise the target one step, capped at hard.
2. Two consecutive eligible failures with distinct result IDs, at or below the
   current target, lower it one step, floored at easy. Repeated failure on the
   same concept still warrants relief; it does not require concept breadth.
3. A change of outcome resets the streak. An easier success or harder failure
   cannot move the target and also resets the streak. After a movement, consume
   the streak; the same pair cannot cause another movement.
4. Two failures while already at easy activate a 40-point topic-break penalty
   when the immediately preceding exposure is in that topic. A successful pair
   clears it. The diversity rule below also redirects after two topic allocations.

One observation never causes a level change. Repeating success on one concept,
including across channels, cannot supply a distinct pair. Missing/untrusted results are
ignored, not scored as failures. Two easier successes cannot keep raising a
medium target. New allocations in a batch update exposure only, never invent
performance or raise difficulty within the batch.

## Selection process and weights

The assessment inventory first applies the caller's **exact category, difficulty
and type filters**. An explicit difficulty overrides the adaptive preference;
the engine never changes that filter. For each requested slot:

1. Remove already selected batch questions. Exclude stable question IDs from the
   last **five exposures**, including previous versions. If none remain, choose
   from the least recently exposed questions and disclose cooldown relaxation.
2. Avoid canonical concepts from the last **two exposures** when alternatives
   exist. After two consecutive exposures in one category, choose another
   available category when possible.
3. Every **fourth** allocation restricts choice to the least-covered available
   topic in the last 20 exposures. This exploration can deliberately outweigh job
   relevance. Cadence uses the absolute exposure count, even beyond 1000 rows.
4. Choose one driving skill for each question: highest job importance, then
   greatest practice need, then stable skill key. Never add relevance across
   skills. Within each topic/driving-skill group, retain the closest available
   difficulty; prefer the easier neighbor on an equal distance.
5. Rank the remaining questions by the sum below. Ties prefer least recent use
   (unseen first), then SHA-256 of seed/absolute slot/question ID, then question ID.
6. Record the choice, component scores and reasons. Append its exposure and
   repeat, without replacement within the batch.

Let `r` be Required=3, Preferred=2, Mentioned=1, Low relevance=0; `n` be
practice=1, unknown=0.5, maintain=0. Let `c` be topic exposure count in the last
20 and `d` the ordinal distance from target difficulty (easy=0, medium=1, hard=2).

| Component           | Points                                                                   | Purpose                                                                               |
| ------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Job relevance       | `20 * r`                                                                 | Favor skills important to the selected job.                                           |
| Practice need       | `(10 + 10 * r) * n`                                                      | Give high-relevance weaknesses extra priority; missing data gets diagnostic priority. |
| Coverage            | `12 / (1 + c)`                                                           | Favor less-practiced topics between exploration turns.                                |
| Difficulty distance | `-18 * d`                                                                | Favor questions near the current target.                                              |
| Failure break       | `-40` when the easy-floor failure condition above applies, otherwise `0` | Encourage a break from repeated failure.                                              |

These are scheduling points, not percentages, calibrated confidence or a
readiness score. The trace records the exact sum and each contribution. Topic
diversity, concept spacing and question cooldowns precede scoring. For example,
a Required weak skill gets 100 relevance/need points; a Required maintained
skill gets 60. Exploration can nevertheless select a less-relevant topic.

## Repetition, loop prevention and finite inventory

Stable IDs block version-based repetition. Recent concepts discourage equivalent
variants. The two-topic streak rule and every-fourth exploration prevent an
important weak topic from monopolizing selection. Least-recent tie-breaking and
seeded ordering avoid always returning the alphabetically first question.
Bounded loops terminate after at most 12 selections; exhaustion is explicit.

The same unchanged input intentionally returns the same output. Callers must
persist allocations and pass updated history to make progress. The assessment
service does so under its existing principal lock; retrying a submission UUID
returns the saved attempt and its original trace. This is desired idempotency.
New UUIDs cannot bypass history cooldowns. Concurrent starts serialize allocation.

Finite catalogues necessarily repeat. If all eligible questions are recent, the
least-recent one is reused with a reason. If the nearest difficulty is unavailable
after filters/cooldowns, the nearest remaining difficulty is disclosed. Explicit
filters are never relaxed. If fewer distinct questions exist than requested, the
pure engine returns a shorter result with a notice; assessment start rejects it
with `409 assessment_pool` before writing an attempt.

## API, persistence and bounds

Existing assessment start payloads work unchanged. To target a job, include its
owned UUID as `target_id`; omit `difficulty` or send null to let the engine choose
across levels. The frontend retains its existing configuration form; selecting
a target specifically for an assessment is currently an API capability.

Attempt responses add nullable `selection`, containing `policy_version`, ordered
`choices` (IDs, topic, driving skill, actual/target difficulty, score components,
reasons) and notices. It contains no response text, resume excerpt, answer key,
rubric or provider secret. The trace is frozen alongside existing configuration
JSON; `context_version` is `adaptive-v1`. The grading policy is unchanged.
Pre-adaptive configurations without a target or trace remain readable/replayable.
No schema migration or new retention store is required.

Release the matched API/client contract together. A rollback to an older API that
rejects extra configuration keys would not read newly created adaptive attempts;
retain this backward-compatible configuration reader in any rollback build.
Do not erase traces or rewrite historical allocations to accommodate an old reader.

Inventory is limited to 1000 candidates, at most 100 skill mappings per question
and 10000 mappings overall; overflow fails with `409 adaptive_pool_limit` rather
than silently biasing the inventory. More than 1000 skill-context rows fails with
`409 adaptive_context_limit`. Existing evidence adapters bound each input category
at 1000 rows; partial evidence disables performance eligibility and the trace
discloses the limitation. The pure contract accepts at most 2000 performance
observations, 1000 exposures, and a batch of 1–12. Duplicate question, skill-context
or performance IDs and inconsistent history counts fail validation.

Exposure history retains only the latest 1000 rows for selection; the total count
is queried separately. Database adapters resolve identity from the authenticated
principal and scope every private source and content lookup. Account/demo auth,
CSRF, no-store headers, retry limits and immutable-attempt rules are unchanged.
Traces follow assessment retention: account history persists until principal
erasure; demo history expires with its workspace. No external sharing is added.

## Limitations and future evolution

- The catalogue currently has 29 authored prompts across all types, with limited
  coverage at each level. Diversity and level matching cannot create missing
  questions. Category labels are a coarse proxy for topic diversity.
- Editorial difficulty and these weights are not empirically calibrated. A small
  number of eligible observations supports only local scheduling decisions.
  Initializing from the earliest observed level is a transparent prior, not a
  claim that the candidate has mastered that level.
- No time-based forgetting, learning disability/accommodation model, response-time
  inference, semantic duplicate detection or prerequisite graph is implemented.
  Difficulty can oscillate after new opposite pairs; hysteresis reduces reaction
  to single answers but cannot guarantee monotonic progress.
- Repetition history is an allocation proxy: an abandoned assessment's allocated
  questions count even if never viewed. Browsing without a stored response is not
  tracked. Deleting bank practice removes its exposure from this history.
- A multi-skill question uses one driver and may contain another skill at a less
  suitable level. Automatic role-title matching is deliberately absent; the
  selected job's skill evidence provides relevance.
- Selection is between assessments, not an adaptive standardized test. The
  existing interview schema contributes eligible history, but a production
  interview workflow is separate work. No learning-outcome improvement is claimed.
- Future versions can add reviewed prerequisites, explicit accommodations,
  independently calibrated question difficulty, exposure events, and evidence
  aging. Evaluate changes using reproducible scenarios, coverage/repetition and
  completion diagnostics before changing weights. Any learned policy would need
  real consented data, held-out evaluation, provenance and a deterministic fallback;
  none is included or represented as implemented here.

Unit tests cover cold/strong/weak/role-specific candidates, sparse/missing data,
up/down transitions, caps, invalid evidence, repetition across versions/concepts,
diversity, exhaustion, deterministic replay, input validation and long sequences.
Database/API tests exercise owned targets, history ordering, trace persistence,
retry compatibility, exact filters and real evidence eligibility.
