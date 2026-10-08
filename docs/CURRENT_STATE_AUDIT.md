# Current State Audit

Audit date: 2026-10-08 (Asia/Calcutta). Branch: `rebuild/professional-v2`. Audited commit: `48fcd90` (`Add files via upload`). Scope: technical and product audit before a major V2 rebuild; no implementation or behavior changes.

## Executive summary

The current project is a small Streamlit demonstration of an interview-preparation workflow. It collects self-reported confidence in six topics, summarizes those ratings, displays predetermined study suggestions, samples question titles, and assigns a readiness label. It does not assess answers, execute submissions, measure learning over time, or predict interview outcomes using validated evidence.

Only one feature uses machine learning: a decision tree fitted on eight hardcoded score/label examples. This is real classifier code, but its output is an unvalidated classification of the user's average self-rating. There is no generative AI, language model, AI question generation, AI assessment, or AI roadmap generation. The classifier adds dependency and execution complexity without establishing useful predictive validity.

The highest-priority findings are:

| Priority | Finding | Consequence |
| --- | --- | --- |
| High | Homepage displays fixed `100+` students, `500+` questions, and `87%` success. The repository contains 15 question titles and no usage/outcome records. | Product claims are unsupported; the question-count claim conflicts with the implemented bank. |
| High | Assessment is six sliders; readiness is fitted to eight authored examples. | Confidence can be mistaken for demonstrated skill or interview readiness. |
| High | Progress consists of the latest ratings and a fixed target of 100. | There is no historical progress, completed work, or evidence of improvement. |
| High | No durable user storage; profile and assessment widgets reset after navigation. | Users can lose input or overwrite previous ratings unintentionally. |
| High | The unmodified application cannot start in the inspected local environment. | pandas/NumPy incompatibility is the first failure; Matplotlib also fails and scikit-learn is missing. |
| Medium | Difficulty changes a heading, not question selection. | The control promises behavior it does not implement. |
| Medium | All business rules and UI live in one top-level script with no tests or data schema. | Changes are difficult to isolate and verify. |

Preserve the preparation workflow, the idea of topic-level feedback, and the small content seed after editorial review. Replace the unsupported readiness model, marketing metrics, score-only progress, and fragile state handling. A simpler, truthful baseline is preferable to retaining machinery solely because it exists.

### Scope and evidence

Every repository content file was read in full:

| File | Size / scope | Purpose |
| --- | --- | --- |
| [app.py](../app.py) | 277 lines; 8,649 bytes | Entire application, navigation, state, rules, visualizations, and classifier. |
| [questions.json](../questions.json) | 25 lines; 580 bytes | Three topic arrays containing five question titles each. |
| [requirements.txt](../requirements.txt) | Four package names; 43 bytes | Unpinned direct dependencies. |

Tracked and untracked file inventories and ancestor/repository instruction-file checks found no additional application, configuration, documentation, tests, or `AGENTS.md` files. The local `.dist` directory was empty. Git metadata was inspected for branch, status, and history; it is not application source. The repository had one commit and a clean working tree before this audit.

Evidence references below use line numbers in the audited source. Findings about missing functionality apply to this checkout. No deployed service, external database, hosting account, real user dataset, or private operational configuration was available for inspection.

## Current architecture

### Execution and Streamlit structure

`app.py:2-7` imports pandas, Streamlit, Matplotlib, scikit-learn, `random`, and `json`. At each script execution, it loads `questions.json` relative to the process working directory (`app.py:13-14`), builds a sidebar radio menu (`18-29`), initializes three application state keys (`31-38`), and executes one of seven `if`/`elif` view branches.

The logical data flow is:

```text
Browser widgets <-> Streamlit Python process
                      |
                      +-- questions.json -> random sample -> displayed titles
                      +-- session scores -> mean/thresholds -> dashboard
                      |                  -> fixed topic text -> roadmap
                      |                  -> current-score table
                      |                  -> eight-example tree -> readiness label
                      +-- session name/role -> stored but unused
```

There are no application functions or classes, service boundaries, API endpoints, background jobs, database, repository layer, separate frontend, or model artifact. Streamlit owns rendering and widget interaction. This small single-process shape is appropriate for a prototype; the problem is the coupling of presentation, policy, content, and storage assumptions as the product grows.

### State management and persistence

| State | How it is written | How it is used / retained |
| --- | --- | --- |
| `scores` | Replaced with six slider values on Analyze Skills (`115-124`). | Dashboard, roadmap, and progress read the latest dictionary in the current session. No timestamp or previous version. |
| `student_name` | Save Profile (`97`). | Never read by another feature or used to repopulate the form. |
| `role` | Save Profile (`98`). | Never affects questions, assessment, recommendations, or readiness. |
| Branch and year | Local widget return values (`89-94`). | Not copied into application state by Save Profile; no durable record. |
| Selected questions | Local `questions` variable inside a button branch (`232-237`). | Not saved; output vanishes on a subsequent rerun. |

The application-level keys persist across ordinary navigation in the same session. The widgets themselves are not initialized from those saved values. Isolated Streamlit checks confirmed that returning to the profile shows blank/default fields while the saved name and role still exist; returning to assessment shows six 50s while the saved score dictionary can contain different values. A new submission overwrites that dictionary.

Streamlit documents that Session State is tied to the WebSocket session and resets on a browser reload. It also removes the state of widgets not rendered during a run. These framework semantics explain why explicit state restoration and durable storage are needed here. See [Session State documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state) and [widget lifecycle documentation](https://docs.streamlit.io/develop/concepts/architecture/widget-behavior).

There are no file writes for user data, database calls, exports, migrations, backups, user identifiers, or cross-device recovery. `questions.json` is bundled content, not a user-data persistence mechanism. Session isolation provided by Streamlit is not account-based authentication or durable ownership.

## Existing features

| Screen | Actual implementation | Important limits | Evidence |
| --- | --- | --- | --- |
| Home | Marketing copy, three fixed metrics, capability cards. | No analytics behind the metrics. | `app.py:40-74` |
| Student Profile | Name, five roles, five education branches, four year options; saves name and role to session. | Empty names accepted; education choices not saved; profile unused elsewhere. | `76-100` |
| Skill Assessment | Six integer sliders from 0 to 100, default 50; saves a score dictionary. | Self-report only; no questions, answers, grading, timing, rubric, or attempt record. | `102-126` |
| Dashboard | Mean rating, weak/strong topic counts, bar chart, topic labels. | Describes confidence input, not independently measured performance. | `128-168` |
| AI Roadmap | Four hardcoded weekly strings for each topic rated below 50. | No generated content, integrated schedule, resources, milestones, or completion state. | `170-221` |
| Interview Questions | Select topic and difficulty; randomly display three existing titles. | Difficulty is unused in selection; no answering or review workflow. | `223-237` |
| Progress Tracker | Latest ratings beside target 100; classifier label and feedback. | No history, actual progress, or validated interview prediction. | `239-277` |

### Assessment and dashboard rules

The topics are Arrays, Linked List, Stack, Queue, DBMS, and OS. The UI calls the last topic Operating System; the saved key is `OS`. Scores below 50 are weak; scores of at least 75 are strong. Values from 50 through 74 are neither. Each topic contributes equally to the arithmetic mean (`140-143`). These are authored rules without a documented rubric or validation.

Default submission requires no demonstration of knowledge and stores six ratings of 50. A 50 is not weak, so the roadmap displays “Excellent Performance! Keep practicing advanced problems.” The absence of a below-threshold rating is incorrectly treated as excellent performance. The dashboard's percentage formatting suggests a measured score despite having no item count or grading denominator.

An average also hides uneven ability: `[100, 100, 100, 0, 0, 0]` and `[50, 50, 50, 50, 50, 50]` both produce 50. The readiness model receives only that average, so it cannot distinguish these profiles. The saved role does not change topic relevance or weights.

### Question bank and selection

The JSON is valid UTF-8 JSON. It contains 15 nonempty, unique strings, distributed as follows:

| Topic | Existing titles |
| --- | --- |
| Arrays | Find duplicate element in array; Maximum subarray sum; Rotate array by k steps; Two Sum Problem; Merge two sorted arrays. |
| Linked List | Reverse Linked List; Detect cycle in linked list; Merge two linked lists; Find middle node; Add Two Numbers. |
| Stack | Valid Parentheses; Implement stack using queue; Next Greater Element; Min Stack; Postfix Evaluation. |

Queue, DBMS, and OS are assessed and have roadmap text but have no questions. The five target roles have no distinct content coverage. Records lack IDs, difficulty, full problem statements, input/output examples, constraints, answers, explanations, rubrics, tags, prerequisites, provenance, license information, and content versions. These strings are useful topic prompts, not a complete assessment dataset. Some are ambiguous: “Merge two linked lists” does not specify sorted inputs, and the duplicate-array prompt does not define its constraints.

`random.sample(question_bank[topic], 3)` selects three distinct entries within a request. It does not prevent repeats across requests, adapt to weak topics, consider the selected role, or use difficulty. Changing the difficulty changes only the subheading. An isolated check with the same RNG state produced identical questions for Easy and Hard. Production randomness is not recorded, so previous selections cannot be reconstructed.

The current five-item arrays satisfy the three-item sample size. A future topic with fewer than three entries would raise `ValueError`; an empty, malformed, missing, or differently structured bank has no validation or recovery path. Because loading is unconditional, even Home depends on the file being readable from the launch directory.

### Readiness prediction: what is and is not AI

`app.py:259-264` constructs this training data on every populated Progress Tracker execution:

| Input average | Assigned label |
| --- | --- |
| 20, 35 | Low |
| 45, 55 | Medium |
| 65, 75 | Good |
| 85, 95 | Excellent |

A `DecisionTreeClassifier` is fitted and predicts one label from the current mean. This is genuine use of a supervised machine-learning algorithm. However, the examples are literals authored in source, not observations of students or interview outcomes. There is no provenance, held-out validation, calibration, accuracy measurement, model version, persisted artifact, or evidence that the labels represent readiness. It effectively learns an authored set of score bands; the package choice does not make those bands scientifically grounded.

No interview answers, code, role expectations, learning history, or employer outcomes enter this model. A user can obtain a high input simply by moving sliders. Retraining on each page run has no learning benefit because the dataset is unchanged. An explicit, documented confidence-summary rule would be simpler if such labels are retained. It should not claim to predict hiring success.

The actual classifier was not executed in this environment because scikit-learn is absent. The above description follows the complete fit/predict code and its literal data; no measured predictive accuracy or exact runtime boundary behavior is claimed.

### Roadmap and progress

There are six four-week outlines, or 24 authored study suggestions. Arrays covers basics, sliding window, prefix sums, and practice; Linked List covers basics, reversal, fast/slow pointers, and practice; Stack covers basics, monotonic stacks, expression evaluation, and advanced problems; Queue covers basics, circular/priority queues, and graph applications; DBMS covers SQL, joins, normalization, and transactions/indexing; OS covers processes/threads, scheduling, deadlock, and memory management.

Only topics below 50 display an outline. There is no ordering by severity, estimated effort, available study time, role, prerequisites, assessment evidence, or completion. If several topics are weak, each gets its own Week 1 through Week 4, with no combined workload or schedule. Titles mentioning LeetCode or interview problems are not linked learning resources.

Progress Tracker creates a table from the same latest scores and a target of 100 for every topic (`248-254`). It stores no attempts, dates, deltas, completed questions, milestones, streaks, or task status. “You are improving” (`272`) is unsupported because no previous result is available for comparison.

## Technical weaknesses

### Dependencies and local execution

| Dependency | Current use | Assessment |
| --- | --- | --- |
| Streamlit | All UI and in-session state. | Reasonable prototype foundation; no version bound or supported runtime declared. |
| pandas | Two small tables of six topics. | Convenient, but this tiny data model alone does not justify retaining it in V2. |
| Matplotlib | One bar chart. | Adds plotting dependencies and resource management for a simple visualization. |
| scikit-learn | Eight-example decision tree. | Unnecessary for a transparent authored score-band rule. |
| `random`, `json` | Sampling and file parsing. | Python standard library; no external AI integration. |

`requirements.txt` has no pins, upper/lower bounds, lockfile, or Python version. There is no isolated-environment setup or reproducible installation procedure. Installed package metadata showed Python 3.12.1, Streamlit 1.60.0, pandas 2.1.4, Matplotlib 3.8.2, and NumPy 2.5.3; scikit-learn was not installed. NumPy is a transitive dependency, not listed directly.

An unmodified Streamlit AppTest startup failed at the first pandas import with `ValueError: numpy.dtype size changed, may indicate binary incompatibility`. Separate import probes confirmed `matplotlib.pyplot` fails with `ImportError: numpy.core.multiarray failed to import` and `sklearn.tree` fails with `ModuleNotFoundError`. These are verified properties of this local environment, not proof that every fresh installation fails. Dependencies were not installed, upgraded, or repaired during the audit.

### Reliability and maintainability

- Top-level imports, disk reads, UI execution, calculations, and model fitting are coupled. Importing the module is not a safe way to access reusable business logic.
- Question loading depends on the process working directory instead of the script location and has no explicit text encoding, schema check, exception handling, or fallback. The current ASCII-only question text does not itself cause an encoding failure.
- Topic names are repeated across slider labels, score keys, roadmap branches, and JSON. Coverage already differs between these locations. There is no canonical topic registry or stable identifier system.
- The mean and weak-topic rules are duplicated. Their assumptions are not centralized, named, versioned, or explained to users.
- The JSON is reopened on each rerun; the classifier is refitted on each populated progress run. Neither is expensive at this scale, but both are unnecessary repeated work.
- A Matplotlib figure is created in the dashboard with no explicit `plt.close(fig)` (`151-154`). Potential retained-figure/resource growth should be checked if this implementation is retained; a runtime leak was not measured.
- There are no project tests, CI checks, typing contracts, lint/format configuration, README, architecture notes, or license in the audited baseline. The single upload commit provides little design history.
- No data validation boundary protects against future bank schema changes. Sliders enforce current UI score bounds, but the score dictionary has no independent domain validation.

### Testability

Pure calculations and selection policies cannot be imported independently of the UI. Real classification and plotting also require their full dependencies, even for Home, because all imports occur before navigation. Random selection has no injectable RNG or recorded seed. There are no existing regression tests for thresholds, default submissions, navigation, invalid question banks, or save semantics.

V2 should make scoring, selection, and roadmap rules small deterministic units. Useful tests should verify user outcomes: real difficulty filtering, empty/small pools, score provenance, preserved drafts, immutable attempt history, prerequisite warnings, and persistence recovery. Streamlit AppTest can cover widget flows if Streamlit is retained. No permanent test suite or V2 code was added by this audit.

### Deployment readiness

This checkout is a prototype, not a verified production release. `app.py` and `requirements.txt` can serve as entry-point conventions for a compatible Streamlit host, but there is no recorded supported runtime, launch guide, deploy configuration, container, CI pipeline, health/smoke verification, dependency vulnerability assessment, backup strategy, or operational observability. None of those must use a complex platform; the missing requirement is a reproducible, verified operational path.

Launch must resolve `questions.json` from the expected directory. Serving durable accounts would also require authentication, authorization, storage, and ownership policies. Session-only state does not provide recovery after restart or a reliable basis for multiple application instances. TLS, host access controls, framework security settings, logging behavior, and deployment status cannot be established from this repository. No public deployment or live-service test was performed.

## Product weaknesses

- There is no completed learning loop: users cannot answer a question, receive evidence-based feedback, practice a recommended task, mark it complete, and compare a later result.
- Profile collection has no payoff. Selecting ML Engineer or Data Analyst yields the same generic six-topic flow, and education details are not saved.
- Users have no explanation of what a rating of 40, 60, or 80 means. Defaults can create apparently meaningful analysis without any deliberate assessment.
- Recommendations and dashboard categories disagree in tone: six 50s produce no weak topics and an “Excellent Performance” roadmap message, although none qualifies as strong under the dashboard's 75 threshold.
- There is no goal date, study capacity, learning-resource catalog, or prioritization. Multiple four-week lists are not a coordinated plan.
- Difficulty and save controls imply capabilities beyond their implementation. Generated output disappearing after interaction further reduces confidence in the product.
- Navigation has useful empty-state warnings for assessment-dependent views, but no guided next action, saved-state indicator, recovery affordance, or assessment completion history.
- The UI uses standard labeled Streamlit controls, a simple sidebar, and readable topic summaries. These are useful foundations. Text quality issues include “Preferrred Role,” “Skill Assement,” inconsistent spacing in role names, and inconsistent OS naming.
- The chart does not explicitly fix a 0-100 score axis, which can impair comparisons between visits. Weakness messages use error styling even though a lower confidence rating is not an application error. These merit UX review rather than being treated as defects proven by visual testing.
- Browser layout, mobile behavior, keyboard navigation, contrast, and screen-reader accessibility were not visually or interactively audited in a real browser. Source emoji are valid UTF-8; garbled characters from a default shell read were a terminal-decoding artifact, not evidence of corrupted UI text.

## Misleading functionality

| Claim or label | Evidence-based reality | Recommended disposition |
| --- | --- | --- |
| AI-Powered Analysis / analyze coding skills | Arithmetic over self-ratings; no submitted code or answers (`43-47`, `106-124`, `140-143`). | Call it a self-assessment until measured assessment exists. |
| AI Learning Roadmap | Fixed strings chosen by `< 50` checks (`179-221`). No AI call. | Present transparent curated recommendations, or later implement and evaluate a genuine optional AI feature. |
| Interview Question Generator | Randomly retrieves three bank titles (`232-237`). No generated question content. | Name it question selection/practice unless generation is actually implemented. |
| Easy / Medium / Hard | Same topic pool; selected difficulty only changes the heading (`229-234`). | Add validated difficulty metadata and filtering, or remove the control. |
| AI Readiness Prediction | Actual ML algorithm, but trained solely on eight hardcoded examples (`259-266`). | Replace with a transparent evidence summary; do not equate this with validated readiness. |
| Progress Tracker / “You are improving” | Only the latest self-ratings; no temporal evidence (`248-272`). | Record real attempts and compare comparable measurements before making trend claims. |
| Profile Saved Successfully | Only name and role are saved in the active session; form does not restore them (`89-100`). | Make save scope truthful and restore persisted fields. |
| Questions Available: 500+ | Exactly 15 titles in the only bank (`53`; all of `questions.json`). | Derive counts from approved content. |
| Students Practicing: 100+ | Literal string, no user or activity counting (`52`). | Remove until backed by defined, auditable metrics. |
| Success Rate: 87% | Literal string, no outcomes, denominator, period, or measurement (`54`). | Remove; do not migrate into V2 metrics or copy. |

The absence of an LLM does not mean no AI algorithm exists: the decision tree is present. Conversely, its presence does not validate all AI-branded features. There are no model-provider SDKs, prompts, embeddings, retrieval pipelines, provider credentials, or model API requests in any repository file. No claim is made about the author's intent; the audit assesses what the implementation can substantiate.

## Security/privacy concerns

### Observed exposure and safeguards

The source contains no credentials, access tokens, user-upload handling, shell execution, dynamic `eval`, database query construction, unsafe HTML flag, or explicit external-service calls. The question bank is a fixed local JSON file; `json.load` is not executable deserialization. These limit the application-specific attack surface. There is no evidence here of a secret leak, SQL injection, remote-code execution path, or cross-user data breach. This is source review, not a penetration test or dependency-CVE scan.

There is no authentication, authorization, durable user ownership, application-level rate limiting, or audit trail. For a public anonymous prototype, lack of accounts is a product constraint; it becomes a design gap if private histories are added. Existing Streamlit per-session state should not be misreported as a shared global store, but it cannot authenticate a returning person.

Unpinned dependencies make builds variable and complicate vulnerability tracking. No deployment configuration establishes TLS, network exposure, framework security options, or access boundaries. The code does not explicitly disable Streamlit protections; lack of repository configuration is not proof that a deployed host lacks them. Input length limits and validation are absent for the name, although the present code does not subsequently render or interpolate that name into a sensitive sink.

### Data handling and privacy

The form requests a name, desired role, education branch, and year; the application also processes subjective ability ratings. Browser input is handled by the server-side Streamlit session, so “no database” does not mean “data never leaves the device.” Name and role are unnecessary collection under the current behavior because they are never used, and branch/year provide no saved benefit.

There is no privacy notice, defined retention policy, explicit session-lifetime disclosure, export/delete workflow, or documented handling of server logs and host telemetry. No explicit application code sends this information to an AI provider or other external API. Framework/hosting telemetry and access logs were not audited and cannot be inferred absent solely from the application code. No durable personal records are present in the repository to migrate.

V2 should minimize required personal data and state the actual storage and retention behavior. If accounts are introduced, enforce ownership for every persisted record and provide deletion/export semantics. If an AI provider is introduced, document exactly which inputs leave the application and why before collecting additional personal information. These are future design needs, not claims that such integrations exist today.

## Valuable components to preserve

- The conceptual flow: establish goals, assess relevant skills, identify gaps, practice, follow a plan, and review progress.
- Topic-level summaries and understandable visual feedback, provided they distinguish confidence, measured performance, and coverage.
- Self-ratings as optional confidence inputs that complement assessment rather than substitute for it.
- The 15 unique question titles as a small editorial seed. Expand each into a reviewed, attributable, structured record before using it for scoring.
- The six topic labels and 24 roadmap suggestions as starting material for a consistent topic catalog and curated learning tasks. Their pedagogy and ordering still need review.
- Role choices as examples of future preparation tracks, after normalization and research into the skills each track needs.
- The simple navigation and existing assessment-prerequisite warnings. Streamlit may remain useful for a prototype or internal tool if it meets the chosen V2 experience.

No current implementation needs to be retained merely for compatibility: there is no published API, durable schema, or model artifact in the checkout. Keep the audited commit as a reference; preserve useful concepts without inheriting artificial complexity.

## Components to replace

| Current component | Replacement direction |
| --- | --- |
| Eight-example readiness tree | Evidence-based results with transparent rules and explicit limits. Only introduce a predictive model after obtaining suitable data and validating it. |
| Fabricated/unsupported homepage metrics | Remove initially; later derive real content/activity metrics with stated definitions. |
| Sliders presented as skill assessment | Actual graded attempts and rubrics; keep optional confidence ratings separately. |
| Three-string random question output | Structured question practice with real filtering, stable selection, answer/review state, and sensible small-pool handling. |
| Inline roadmap `if` chains | Curated task data and a simple policy using observed gaps, prerequisites, and available time. |
| Latest-score progress table | Timestamped attempt and completion history with comparable before/after results. |
| Session-only save semantics | Deliberate draft state plus storage appropriate to the chosen account/anonymous model. |
| Monolithic top-level policy code | Small cohesive modules separating UI, domain rules, content validation, and persistence. |
| Unpinned environment | Supported Python version, reproducible dependencies, and verified startup. |

Do not automatically carry pandas, Matplotlib, or scikit-learn into the new stack. Select packages from actual requirements. Do not introduce microservices, queues, vector databases, agent frameworks, or an LLM simply to justify the V2 label. The audit does not decide whether Streamlit must be kept or replaced.

## Migration recommendations

### What data exists to migrate

| Asset | Migration recommendation |
| --- | --- |
| 15 question strings | Import as draft content with stable IDs, original topic mapping, and source commit. Preserve original text, then add reviewed statements, real difficulty, answers/rubrics, explanations, and provenance. Do not invent difficulty labels from the old selector. |
| Six topic names | Normalize to stable IDs; map `Operating System` and `OS` to one topic. Preserve display-name aliases where useful. |
| 24 roadmap strings | Treat as editorial suggestions, not scheduled tasks, completed work, or validated learning pathways. Review prerequisites and resource sources before publishing. |
| Five role names | Normalize spacing and define actual role-to-skill coverage if those roles remain in scope. |
| Eight classifier examples | Retain only as historical audit evidence, not a training corpus or real outcome dataset. |
| Homepage metrics | Do not migrate as facts or analytics. |
| User profiles, scores, attempts | No durable user dataset exists in the checkout. There is no attempt history to import. |

A still-running external instance could have transient in-memory ratings, but no such instance or export was inspected. If genuine users need continuity, inventory that deployment before shutdown and consider an explicit, consented export of what actually exists. Any imported ratings must retain the provenance `legacy self-report`; they must not become graded answers, dated historical attempts, or validated readiness labels. Unknown timestamps must remain unknown.

### Migration sequence and acceptance criteria

1. Retain the original source and commit as the baseline; finish V2 product and data decisions before implementation.
2. Define the minimum truthful learning loop, supported roles/topics, question quality bar, assessment rubric, and distinction between confidence and measured results.
3. Define a small versioned content schema and stable IDs. Validate that the initial import has exactly 15 unique draft questions, three populated legacy topic groups, and explicit gaps for the other three topics.
4. Review content provenance and licensing before redistribution. The repository provides no license or question-source information; do not assume attribution from familiar titles.
5. Choose storage and identity based on actual continuity requirements. Suggested logical records are topics, questions, attempts, answer evaluations, plan tasks, and task completions; profiles are needed only if they serve a purpose. Use content/rubric versions so historical results remain interpretable.
6. Build and verify one end-to-end practice flow before expanding role coverage or adding AI. Test state restoration, durable writes, question filtering, assessment boundaries, and history comparisons.
7. Remove unsupported marketing and verify every displayed count/claim against its source. Validate a fresh environment and startup path before a deployment decision.

This is a recommended sequence, not implemented scope or an approved V2 stack. Migration should preserve useful content and provenance; there is no need to preserve the current dependency shape or pretend historical data exists.

## V2 opportunities

The highest-value opportunity is a trustworthy practice product with a complete feedback loop: choose a relevant skill, attempt a clear question, receive rubric-backed feedback, practice a specific gap, and see evidence of improvement over time.

- Define role-specific skill coverage and question difficulty through curated metadata; explain why a task was recommended.
- Make assessment distinguish correct answers, partial understanding, confidence, and untested areas. Avoid a single readiness percentage that conceals gaps or uncertainty.
- Provide saved practice sessions, answer review, resource-linked study tasks, achievable scheduling, and persistent completion history.
- Measure progress from comparable attempts and coverage. Show insufficient evidence when appropriate, rather than inventing a trend or prediction.
- Use a simple modular application and data store that fit the agreed user experience and deployment needs. Final framework and database choices are deferred.
- If AI has a justified role, start with a narrow feature such as draft explanations or rubric-assisted feedback, backed by reviewed content and evaluation cases. Make provider use visible, validate outputs, set cost/latency limits, and preserve a useful fallback when the provider is unavailable. These capabilities do not exist in V1.
- Keep factual claims auditable: content counts from content, completion from events, and outcome claims only from an appropriately defined dataset.

### Verification performed and limits

The audit used read-only source inspection, local Python probes, and an in-memory UI harness. It did not edit application files, change dependencies, create a database, commit, or push.

| Check | Result |
| --- | --- |
| Repository inventory and full reading | All three tracked content files read; no additional relevant files found; `.dist` empty. |
| Python syntax | `ast.parse` and in-memory `compile` passed for `app.py`. |
| JSON integrity | Parsing passed; 3 topics, 15 unique nonempty strings, 5 per topic. Missing question coverage: Queue, DBMS, OS. |
| Encoding | UTF-8 decoding confirmed intact emoji in Python source. |
| Dependency metadata and import probes | pandas/NumPy incompatibility; Matplotlib import failure; scikit-learn absent. |
| Unmodified application startup | Streamlit AppTest failed at pandas import before any screen rendered. |
| Isolated Streamlit UI checks | Passed checks for static homepage values, empty-score guards, empty-name acceptance, saved name/role, reset profile/education widgets, six default ratings, default “Excellent Performance” message, weak Arrays roadmap, reset sliders with retained submitted score, three sampled titles, ignored difficulty, and disappearing output on rerun. |
| AI and data-flow tracing | All inference, sampling, state writes, thresholds, and roadmap branches reviewed directly; no LLM/API integration found. |
| Source integrity | SHA-256 baselines recorded and compared after documentation creation; original source/data/dependency files unchanged. |

For isolated UI checks, the pandas, Matplotlib, and scikit-learn import statements were omitted from an in-memory source string passed to Streamlit AppTest. Repository source was not edited. The checked screens use actual Streamlit widgets; populated Dashboard and Progress Tracker paths were not executed in that harness. The sample comparison reset Python's RNG to the same seed to isolate difficulty behavior. These checks establish the described UI/state defects, not successful operation of the original full application.

No end-to-end browser rendering, classifier runtime, populated chart/table integration, load test, multi-instance deployment, external data inventory, security scan, or accessibility certification was performed. This report distinguishes those limits from the verified source and UI findings.

Recorded original SHA-256 values:

```text
app.py           5a6abc9d300423ecbe75ed4afc53c188ea840d34e744b2aebd449a27be622f99
questions.json   8324fd68ac2c257b5d5c0d4f82406e16b2eb62ea22fbd7a4ffb618ba856a95b9
requirements.txt 0cbb47835edb89b4addfff09725e98a7aacc8f52e291a9e6e6bffeb2076f1eff
```
