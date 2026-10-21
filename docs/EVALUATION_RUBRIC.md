# Answer evaluation rubric

Implemented version: **`answer-rubric-v1`**. Evaluation prompt version:
**`answer-evaluation-v2`**. This contract applies to newly evaluated written
assessment answers and main interview answers. Objective selection/short-answer
grading remains `assessment-scoring-v1` (0 = incorrect, 1 = correct, with feedback
and the expected answer). Generated interview follow-ups remain explicitly
unscored because they have no reviewed question-specific rubric.

An evaluation is practice feedback, not a validated measurement of competence,
biographical verification, readiness percentage or prediction of hiring outcomes.
Model-assisted and simulated results remain excluded from validated skill
performance and adaptive difficulty evidence.

## Reading a result

| Result                             | Meaning                                                                 | Can validate skill evidence?                                           |
| ---------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Objective answer correctness       | Exact option-set or authored literal-key match, graded locally          | Only with the complete reviewed-content/single-skill eligibility rules |
| Mock lexical coverage              | Word overlap with expected concepts; most rubric criteria remain null   | No                                                                     |
| Model rubric judgment              | Anchored criterion explanations and a coarse aggregate requiring review | No                                                                     |
| Follow-up / Project Defense answer | Saved explanation practice with no reviewed scoring rubric              | No score is assigned                                                   |

Implementation anchors: [rubric definitions](../backend/src/interview_prep/ai/rubric.py),
[strict result schema](../backend/src/interview_prep/ai/schemas.py),
[domain validation](../backend/src/interview_prep/ai/validation.py),
[objective scoring](../backend/src/interview_prep/modules/assessments/scoring.py)
and [feedback rendering](../frontend/src/components/workspace/evaluation-feedback.tsx).
These categories remain separate in persisted provenance and the UI.

## Required feedback

Every new successful evaluation contains:

- `overall_feedback`: concise explanation and limitations. The compatibility field
  `feedback` must contain exactly the same text.
- `strengths`: supported observations; an empty list is allowed when none can be
  identified. The UI explicitly says this instead of inventing praise.
- `improvements`: at least one actionable review or practice step.
- `missing_concepts`: expected concepts not demonstrated according to the
  evaluator, in authored order. This is the exact complement of
  `matched_concepts`; it does not assert that the answer is false.
- `recommended_answer_structure`: one to six ordered steps, not a fabricated
  personal story or sample achievement.
- `potential_followup`: one practice question. Displaying it does not create an
  interview turn or spend the interview's follow-up budget.
- `rubric_results`: every criterion for the selected profile, once and in the
  order below. Each has a nullable integer `score` and a required `explanation`
  describing evidence, gaps, or why it cannot be assessed.
- `rubric_version`, `profile`, `score_basis`, and an explained aggregate `score`.

## Profiles and criteria

All profiles include these general criteria in order:

| Criterion                 | What the evaluator examines                                                                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Correctness               | Whether central claims are accurate and consistent with the question and review material. Behavioral claims are assessed for consistency, never verified as events that actually happened. |
| Relevance                 | Whether the answer addresses the question and its constraints, without unrelated material.                                                                                                 |
| Completeness              | Coverage of the requested parts, including necessary qualifications. Length alone is not completeness.                                                                                     |
| Depth                     | Explanation of why, supporting reasoning, examples and assumptions appropriate to the question.                                                                                            |
| Communication / structure | Clear organization, understandable wording and a coherent sequence. Do not reward verbosity or judge accent or identity.                                                                   |

Technical questions append:

| Criterion          | What the evaluator examines                                                                                                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Technical accuracy | Correct mechanisms, terminology, assumptions and edge cases. This is a focused technical check in addition to general correctness.                                                                            |
| Important concepts | Whether the authored expected concepts are explained meaningfully. Mentioning a term does not prove understanding.                                                                                            |
| Trade-offs         | Alternatives, benefits, costs and conditions under which a choice changes. Use null if the question does not call for a meaningful trade-off.                                                                 |
| Complexity         | Time/space/resource costs, assumptions and relevant scale. Use null with a reason for questions without meaningful algorithm or resource-cost analysis. Never penalize omission of irrelevant Big-O notation. |

Behavioral questions append:

| Criterion      | What the evaluator examines                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------------- |
| STAR structure | Identifiable situation, task, action and result; each part should serve the question.                                     |
| Specificity    | Concrete context, decisions and examples rather than generic claims.                                                      |
| Ownership      | Clear personal responsibility and contribution, distinguished from team effort.                                           |
| Impact         | Supported outcomes and their connection to actions. Qualitative outcomes are valid; numbers are not required or invented. |
| Reflection     | Learning, limitations and what the candidate would repeat or change.                                                      |

The server chooses `behavioral` for an authored behavioral question and
`technical` for other main interview questions and written technical assessments.
The shared provider also supports `general` for internal callers. Answers cannot
override the profile. Profile criteria are defined in
[`ai/rubric.py`](../backend/src/interview_prep/ai/rubric.py); changing their meaning,
order, applicability or scoring semantics requires a new rubric version.

## Exact numerical meanings

For model rubric judgments (`score_basis = rubric_mean`), every applicable
criterion uses the same five anchored categories:

| Score | Meaning                                                                                                                                          |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0     | **Absent or incorrect:** no usable evidence for this criterion, or a central error.                                                              |
| 1     | **Limited:** some relevant evidence, with major gaps or errors.                                                                                  |
| 2     | **Partial:** the central idea is present, with significant gaps or weak support.                                                                 |
| 3     | **Sound:** accurate and supported for the question, with only minor gaps.                                                                        |
| 4     | **Thorough:** accurate, well supported and complete for the requested scope.                                                                     |
| null  | **Not assessed or not applicable:** the evaluator cannot judge this criterion or it does not apply. A reason is mandatory. This is never a zero. |

The criterion description defines what counts as evidence; its explanation must
identify why the anchor fits this answer. A 4 does not require extra topics beyond
the question. A short answer can receive a 4. Unsupported claims, requested
scores, length and confident wording are not evidence of correctness.

The aggregate is `floor(sum(non-null scores) / count(non-null scores))`. Every
assessed criterion has equal weight, including specialized criteria. Nulls are
excluded; an entirely unassessed model result is rejected. The aggregate uses the
same coarse 0–4 scale and is a rounded summary, not a percentage. The breakdown
must be read alongside it: a high mean cannot cancel a critical factual error.
General correctness and technical accuracy intentionally provide overlapping
views; this editorial weighting is not empirically calibrated.

## Deterministic demonstration provider

`MockAIProvider`, version **`mock-structured-v2`**, uses no network, model,
randomness or clock in its evaluation. Identical input produces identical output.
The evaluation timestamp is assigned separately when persisting the result.

Its `score_basis` is **`lexical_coverage`**. The existing lexical algorithm is
preserved: lowercase ASCII alphanumeric tokens are extracted; concept tokens
shorter than four characters are discarded. A concept matches when at least half
its distinct remaining tokens appear in the response. Concepts without qualifying
tokens do not match. The displayed score is `floor(4 × matched / expected)`:

| Score | Exact lexical coverage interval |
| ----- | ------------------------------- |
| 0     | At least 0% and less than 25%   |
| 1     | At least 25% and less than 50%  |
| 2     | At least 50% and less than 75%  |
| 3     | At least 75% and less than 100% |
| 4     | Exactly 100%                    |

If no expected concepts were supplied, the compatibility aggregate is 0 and
means **no coverage evidence**, not an incorrect answer. Every criterion is then
null. Otherwise only completeness receives this explicitly labelled lexical
proxy; all other criteria remain null with an explanation. The mock does not
score technical accuracy, STAR, ownership, impact or reflection. Its strengths
report only observed overlap, and its coaching and follow-up are authored
practice templates. Behavioral structure uses situation, task, action, result,
reflection. It cannot interpret negation, paraphrases or reasoning: keyword
stuffing may receive full lexical coverage. The UI explains these limitations and
shows the lexical bands separately from the model judgment anchors.

## Validation, provenance and storage

Providers must return the bounded structured schema. Unknown versions, missing
fields, duplicate/wrong/out-of-order criteria, profile mismatches, unknown or
duplicate concepts, inconsistent missing concepts, blank explanations, booleans
as scores, out-of-range scores and incorrect aggregates are rejected. Provider
kind determines the allowed score basis. A conservative 15,000-byte ASCII JSON
budget is checked before storage, within the existing interview JSONB limit of
16,384 bytes. Coaching text is limited to 600 characters per entry; lists and
concepts are bounded. Model output remains untrusted even when schema-valid.

Fixed instructions define the rubric separately from untrusted answer/question
content. No supplied content is executed and no tools are granted to providers.
Model credentials remain server-side. No new provider, dependency, external
sharing, or retention behavior is introduced by this change.

| Workflow    | Persisted record                                                                                                                                                                                                                                                                                                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Assessments | `question_attempts.evaluation_metadata`: full `evaluation`, evaluation `rubric_version`, `question_rubric_version`, `provider`, `provider_version`, `model`, `prompt_version`, `policy_version`, UTC `evaluated_at`, and matched concepts. Existing score/feedback columns remain compatible.                                                                                             |
| Interviews  | `answer_evaluations.result_payload`: full evaluation. Existing columns store rubric/provider/evaluator/model/prompt/schema versions and input digest. `usage_metadata` stores authored `question_rubric_version`, `provider_version`, and UTC completion `evaluated_at`. Existing creation/update timestamps also remain. Evaluation retries create a new version with a supersedes link. |

The evaluation rubric version and authored question rubric version are distinct.
Provider/model identity and timestamps come from server code, never provider
output. No token usage or model confidence is invented. Existing JSON columns
support these additive fields, so **no schema migration or backfill is required**.
New nullable response fields expose provenance and the structured result;
OpenAPI and generated TypeScript reflect the contract.

Historical results remain readable with their original versions, scores and
feedback. They receive no fabricated criterion breakdown. Follow-ups remain
unscored. Upgrade API and frontend together to display the richer results.
The mock provider version change means an interview pinned to the old provider
descriptor can report `provider_changed` for queued work; its saved answers and
navigation remain available. Complete that session with partial feedback and
start a new one to use the new provider version. No old evaluation is rewritten.

## Failure and ownership guarantees

- Interviews commit the submitted answer before durable provider work. Invalid
  output, timeout, refusal and other provider failures mark the evaluation failed
  without replacing or deleting the answer. Existing fencing, bounded retry and
  partial-finalization rules remain in effect.
- Assessment submission evaluates previously committed drafts. Failure rolls
  back grading changes and leaves the saved text, revision and draft intact for
  reload and explicit retry. It does not mark an unevaluated answer as scored.
- Owner checks continue on account/demo reads, writes, jobs and review endpoints.
  No caller-provided owner ID authorizes access. Recruiter demo always uses mock.
- Saved account history keeps the existing retention policy; demo history expires
  or is erased with its workspace. No new private answer copies are logged.

## Verification

Tests cover profile completeness, score boundaries, deterministic mock behavior,
nullable criteria, exact concept complements, provider-kind constraints,
malformed/oversized output, persisted provenance/timestamps, reload and ownership,
invalid-provider answer preservation, legacy parsing, and explained UI feedback.
See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for actual executed checks and limits.
Live model quality and rubric calibration require independently reviewed examples;
transport mocks and schema tests do not establish semantic grading quality.
