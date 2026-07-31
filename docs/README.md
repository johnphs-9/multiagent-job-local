# Planning and Design Documentation

This directory records the implemented design for the local React, FastAPI, CrewAI,
and Ollama application.

## Recommended reading order

1. [Project brief](00-project-brief.md) — purpose, user, principles, scope, and success
   criteria.
2. [Product requirements](01-product-requirements.md) — journeys, functional
   requirements, local profiles, non-functional requirements, and acceptance criteria.
3. [System architecture](02-system-architecture.md) — runtime components, flows, trust
   boundaries, failure behaviour, and scalability boundary.
4. [LLM and multi-agent design](03-llm-and-agent-design.md) — Ollama profiles, agents,
   evaluator–optimizer Flow, structured output, and evidence controls.
5. [UX design](04-ux-design.md) — information architecture, screens, responsive
   behaviour, states, accessibility, and content.
6. [API and data design](05-api-and-data-design.md) — FastAPI routes, job lifecycle,
   validation, and contracts.
7. [Local deployment and operations](06-deployment-and-operations.md) — installation,
   build, startup, configuration, health, capacity, logging, and recovery.
8. [Security and privacy](07-security-and-privacy.md) — data lifecycle, threats,
   controls, local binding, logging, and disclosures.
9. [Testing and quality](08-testing-and-quality.md) — deterministic automation, local
   model checks, static gates, and smoke tests.
10. [Implementation plan](09-implementation-plan.md) — completed baseline, maintenance
    workstreams, backlog, sequence, and definition of done.
11. [Decision log](10-decision-log.md) — active architectural decisions.
12. [Local HTML deployment architecture](12-local-html-deployment-architecture.md) —
    presentation-ready detailed topology and operational walkthrough.

## Document status

The implemented baseline is:

- React/HTML frontend;
- FastAPI/Uvicorn application boundary;
- ephemeral sessions and bounded jobs;
- existing Python/CrewAI domain logic;
- Preview, Demo, and Deep Ollama profiles;
- optional public company search;
- CLI access; and
- local-only deployment and operations.

Material changes to persistence, network exposure, authentication, agent topology,
profile ceilings, or privacy boundaries should update the product requirements,
architecture, security document, tests, and decision log together.
