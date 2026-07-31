# LLM and Multi-Agent Design

**Status:** Implemented baseline
**Model runtime:** Local Ollama only
**Last updated:** 2026-07-31

## 1. Design goals

- Use specialist agents where separate roles improve clarity and evaluation.
- Keep all inference on the workstation.
- Make structured Pydantic contracts authoritative.
- Prevent candidate-fact fabrication.
- Bound every retry, question count, answer count, and review cycle.
- Degrade gracefully when public company research is unavailable.

## 2. Local model profiles

| Profile | Ollama model | Role questions | HR questions | Coached answers | Reviews | Output tokens |
|---|---|---:|---:|---:|---:|---:|
| Preview | `llama3.2:latest` | 3 | 1 | 3 | 1 | 2,048 |
| Demo | `gemma4:latest` | 6 | 2 | 6 | 1 | 4,096 |
| Deep | `gemma4:26b` | 20 | 6 | 26 | 3 | 8,192 |

Operators can change model tags and every profile property through `.env` without
changing domain code. Profile keys use the `PROFILE_PREVIEW_*`, `PROFILE_DEMO_*`, and
`PROFILE_DEEP_*` prefixes. The backend loads and validates these values at startup;
browser values never expand them.

## 3. Model construction

`create_llm(settings)` creates the CrewAI model client with:

```text
model              = ollama/<selected tag>
base_url           = http://localhost:11434
temperature        = 0.2 by default
timeout            = 600 seconds by default
max_retries        = 2
max_tokens         = profile ceiling or operator override
reasoning_effort   = none by default
```

Keeping hidden reasoning off is important for models that might otherwise consume the
completion budget before emitting the required JSON.

## 4. Preparation Crew

### Identity analyst

Extracts the company and role from the JD. A user company hint overrides inference. An
unclear employer becomes `Unknown company`; the agent does not guess from wording or a
recruiter name.

### Company research analyst

Synthesises only supplied search evidence and relevant JD statements. Facts cite source
IDs, uncertainty remains explicit, and absent evidence becomes a research limitation.

### Job-description analyst

Extracts responsibilities, skills, competencies, likely challenges, and keywords. It
maps each requirement to candidate evidence using:

- `matched`;
- `partial`;
- `gap`; or
- `unknown`.

Direct evidence is required for strengths. Course or project evidence must not be
upgraded into unsupported professional ownership.

### Interview architect

Creates a non-duplicative, capped question bank with category, rationale, strong-answer
signals, and source references. It receives the research and JD analysis as task
context and never drafts answers.

### Execution order

```text
Identity kickoff
 -> optional deterministic search
 -> research task
 -> JD analysis task
 -> question-design task
 -> validation and normalisation
 -> deterministic metrics
```

The final three tasks use a sequential CrewAI Crew.

## 5. Answer evaluator–optimizer Flow

### Evidence ledger

Candidate profile lines are normalised into stable evidence IDs (`E1`, `E2`, ...).
Drafts may cite only IDs from this ledger. Invalid IDs are removed and reported as
missing evidence.

### Draft

The answer agent:

- writes one first-person answer per selected question;
- supports past-tense and habitual claims with evidence IDs;
- uses prospective wording for unverified approaches;
- records missing evidence explicitly;
- avoids placeholders; and
- respects the profile word limit.

### Evaluate

The evaluator scores from 1 to 5, lists strengths and weaknesses, identifies unsupported
claims, and returns concrete improvement instructions. Unsupported experience caps the
answer at a low score.

### Revise

Only answers below the pass score are revised. Revisions remove unsupported claims,
preserve valid evidence, and remain honest about gaps.

### Stop conditions

The Flow stops when:

- every pending answer reaches the pass score; or
- the profile's maximum evaluation count is reached.

The schema hard ceiling is three cycles.

## 6. Structured-output controls

Each model operation appends a compact value-shaped JSON example derived from the
Pydantic schema. Result handling proceeds as follows:

1. use a native Pydantic result when supplied;
2. otherwise repair raw JSON locally;
3. validate against the expected model;
4. if invalid, ask the same agent for one bounded correction;
5. fail with a safe contract error if correction remains invalid.

Post-model normalisation enforces counts, IDs, source references, evidence references,
word limits, and deterministic metrics.

## 7. Prompt-injection controls

The JD, candidate profile, and search snippets are untrusted reference data. Agent
instructions explicitly delimit them and prohibit following embedded directives.
Search snippets are evidence leads, not executable instructions or unquestioned facts.

## 8. Observability

Stable progress stages include:

- `identifying_role`;
- `collecting_research`;
- `synthesizing_research`;
- `analysing_requirements`;
- `designing_questions`;
- `drafting_answers`;
- `evaluating_answers`;
- `revising_answers`; and
- `report_ready`.

Logs may include job IDs, stage, elapsed time, model tag, retry count, and safe error
codes. They must not include document bodies, prompts, or raw completions.

## 9. Testing approach

Most tests replace agent runners, model calls, and search functions with deterministic
fakes. Deliberate live-model tests use safe example data and are run separately because
they are slower and depend on installed local models.
