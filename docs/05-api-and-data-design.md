# API and Data Design

**Status:** Implemented baseline
**Base path:** `/api/v1`
**Last updated:** 2026-07-31

## 1. Design rules

- The API and compiled React application use one local origin.
- Pydantic domain models remain the canonical generated-content contracts.
- Long work returns `202 Accepted`; clients poll a job resource.
- Server-side profile limits override browser values.
- Plan and answer submissions support idempotency.
- Raw document text is never returned in session metadata.
- No model credential is accepted from or returned to the browser.

## 2. Resource model

```text
SessionRecord
  - opaque session ID
  - selected profile
  - extracted JD and candidate text
  - filenames and workflow preferences
  - zero or one InterviewPackage
  - zero or one InterviewReport
  - zero or one active job ID

JobRecord
  - opaque job ID
  - session ID
  - type: plan | answers
  - state, stage, message, and coarse progress
  - timestamps and safe error fields
```

Both records exist only in `RuntimeState` memory.

## 3. Health and configuration

| Method | Path | Purpose |
|---|---|---|
| GET | `/health/live` | Process and event-loop liveness |
| GET | `/health/ready` | Ollama and selected-model readiness |
| GET | `/config` | Client-safe profiles, limits, types, version, and expiry |

Example configuration:

```json
{
  "appVersion": "0.2.3",
  "buildTag": "20260731.3",
  "profiles": [
    {
      "id": "demo",
      "label": "Fast demo",
      "description": "The recommended demonstration with concise answers and one review pass.",
      "model": "gemma4:latest",
      "roleQuestionCount": 6,
      "hrQuestionCount": 2,
      "defaultAnswerCount": 4,
      "maxAnswerCount": 6,
      "maxIterations": 1
    }
  ],
  "defaultProfile": "demo",
  "maxUploadBytes": 10485760,
  "supportedExtensions": [".docx", ".md", ".pdf", ".txt"],
  "sessionIdleMinutes": 60
}
```

Environment values and internal filesystem paths are never returned.

## 4. Session endpoints

### Create from user evidence

`POST /sessions` with `multipart/form-data`:

- `job_description`: required file;
- `candidate_profile`: optional file when notes are present;
- `candidate_notes`: optional text;
- `company_hint`: optional text;
- `interview_focus`: optional text;
- `web_research`: boolean; and
- `profile`: `preview`, `demo`, or `deep`.

At least one candidate file or candidate-notes value is required. The API reads and
extracts upload bytes during this request and does not retain the original files.

### Create from safe examples

`POST /sessions/examples` with JSON:

```json
{
  "profile": "preview",
  "company_hint": "",
  "interview_focus": "balanced company, role, technical, and behavioural coverage",
  "web_research": false
}
```

### Read and delete

| Method | Path | Purpose |
|---|---|---|
| GET | `/sessions/{session_id}` | Read session state and result availability |
| DELETE | `/sessions/{session_id}` | Remove the session, jobs, and results |

Example session:

```json
{
  "sessionId": "opaque-random-id",
  "profile": "preview",
  "state": "plan_ready",
  "createdAt": "2026-07-31T00:00:00Z",
  "expiresInSeconds": 3500,
  "activeJobId": null,
  "hasPlan": true,
  "hasReport": false,
  "jobDescriptionFilename": "job_description.txt",
  "candidateFilename": "candidate_profile.txt"
}
```

## 5. Job endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/sessions/{session_id}/plan-jobs` | Submit plan generation |
| POST | `/sessions/{session_id}/answer-jobs` | Submit selected-answer coaching |
| GET | `/jobs/{job_id}` | Poll job state and progress |

Mutation requests use an `Idempotency-Key` header. The browser generates a UUID for
each new logical submission.

Answer submission body:

```json
{
  "selected_question_ids": ["RC01", "HR01"]
}
```

The API rejects duplicates, unknown IDs, and selections above the session profile's
maximum.

Example job:

```json
{
  "jobId": "opaque-job-id",
  "sessionId": "opaque-session-id",
  "type": "plan",
  "state": "running",
  "stage": "analysing_requirements",
  "message": "Analysing role requirements and candidate fit",
  "completedSteps": 3,
  "totalSteps": 5,
  "createdAt": "2026-07-31T00:00:00Z",
  "startedAt": "2026-07-31T00:00:01Z",
  "finishedAt": null,
  "errorCode": null,
  "retryable": false,
  "resultUrl": null
}
```

Job states are `queued`, `running`, `succeeded`, `failed`, and `cancelled`.

## 6. Result and download endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/sessions/{session_id}/plan` | Return `InterviewPackage` |
| GET | `/sessions/{session_id}/report` | Return `InterviewReport` |
| GET | `/sessions/{session_id}/downloads/report.md` | Render Markdown download |
| GET | `/sessions/{session_id}/downloads/report.json` | Render JSON download |

A result request before completion returns `409`. Downloads are rendered from the
in-memory report and are not written by the API.

## 7. Idempotency and concurrency

The runtime stores:

```text
(session_id, job_type, idempotency_key) -> (payload_digest, job_id)
```

Repeating the same key and payload returns the original job. Reusing a key with a
different payload returns `409`.

The runtime also enforces:

- one active job per session;
- one running workflow by default;
- five queued workflows by default;
- non-blocking rejection when capacity is full; and
- cleanup of job and idempotency records with the session.

## 8. Error model

Handled application errors use:

```json
{
  "error": {
    "code": "QUEUE_FULL",
    "message": "The workflow queue is full. Try again shortly.",
    "retryable": true
  }
}
```

Stable codes include:

```text
INVALID_DOCUMENT
QUEUE_FULL
ACTIVE_JOB_EXISTS
IDEMPOTENCY_CONFLICT
MODEL_UNAVAILABLE
MODEL_RATE_LIMITED
MODEL_TIMEOUT
STRUCTURED_OUTPUT_INVALID
WORKFLOW_VALIDATION_ERROR
WORKFLOW_FAILED
```

FastAPI validation and missing-resource responses use safe `detail` messages.

| Status | Use |
|---:|---|
| 200 | Successful read |
| 201 | Session created |
| 202 | Job accepted |
| 204 | Session deleted |
| 404 | Unknown session, job, or route |
| 409 | Invalid state, active job, or idempotency conflict |
| 410 | Expired session |
| 422 | Field, profile, ID, or document validation |
| 429 | Request rate limit |
| 503 | Queue full, Ollama unavailable, or frontend absent |

## 9. Naming and compatibility

- Python domain models use `snake_case`.
- API result objects are recursively converted to `camelCase`.
- Timestamps use UTC ISO 8601 strings.
- Identifiers are opaque and must not be parsed.
- Additive fields are backward compatible.
- Breaking route or meaning changes require a new API version.

The CLI calls Python services directly and does not depend on HTTP routes.
