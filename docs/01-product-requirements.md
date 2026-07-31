# Product Requirements

**Status:** Implemented baseline
**Version:** 0.2
**Last updated:** 2026-07-31

## 1. Product statement

Interview Atelier is a local-first interview preparation workspace. It analyses a job
description and candidate evidence, optionally researches the company, produces
tailored questions, and coaches evidence-grounded answers with local Ollama models.

## 2. Goals

- Turn unstructured job and candidate documents into structured preparation material.
- Keep personal evidence and model inference on the user's workstation.
- Make every candidate claim traceable to supplied evidence.
- Provide clear progress for long-running multi-agent workflows.
- Enforce deterministic limits around probabilistic model output.
- Offer a polished browser experience without requiring a remote service.

## 3. Non-goals

- Predicting hiring outcomes.
- Inventing or embellishing candidate history.
- Persisting documents or reports after the local process exits.
- Supporting multiple application hosts or shared user accounts.
- Automatically submitting job applications.

## 4. Primary journey

1. The user opens the local HTML application.
2. The application reports Ollama/model readiness.
3. The user supplies a JD, candidate profile or notes, focus, profile, and research
   preference.
4. The backend extracts text and creates an ephemeral session.
5. The user starts a plan job and watches stage-based progress.
6. The application shows company research, requirement mapping, fit indicators, and
   tailored questions.
7. The user selects questions for coaching.
8. The backend drafts, evaluates, and conditionally revises answers.
9. The user reviews results and downloads Markdown or JSON.
10. The user deletes the session, lets it expire, or stops the process.

## 5. Functional requirements

### Evidence intake

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Accept one required job-description file. | Must |
| FR-002 | Accept a candidate file, candidate notes, or both. | Must |
| FR-003 | Support TXT, Markdown, PDF, and DOCX. | Must |
| FR-004 | Reject unsupported, encrypted, empty, oversized, or unextractable files. | Must |
| FR-005 | Discard original upload bytes after extraction. | Must |
| FR-006 | Let the user supply a company hint and interview focus. | Should |
| FR-007 | Let the user explicitly enable or disable public web research. | Must |

### Plan workflow

| ID | Requirement | Priority |
|---|---|---|
| FR-010 | Identify the company and role without guessing an unknown company. | Must |
| FR-011 | Retrieve public company evidence only when enabled. | Must |
| FR-012 | Preserve source IDs and research limitations. | Must |
| FR-013 | Extract responsibilities, must-have skills, preferences, and competencies. | Must |
| FR-014 | Map every requirement to matched, partial, gap, or unknown candidate evidence. | Must |
| FR-015 | Generate capped role/company and HR question sets. | Must |
| FR-016 | Calculate deterministic fit and question-quality metrics. | Must |
| FR-017 | Validate and normalise all structured outputs. | Must |

### Answer workflow

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | Let the user select generated question IDs up to the profile ceiling. | Must |
| FR-021 | Draft first-person answers using only candidate evidence. | Must |
| FR-022 | Mark missing evidence rather than inventing details. | Must |
| FR-023 | Evaluate answers using a consistent five-point rubric. | Must |
| FR-024 | Identify unsupported claims and actionable improvements. | Must |
| FR-025 | Revise only answers below the pass score. | Must |
| FR-026 | Stop early when all answers pass. | Must |
| FR-027 | Enforce a maximum of three evaluation cycles. | Must |
| FR-028 | Calculate deterministic answer-quality metrics. | Must |

### Web application

| ID | Requirement | Priority |
|---|---|---|
| FR-030 | Serve the compiled React application and API from one local origin. | Must |
| FR-031 | Create cryptographically random ephemeral session IDs. | Must |
| FR-032 | Submit long work as asynchronous jobs returning `202`. | Must |
| FR-033 | Expose job state, stage, safe message, and coarse progress. | Must |
| FR-034 | Allow at most one active job per session. | Must |
| FR-035 | Enforce bounded worker and queue capacity. | Must |
| FR-036 | Support idempotent plan and answer submissions. | Must |
| FR-037 | Restore an active session after browser refresh when it still exists. | Should |
| FR-038 | Provide Markdown and JSON downloads without durable files. | Must |
| FR-039 | Expose liveness, readiness, and public configuration endpoints. | Must |

### Local models and profiles

| ID | Requirement | Priority |
|---|---|---|
| FR-040 | Use Ollama for every model operation. | Must |
| FR-041 | Verify the configured Ollama endpoint and selected model before work. | Must |
| FR-042 | Provide Preview, Demo, and Deep profiles. | Must |
| FR-043 | Keep profile workflow limits server-authoritative. | Must |
| FR-044 | Allow operators to change local model tags through environment values. | Must |
| FR-045 | Keep hidden reasoning disabled by default for structured-output reliability. | Should |

## 6. Profile policy

| Profile | Role/company questions | HR questions | Maximum coached answers | Reviews | Output tokens |
|---|---:|---:|---:|---:|---:|
| Preview | 3 | 1 | 3 | 1 | 2,048 |
| Demo | 6 | 2 | 6 | 1 | 4,096 |
| Deep | 20 | 6 | 26 | 3 | 8,192 |

## 7. Non-functional requirements

### Privacy and security

- NFR-001: Bind the default application server to loopback.
- NFR-002: Do not introduce model credentials into browser configuration.
- NFR-003: Treat JD, CV, notes, and search snippets as untrusted data.
- NFR-004: Do not log document bodies, prompt bodies, or raw model completions.
- NFR-005: Clearly disclose that optional web search sends company queries externally.
- NFR-006: Add safe browser security headers.

### Reliability

- NFR-010: Liveness must not call Ollama or public search.
- NFR-011: Readiness must fail when Ollama or the selected model is unavailable.
- NFR-012: Ollama calls must use finite timeouts and bounded retries.
- NFR-013: Invalid model JSON gets local repair and at most one correction request.
- NFR-014: Search failure degrades to JD-only research.
- NFR-015: Process restart is an accepted loss boundary for ephemeral state.

### Performance and capacity

- NFR-020: HTTP requests must not execute CrewAI work on the event-loop thread.
- NFR-021: Default workflow concurrency is one with five queued jobs.
- NFR-022: Default session capacity is 50 with 60-minute idle expiry.
- NFR-023: File size is capped at 10 MB and extracted text at 60,000 characters.
- NFR-024: Frontend polling backs off for longer jobs.

### Maintainability

- NFR-030: Domain services remain independent of HTTP and React.
- NFR-031: Pydantic models are the authoritative domain contracts.
- NFR-032: Frontend and backend tests run without live model or search calls.
- NFR-033: Local configuration is documented in `.env.example`.
- NFR-034: The frontend production build and Python package install from the repository.

## 8. Acceptance criteria

1. `npm run build --prefix frontend` produces `frontend/dist`.
2. Uvicorn serves the application on `127.0.0.1:8000`.
3. `/api/v1/health/ready` confirms Ollama and the selected model.
4. The sample Preview plan and answer workflow completes locally.
5. Disabling web research produces no runtime internet search requests.
6. Session expiry, queue limits, idempotency, downloads, and safe errors work as
   documented.
7. `pytest`, Python lint, frontend tests, frontend lint, and the frontend build pass.
