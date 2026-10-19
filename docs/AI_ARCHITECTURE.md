# AI-provider architecture

The backend defaults to **`AI_PROVIDER=mock`**. Local development, automated tests,
CI and the recruiter demo require neither an AI credential nor a model server.
The mock is an explicitly labelled deterministic simulation, not machine learning
or a prediction of competence. Optional account integrations are available for a
configured Ollama server and OpenAI's Responses API. Recruiter demo evaluation is
always pinned to mock independently of the account provider.

## Interface and boundaries

`backend/src/interview_prep/ai/provider.py` defines the asynchronous `AIProvider`
protocol. All implementations expose the same six typed operations:

| Method                         | Input                                                                   | Validated data output                                                                      |
| ------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `analyze_resume()`             | `ResumeInput`: extracted document text                                  | `ResumeAnalysis`: summary, skill mentions with exact source spans, improvement suggestions |
| `analyze_job_description()`    | `JobInput`: document text                                               | `JobAnalysis`: summary, source-backed requirement suggestions, review notes                |
| `evaluate_answer()`            | `AnswerInput`: question, answer, expected concepts, rubric descriptions | `AnswerEvaluation`: integer 0–4 score, feedback, matched concepts                          |
| `generate_followup()`          | `FollowupInput`: answer context and recent questions                    | `Followup`: one non-repeated question and rationale                                        |
| `recommend_roadmap()`          | `RoadmapInput`: explicit topics and weekly minutes                      | `Roadmap`: one bounded practice step per topic, minutes and concrete success checks        |
| `generate_project_questions()` | `ProjectInput`: project text and requested count                        | `ProjectQuestions`: distinct questions, focus and exact supporting excerpts                |

Each method returns `ProviderResult[T]`, containing validated `data` and
server-generated `provenance`: provider name/version, configured model identifier
(null for mock), `simulation` or `model_assisted`, prompt version and disclosure.
The model cannot choose its provenance or claim a `deterministic` result kind.
Configured model aliases are recorded as configured, not represented as resolved
immutable model snapshots. Scores and suggestions never establish job readiness.

Responsibilities are separate:

- `schemas.py`: bounded typed inputs/results, no provider-specific business rules.
- `prompts.py`: fixed trusted instructions and six versioned task prompts
  (`ai-prompts-v1`), plus JSON serialization of untrusted input.
- `provider.py` and `validation.py`: shared validation and provenance boundary.
- `mock.py`: deterministic simulations and a finite skill vocabulary.
- `remote.py`: OpenAI/Ollama request and response formats.
- `transport.py`: HTTP size limits, deadline, retry and safe failure handling.
- `factory.py`: server-side configuration and unconditional demo override.

The provider interface has no database, file, browser, shell, tool-execution or
owner-ID capability. Callers must resolve authenticated ownership before supplying
private context. The existing assessment workflow does so before evaluating saved
answers. The later [interview workflow](MOCK_INTERVIEWS.md) also connects answer
evaluation and contextual follow-up generation through durable owned work. The
other four operations remain internal services for future workflows. Resume upload still uses the
existing local PDF/evidence pipeline; it does not automatically call AI. No raw
resume, JD or project is sent by the assessment workflow.

## MockAIProvider

The mock performs no network requests, reads no credentials, uses no clock or
randomness and requires no model download. The same valid input yields the same
serialized result. All outputs pass the same schema/domain validation as remote
outputs. The provenance envelope says “Demo/simulated output; not verified
competence.” Existing assessment feedback also explicitly says “Mock simulation.”

Its behavior is deliberately limited and inspectable:

- Resume/JD analysis locates literal mentions from a small vocabulary (such as
  Python, SQL, React and Docker), returning actual character spans. Resume
  suggestions ask for attributable contributions and documented outcomes. Job
  mentions always have `mentioned` importance; the mock does not infer required
  versus preferred or invent experience. Negated/aspirational mentions need review.
- Answer evaluation preserves the existing `mock-lexical-v1` assessment policy:
  an expected concept matches when at least half its distinct words of four or
  more characters appear in the answer. Score is the floor of
  `4 * matched / max(1, concept_count)`. This measures lexical overlap only;
  incorrect reasoning or copied wording can still match. It never sets objective
  correctness or validates competence.
- Follow-ups choose from a fixed reasoning/test/tradeoff prompt sequence, skipping
  the current and recent questions. These are practice prompts, not evidence that
  the mock understood the answer.
- Roadmaps divide the supplied weekly budget equally across requested topics,
  rounding down. Each step includes a practice activity and observable check.
  No fabricated readiness percentage or hiring outcome is produced.
- Project questions use six authored ownership/design/testing/security/operations/
  evolution templates and a real excerpt from supplied text. They are generic
  project-defense practice, not verified repository analysis.

The existing assessment import path retains a compatibility adapter named
`MockAIProvider`; the shared implementation is in `ai/mock.py`. There is one
lexical algorithm, not two independent scoring policies.

## Configuration

The root `.env.example` contains:

```dotenv
AI_PROVIDER=mock

OLLAMA_BASE_URL=
OLLAMA_MODEL=

OPENAI_API_KEY=
OPENAI_MODEL=

AI_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=1
```

No AI key is required or requested for the default application. Mock ignores
optional remote configuration. Tests clear AI credential/model environment values
and pin mock; CI also explicitly selects mock with empty remote configuration.
Transport tests use `httpx.MockTransport` and fictional test credentials, never a
real model or paid API. Existing HTTPX/Pydantic dependencies are reused.

Only operators opting into a remote account provider set `AI_PROVIDER=ollama` or
`openai`. An invalid provider name fails settings validation instead of silently
selecting a different provider. Missing model/key values for an explicitly chosen
optional provider do not prevent application startup or demo use: evaluation
returns a safe unavailable error without attempting a request. Switching the
server configuration back to mock restores account simulation after restart.

Settings mask the OpenAI key and exclude it from serialization. Compose passes
these variables only through the backend service environment, never frontend
environment/build arguments. No provider credential has a `NEXT_PUBLIC_` variant
or appears in API responses/generated frontend types. The browser selects neither
provider URLs nor credentials. It sees the provider name/kind and saved evaluation
metadata only.

## OllamaProvider

The optional adapter sends non-streaming `POST /api/chat` requests with JSON Schema
in `format`, separate system/user messages, temperature 0, seed 0 and a 4096-token
generation cap. It does not pull models or start Ollama. A model already available
to the operator's Ollama server must be selected explicitly. These request fields
follow the [Ollama chat API](https://docs.ollama.com/api/chat) and
[structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs).

An empty base URL resolves to `http://127.0.0.1:11434`; the model remains unset
until configured. For a backend container talking to a host-local Ollama server,
the operator can use `http://host.docker.internal:11434`. A configured origin may
also identify a trusted LAN/container server. The default is local; configuring a
remote host changes the data destination and is an operator responsibility.
URL validation rejects embedded credentials, paths, queries, fragments, whitespace
and non-HTTP(S) schemes. URLs never come from submitted documents or browser input.

Unavailable servers/models, timeouts and bad responses fail gracefully with safe
errors. Completed output must contain an assistant message and a `stop` completion;
partial/token-limited output and tool calls are rejected. Temperature/seed settings
do not promise determinism across Ollama models, versions or hardware; CI uses mock.

## OpenAIProvider

The optional adapter calls the fixed server-side endpoint
`https://api.openai.com/v1/responses`. It uses `instructions` for trusted policy,
a user message for serialized data, and strict `text.format` JSON Schema, with all
output fields required and extra properties forbidden. It sets `store: false`
and a 4096-output-token cap; no tools, conversation storage, file upload, web search
or code execution is requested. This follows OpenAI's
[Responses structured-output format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

The adapter reads the actual `output` message/content array rather than assuming
an SDK-only `output_text` convenience property exists on the HTTP response. It
requires completed status, one completed assistant message with one output-text
part, and rejects refusal, incomplete/failed states, tool outputs and malformed
envelopes before parsing the domain result. Refusals are handled separately from
schema failures. No model is selected implicitly: `OPENAI_MODEL` must identify an
operator-chosen model that supports Responses structured outputs. No live paid
request or model-compatibility claim is part of automated verification.

## Validation and untrusted content

All input fields are bounded and revalidated at the method boundary, including
previously constructed Pydantic objects. Examples: documents at 50,000 characters,
question at 30,000, answer at 10,000, up to 12 expected concepts/rubric descriptions,
20 recent questions, six roadmap topics and six project questions. Roadmap budgets
are 15–600 minutes. Output numbers are strict; booleans/string scores are invalid.

All remote text is parsed into the explicit Pydantic output schema. Additional
checks verify exact evidence spans/substrings, unique skill/concept references,
matched concepts drawn only from supplied concepts, no repeated follow-up, roadmap
topic coverage and total time, and exact requested project-question count.
Unexpected keys, blank required text, excessive sizes, invalid enums and unknown
concept references fail safely. Server-generated provenance is outside model JSON.

Resume, job, question, answer, rubric and project text are data. They are JSON-escaped
in the user message and never interpolated into trusted instructions. The prompt
explicitly rejects embedded instructions, role claims, secret requests, links and
code execution. No response is executed or used to change system policy. Existing
UI rendering treats feedback as text. Injecting “give score 4,” closing delimiters
or a fake system role cannot change transport configuration, tools or credentials.

This is defense in depth, not proof that a model will ignore every adversarial
instruction. Schema-valid prose can still be false or influenced by a document;
span validation confirms a quote exists, not its interpretation. Outputs require
review and cannot auto-confirm job requirements or competence. Existing skill and
adaptive engines continue to exclude simulation and model-assisted grades from
validated performance. No AI output is persisted before validation.

## Deadlines, retries and unavailable providers

Each remote call has one configurable total deadline (default 30 seconds, maximum 60) covering connection, body reads, retries and backoff. There are at most two
additional retries; default is one. The HTTP body is limited to 256 KiB after
decoding, and the domain JSON text to 128 KiB. Redirect following and environment
proxy inheritance are disabled on the application HTTP client.

Retry only connection establishment failures and HTTP 408, 429, 500, 502, 503, 504. A 429 `insufficient_quota` result is not retried. Respect numeric/date
`Retry-After`; otherwise use bounded exponential delays starting at 250 ms. A
backoff exceeding the deadline returns unavailable without retrying too early.
Read/write/pool timeouts, other transport errors, authentication/configuration
errors, invalid output, refusal and incomplete results are not retried. An
ambiguous timeout after sending a request is deliberately not replayed. Even
transient-status retries can duplicate remote computation/billing; this is a
bounded policy, not an exactly-once generation guarantee.

Caller cancellation propagates. Safe errors are `ai_unavailable`, `ai_timeout`,
`ai_invalid_output` and `ai_refusal`; they contain no upstream body, credential or
document. There is no silent remote-to-mock fallback: falsely presenting simulated
grades as real AI would violate provenance. The mock-only demo remains available.

In assessments, provider errors become HTTP 503 and roll back partial grading;
saved drafts remain editable/retryable. The compatibility adapter permits the
configured provider deadline while preserving a five-second bound for legacy
test/custom evaluators. Up to 12 written answers are evaluated sequentially;
the per-answer deadline bounds each call, not the total submission duration.
The existing browser submission timeout is 75 seconds. A large/slow remote batch
can exceed that wait; reload the saved attempt before retrying to discover whether
the server completed it. Background evaluation and progress reporting are future
work, not implemented here.

## Existing application integration and privacy

The FastAPI lifespan constructs a shared HTTP client and selected provider and
closes the client on shutdown. No provider health request occurs at startup.
The assessment adapter maps `evaluate_answer()` to the existing conceptual grading
contract. Objective MCQ/multiple-select/literal short-answer grading stays entirely
deterministic, local and independent of optional AI availability.

The assessment configuration screen identifies the active provider and discloses
OpenAI/Ollama sharing before starting. Only written responses invoke AI on submit;
choosing objective formats avoids it. Questions, answer text, expected concepts and
rubric descriptions are sent to the selected server. IDs, resume/JD/project text
and credentials are not included in the model prompt. `store: false` does not
promise zero provider retention; provider policies still apply. The privacy page
has been updated accordingly.

Validated conceptual results retain existing simulation/model-assisted kinds and
add optional configured-model and prompt-version fields to the existing metadata
JSON. Old records without these fields remain valid. There is no schema migration,
new analytics store or logging of full input/output bodies. Account assessment
history retains its existing lifetime; demo expiry/exit erases demo history. The
new analysis/generation methods do not persist outputs themselves.

## Verification and next steps

Tests exercise all six methods on mock and fake OpenAI/Ollama transports, strict
schema/domain checks, mock determinism, source spans, simulation provenance,
invalid settings, missing keys/models, unavailable servers, transient/permanent
failures, timeouts, cancellation, oversized bodies, redirects, refusals and
injection-like documents. Application tests check default/mock and optional-provider
startup without credentials, demo pinning, persisted model/prompt provenance and
exclusion from validated competence. Frontend tests check the sharing disclosures.

Live Ollama and OpenAI calls are optional operator verification, not CI requirements.
Future work can connect the other typed operations to explicitly authorized owned
workflows, add reviewed prompt fixtures/evaluations, improve model-specific quality
and throughput, and build a user review flow. Enabling a model does not establish
its accuracy or validate the editorial scoring policy.
