# Project Brief

**Status:** Implemented baseline
**Product:** Interview Atelier
**Last updated:** 2026-07-31

## Purpose

Build a private, local-first interview preparation application that converts a job
description and candidate evidence into researched preparation material, job-fit
analysis, tailored questions, and evidence-grounded answer coaching.

## Product outcome

A user opens the React application in a browser, uploads local documents, selects an
Ollama workflow profile, and receives:

- company research with optional public sources;
- structured job-description and candidate-fit analysis;
- role, company, technical, HR, and behavioural questions;
- draft answers grounded in candidate evidence;
- evaluator feedback and bounded revisions; and
- Markdown and JSON report downloads.

## Architecture direction

The application runs on one workstation:

- React/TypeScript compiled to HTML, JavaScript, and CSS;
- FastAPI served by Uvicorn on loopback;
- an in-memory session store and bounded background job executor;
- shared Python domain services and Pydantic contracts;
- CrewAI agents and a typed evaluator–optimizer Flow;
- Ollama for all model inference; and
- DDGS only for optional company web research.

No application database is required. Uploaded bytes are discarded after extraction,
and generated state expires from process memory.

## Product principles

1. **Local by default.** Candidate evidence and model prompts remain on the workstation.
2. **Evidence before fluency.** The system must not invent candidate experience.
3. **Bounded agent behaviour.** Question counts, answer counts, retries, and revision
   cycles have server-owned ceilings.
4. **Transparent uncertainty.** Missing evidence and research limits remain visible.
5. **Responsive web interaction.** Long model work runs outside the HTTP event loop and
   exposes stage-based progress.
6. **Simple operations.** One Python process, one local model service, and no durable
   infrastructure.

## Primary user

An individual preparing privately for a specific interview on a personal workstation.
The user is comfortable installing Python, Node.js, and Ollama, but should not need to
understand CrewAI internals.

## In scope

- TXT, Markdown, PDF, and DOCX evidence extraction;
- optional public company research;
- three local workflow profiles;
- ephemeral sessions and asynchronous jobs;
- plan and answer workflows;
- fit, question-quality, and answer-quality metrics;
- Markdown and JSON exports;
- health, readiness, and public configuration endpoints;
- CLI access for local automation; and
- deterministic tests that mock model and search operations.

## Out of scope

- user accounts or team workspaces;
- durable persistence;
- multi-host scaling;
- autonomous job applications;
- claims about hiring probability;
- real-time collaboration; and
- long-term storage of personal documents.

## Success criteria

The baseline is successful when:

1. a first-time local user can install dependencies and start the application;
2. the browser loads the compiled React interface from FastAPI;
3. the Preview profile completes the sample plan and coaching workflow using Ollama;
4. every generated candidate claim is evidence-constrained;
5. web research can be disabled for a fully local runtime path;
6. progress, errors, and expiry behaviour are understandable; and
7. backend tests, frontend tests, lint, and the production frontend build pass.
