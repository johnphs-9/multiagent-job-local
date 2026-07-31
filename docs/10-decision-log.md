# Decision Log

**Status:** Active
**Last updated:** 2026-07-31

## ADR-001 — Use a browser-native React interface

**Decision:** Use React, TypeScript, and Vite for the primary interface.

**Rationale:** The workflow needs persistent navigation, structured progress, responsive
layouts, file intake, and rich report views.

**Consequences:** Frontend types and API contracts must evolve together. A production
frontend build is required for the normal single-origin runtime.

## ADR-002 — Serve the HTML application and API from FastAPI

**Decision:** Uvicorn hosts one FastAPI process that serves `frontend/dist` and
`/api/v1`.

**Rationale:** One local origin simplifies startup, routing, and browser security.

**Consequences:** Missing frontend assets produce a clear `503`. Vite remains a
development-only server.

## ADR-003 — Use Ollama as the only model runtime

**Decision:** All CrewAI model operations use a local Ollama endpoint.

**Rationale:** Candidate evidence is sensitive, and the product is explicitly
local-first.

**Consequences:** Users must install Ollama and the selected model. Readiness verifies
both endpoint and tag availability.

## ADR-004 — Use server-owned profiles

**Decision:** Preview, Demo, and Deep map to fixed workflow and token ceilings.

**Rationale:** Browser input must not expand cost, latency, or agent-loop bounds.

**Consequences:** Operators may change model tags, but profile counts remain backend
policy.

## ADR-005 — Keep application state ephemeral

**Decision:** Store sessions, jobs, plans, and reports in a thread-safe in-memory
runtime.

**Rationale:** The primary use case is one private workstation and does not require
durable infrastructure.

**Consequences:** Restart loses state. Multiple Uvicorn workers are unsupported.

## ADR-006 — Move long workflows off the event loop

**Decision:** Submit synchronous domain workflows to a bounded
`ThreadPoolExecutor`.

**Rationale:** CrewAI and local model calls are long-running and synchronous.

**Consequences:** The API returns `202`, the browser polls job state, and queue capacity
is enforced before submission.

## ADR-007 — Retain deterministic controls around agents

**Decision:** Use Pydantic validation, JSON repair, one correction request,
normalisation, evidence filtering, and deterministic metrics.

**Rationale:** Prompts alone cannot enforce structured or factual behaviour.

**Consequences:** Model output may be corrected, truncated, or rejected before it
reaches the user.

## ADR-008 — Use an evidence ledger for candidate claims

**Decision:** Drafts cite candidate evidence IDs and invalid IDs are removed.

**Rationale:** Fluent fabricated experience is a material product risk.

**Consequences:** Missing evidence remains visible and may reduce answer scores.

## ADR-009 — Keep public company research optional

**Decision:** DDGS retrieval runs only when enabled by the user.

**Rationale:** Search improves company specificity but crosses the local trust boundary.

**Consequences:** Disabled or failed search falls back to JD-only research and records a
limitation.

## ADR-010 — Bound answer improvement

**Decision:** Evaluate at most three cycles and revise only below-threshold answers.

**Rationale:** Bounded loops control latency and prevent runaway agent behaviour.

**Consequences:** Some answers may remain below target and are returned with clear
improvement guidance.

## ADR-011 — Keep the CLI

**Decision:** Retain a local CLI over the same application services.

**Rationale:** It supports automation, offline plan generation, and regression checks
without duplicating domain logic.

**Consequences:** CLI and web paths share schemas, Ollama settings, rendering, and
evidence rules.

## ADR-012 — Bind documented startup to loopback

**Decision:** The supported command binds FastAPI to `127.0.0.1`.

**Rationale:** The application has no authentication and processes sensitive evidence.

**Consequences:** LAN exposure is outside the supported security model.

## ADR-013 — Separate semantic version and build tag

**Decision:** Keep package version for compatibility and `APP_BUILD_TAG` for a specific
local build identifier. Frontend rebuilds advance the semantic patch version and use
the date-based build format `YYYYMMDD.N`, where `N` increments for each build that day.

**Rationale:** A visible build tag helps diagnose stale frontend or server processes.

**Consequences:** Health and configuration responses expose both identifiers.
