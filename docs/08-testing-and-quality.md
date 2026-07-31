# Testing and Quality Strategy

**Status:** Implemented baseline
**Scope:** Local React, FastAPI, CrewAI, and Ollama application
**Last updated:** 2026-07-31

## 1. Strategy

The test suite separates deterministic application behaviour from deliberate live
model checks. Routine tests must not require Ollama, public search, or internet access.

```text
                 Small number of manual local-model checks
                    API and frontend integration tests
                 Domain service and workflow state tests
              Schema, extraction, metrics, and utility tests
```

## 2. Backend unit tests

### Documents

- supported extensions;
- empty and oversized files;
- encrypted PDFs;
- text cleaning and character ceiling;
- DOCX/PDF extraction failures.

### Schemas

- question and answer count ceilings;
- generated IDs and group normalisation;
- score and confidence ranges;
- word limits;
- selected question validation;
- iteration ceiling.

### Metrics

- matched/partial/gap/unknown weighting;
- zero-denominator behaviour;
- evidence coverage;
- question grounding;
- answer passing and unsupported-claim rates.

### Configuration

- Ollama model qualification;
- profile-to-model resolution;
- deep-profile enablement;
- reasoning setting validation;
- environment overrides;
- build tag.

## 3. Workflow tests

Use fake answer runners and agent outputs to verify:

- draft, evaluate, revise ordering;
- only weak answers are revised;
- early stopping;
- maximum cycle enforcement;
- missing answer/evaluation repair;
- invalid evidence ID filtering;
- unsafe coaching-instruction removal;
- progress stages; and
- deterministic result metrics.

## 4. API tests

Use FastAPI `TestClient` with model and service operations replaced by fakes.

Test:

- liveness, readiness, and configuration;
- upload validation;
- example sessions;
- session retrieval and deletion;
- plan and answer job submission;
- idempotency reuse and conflict;
- one-active-job enforcement;
- queue exhaustion;
- progress and terminal states;
- session expiry;
- safe error mapping;
- report and download responses;
- static route fallback and missing-build response; and
- security headers.

## 5. Frontend tests

Vitest covers:

- API path and payload construction;
- safe error decoding;
- configuration parsing;
- session and job types; and
- polling terminal-state behaviour where practical.

Manual browser checks cover:

- keyboard navigation;
- responsive layout;
- upload and example flows;
- progress presentation;
- workspace view switching;
- answer selection ceiling;
- session refresh recovery;
- download links; and
- privacy copy for optional public research.

## 6. Live Ollama contract checks

Live checks are opt-in and use only safe example files.

For each supported profile model:

1. confirm `/api/tags` lists the model;
2. run identity extraction;
3. run one structured preparation output;
4. validate returned JSON against Pydantic;
5. run one answer/evaluation pair;
6. confirm word, evidence, and iteration limits; and
7. record latency and correction count.

Preview is the required smoke target. Demo and Deep checks depend on local memory and
installed models.

## 7. Public search checks

Search tests use injected deterministic functions. A deliberate live check may verify:

- query construction;
- deduplication;
- source ceilings;
- unavailable-search fallback; and
- no search call when research is disabled.

Do not use personal candidate data in a live search check.

## 8. Static quality gates

```bash
python -m ruff check .
python -m pytest
npm run lint --prefix frontend
npm test --prefix frontend -- --run
npm run build --prefix frontend
```

Also run:

- `git diff --check`;
- XML validation for SVG architecture assets;
- dependency vulnerability review; and
- repository-wide checks for unsupported runtime paths.

## 9. Acceptance smoke test

1. Start Ollama with the Preview model installed.
2. Build the frontend.
3. Start Uvicorn on `127.0.0.1:8000`.
4. Check liveness and readiness.
5. Open the HTML application.
6. Create a session from safe examples with web research disabled.
7. Complete the plan job.
8. Coach one or more selected answers.
9. Download Markdown and JSON.
10. Refresh and verify session restoration.
11. Restart Uvicorn and verify the prior session is no longer available.

## 10. Definition of done

A change is complete when:

- deterministic tests pass;
- no live external operation is hidden inside routine tests;
- Python and TypeScript lint pass;
- the frontend production build succeeds;
- public API/type changes are reflected on both sides;
- privacy and operational documentation remain accurate; and
- local sample smoke behaviour is preserved.
