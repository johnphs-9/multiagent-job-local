# Local Deployment and Operations

**Status:** Implemented baseline
**Target:** One local workstation
**Last updated:** 2026-07-31

## 1. Supported runtime modes

| Mode | Frontend | Backend | Model |
|---|---|---|---|
| Normal local use | Compiled React assets served by FastAPI | Uvicorn on port 8000 | Ollama on port 11434 |
| Frontend development | Vite on port 5173 | Uvicorn reload on port 8000 | Ollama on port 11434 |
| CLI | None | Direct Python use cases | Ollama on port 11434 |

The compiled single-origin mode is the recommended way to use and demonstrate the
application.

## 2. Prerequisites

- Python 3.10–3.13;
- Node.js 20.19+ or 22.12+;
- npm;
- Ollama;
- a current browser; and
- enough memory and disk for the selected model.

## 3. One-time installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
npm install --prefix frontend
cp .env.example .env
```

## 4. Model preparation

Start Ollama only when it is not already running:

```bash
ollama serve
```

Pull the required models:

```bash
ollama pull llama3.2:latest
ollama pull gemma4:latest
ollama pull gemma4:26b
```

Confirm availability:

```bash
ollama list
```

The Preview profile is the smallest readiness and smoke-test target.

## 5. HTML application build and run

Use the managed launcher for normal local operation:

```bash
./scripts/start-local.sh
```

It prints each prerequisite and service check as `[x]` when satisfied or `[ ]` when
action is required. It verifies that every model assigned to an enabled runtime
profile is already downloaded and prints an exact `ollama pull` command for each
missing model; model downloads are never automatic. It can start a missing local
Ollama process, builds the frontend, and runs Uvicorn in the foreground so its server
and access logs remain visible. `Ctrl+C` stops Uvicorn and any Ollama process started
by the launcher, without stopping a pre-existing Ollama process.

Run diagnostics without starting or building:

```bash
./scripts/start-local.sh --check-only
```

The equivalent targets are `make start` and `make doctor`.

### Manual commands

Build the frontend:

```bash
npm run build --prefix frontend
```

Start the application:

```bash
source .venv/bin/activate
python -m uvicorn interview_local.api.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>.

FastAPI resolves `frontend/dist`, mounts its `assets` directory, serves files directly,
and returns `index.html` for non-API routes. If the build is absent, the browser route
returns `503` with the build command.

## 6. Frontend development

Run these in separate terminals:

```bash
source .venv/bin/activate
python -m uvicorn interview_local.api.app:app --reload --port 8000
```

```bash
npm run dev --prefix frontend
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to
`http://127.0.0.1:8000`.

## 7. Configuration

```dotenv
DEFAULT_MODEL_PROFILE=demo

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_PREVIEW_MODEL=llama3.2:latest
OLLAMA_DEMO_MODEL=gemma4:latest
OLLAMA_DEEP_MODEL=gemma4:26b
OLLAMA_REASONING_EFFORT=none

PROFILE_DEMO_ROLE_QUESTION_COUNT=6
PROFILE_DEMO_HR_QUESTION_COUNT=2
PROFILE_DEMO_ANSWER_SELECTION_DEFAULT=4
PROFILE_DEMO_ANSWER_SELECTION_MAXIMUM=6
PROFILE_DEMO_MAX_ITERATIONS=1
PROFILE_DEMO_PASS_SCORE=4
PROFILE_DEMO_ANSWER_WORD_LIMIT=120
PROFILE_DEMO_MAX_TOKENS=4096
PROFILE_DEMO_SEARCH_REGION=sg-en

ENABLE_DEEP_PROFILE=true
LLM_TIMEOUT_SECONDS=600

SESSION_IDLE_MINUTES=60
MAX_SESSIONS=50
JOB_WORKER_CONCURRENCY=1
JOB_QUEUE_SIZE=5
REQUEST_LIMIT_PER_HOUR=20

APP_BUILD_TAG=20260731.3
CREWAI_DISABLE_TELEMETRY=true
OTEL_SDK_DISABLED=true
```

Every profile property can be overridden in `.env`. The full set is documented in
`.env.example` under `PROFILE_PREVIEW_*`, `PROFILE_DEMO_*`, and `PROFILE_DEEP_*`.
`LLM_MAX_TOKENS` remains an optional global token-ceiling override.

Use `.env` for workstation-specific values and never commit it.

## 8. Health and diagnostics

### Liveness

```bash
curl http://127.0.0.1:8000/api/v1/health/live
```

Confirms that the process and event loop respond. It does not call Ollama or search.

### Readiness

```bash
curl http://127.0.0.1:8000/api/v1/health/ready
```

Calls Ollama's tag endpoint and confirms that the default profile model is installed.

### Public configuration

```bash
curl http://127.0.0.1:8000/api/v1/config
```

Shows enabled profiles, model tags, workflow limits, upload rules, version, build tag,
and session expiry.

## 9. Capacity

The defaults are appropriate for one workstation:

- one workflow worker;
- five queued jobs;
- one active job per session;
- 50 sessions;
- 60-minute idle expiry;
- 20 rate-limited mutations per client per hour;
- 10 MB per file; and
- 60,000 extracted characters per document.

Increase concurrency only after measuring local model memory and latency. More worker
threads can create simultaneous model requests and exhaust memory.

## 10. Logging

Logs may contain:

- timestamp and severity;
- request, session, and job correlation IDs;
- job type, stage, and state;
- selected local model tag;
- elapsed time and retry count; and
- safe error code.

Do not log upload text, candidate notes, prompts, raw completions, or environment
values.

## 11. Backup and recovery

Application state is intentionally ephemeral. There is no session backup or migration.

- Browser refresh can reconnect while the session remains in memory.
- Session deletion or expiry removes its jobs and results.
- Restarting Uvicorn clears all active state.
- Source and configuration recovery uses version control and a local `.env` backup.
- Reports that must be retained should be downloaded by the user.

## 12. Operational checklist

Before a demonstration:

1. confirm Ollama is running;
2. confirm the Preview model is installed;
3. build the frontend;
4. start Uvicorn on loopback;
5. verify liveness and readiness;
6. run the example Preview plan;
7. confirm Markdown and JSON downloads;
8. disable public web research when a fully local runtime is required; and
9. keep a safe screenshot or sample report as a presentation fallback.
