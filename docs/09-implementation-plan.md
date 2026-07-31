# Implementation Plan

**Status:** Local baseline complete; maintenance plan active
**Last updated:** 2026-07-31

## 1. Delivery objective

Maintain a single local product path: compiled React/HTML served by FastAPI, shared
Python domain services, CrewAI orchestration, and Ollama inference.

## 2. Completed baseline

### Foundation

- Python package and CLI;
- document extraction;
- Pydantic schemas and hard ceilings;
- deterministic metrics and rendering;
- safe example inputs.

### Agent workflows

- identity analyst;
- optional public company research;
- JD and candidate-fit analyst;
- interview architect;
- evidence-grounded answer coach;
- strict evaluator;
- bounded revision Flow;
- structured-output repair and correction.

### Web application

- React/TypeScript interface;
- FastAPI API and static delivery;
- ephemeral session and job lifecycle;
- bounded background executor;
- idempotent plan and answer jobs;
- stage-based polling;
- Markdown and JSON downloads;
- liveness, readiness, and configuration.

### Local operations

- Ollama Preview, Demo, and Deep profiles;
- `.env.example`;
- local build and run instructions;
- privacy boundaries;
- deterministic backend and frontend tests;
- presentation-ready architecture documentation.

## 3. Maintenance workstreams

### A. Contract stability

- keep Pydantic domain models authoritative;
- update TypeScript types with API changes;
- preserve camelCase response mapping;
- test schema normalisation and output ceilings;
- version incompatible API changes deliberately.

### B. Local-model reliability

- smoke-test supported Ollama tags before changing defaults;
- measure structured-output correction rates;
- keep finite timeouts and retries;
- preserve reasoning defaults that protect JSON output;
- document memory expectations for larger models.

### C. Evidence safety

- expand prompt-injection regression cases;
- strengthen unsupported-claim detection;
- preserve evidence ledger validation;
- review score explanations and limitations;
- keep search evidence traceable to source IDs.

### D. User experience

- keep the intake path short;
- maintain keyboard and mobile usability;
- present useful stage messages without invented percentages;
- explain expiry and Ollama recovery clearly;
- preserve research, fit, and coaching navigation.

### E. Operations

- keep single-origin local startup reproducible;
- validate missing-frontend and missing-model errors;
- review dependency updates;
- measure queue and memory behaviour;
- keep logs free of sensitive content.

## 4. Change sequence

For a normal feature:

1. update the product requirement or decision when behaviour changes;
2. change domain contracts and tests;
3. change application services;
4. change API models/routes;
5. change TypeScript types and UI;
6. update local operations and privacy documentation;
7. run deterministic quality gates;
8. run the safe Preview smoke workflow when model behaviour is affected.

## 5. Quality gates

```bash
python -m ruff check .
python -m pytest
npm run lint --prefix frontend
npm test --prefix frontend -- --run
npm run build --prefix frontend
```

Model-dependent changes also require an explicit local Ollama contract check.

## 6. Backlog

### Near term

- increase frontend component test coverage;
- add an explicit opt-in live-model smoke command;
- improve cancellation semantics for queued work;
- add clearer local model memory diagnostics;
- expose safe queue-capacity diagnostics;
- strengthen accessible progress announcements.

### Later, within the local architecture

- optional encrypted local persistence with an explicit retention policy;
- resumable local reports;
- richer locally generated export formats;
- model performance comparison using safe examples;
- configurable local search region;
- user-controlled log verbosity with privacy-safe defaults.

Any feature that introduces shared hosting or multi-user access requires a new product
and security decision and is not part of this plan.

## 7. Definition of done

- one documented browser application path;
- Ollama is the only model runtime;
- no unsupported deployment artifacts or configuration remain;
- web research can be disabled;
- local tests and build pass;
- local architecture documentation matches the implementation; and
- sample inputs complete the Preview workflow.
