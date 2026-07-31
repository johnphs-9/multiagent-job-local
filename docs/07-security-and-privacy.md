# Security and Privacy

**Status:** Implemented baseline
**Scope:** Local workstation runtime
**Last updated:** 2026-07-31

## 1. Data classification

| Data | Classification | Lifetime |
|---|---|---|
| JD and candidate upload bytes | Sensitive | Current upload request only |
| Extracted JD/CV text and notes | Sensitive | In-memory session |
| Plans, answers, evaluations, reports | Sensitive | In-memory session |
| Session and job IDs | Internal | Session lifetime |
| Local model tags and workflow limits | Non-sensitive | Process lifetime |
| Public company search results | Public/untrusted | Session lifetime |

## 2. Privacy model

Model inference uses Ollama on loopback. Extracted evidence is sent from the Python
process to the local Ollama service and is not intentionally transmitted to a remote
model service.

Optional company research is the runtime egress boundary. When enabled, the inferred
company name and search queries are sent to public search. The UI must disclose this
before submission.

## 3. Data lifecycle

```text
Upload bytes
 -> size/type validation
 -> text extraction
 -> original bytes discarded
 -> extracted text stored in RuntimeState
 -> plan/report added to the same session
 -> explicit deletion, idle expiry, or process exit
```

Downloads are rendered from memory and are not written by the API.

## 4. Threats and controls

### Malicious documents

Controls:

- extension allow-list;
- 10 MB file ceiling;
- encrypted PDF rejection;
- 60,000-character extracted-text ceiling;
- text cleaning; and
- no macro or embedded executable processing.

### Prompt injection

JD, CV, notes, and search snippets are treated as untrusted data. Prompts delimit each
source and tell agents not to follow embedded instructions. Agents cannot delegate or
execute tools supplied by document content.

### Candidate-fact fabrication

Controls:

- evidence ledger IDs;
- evidence-required candidate claims;
- invalid evidence-ID filtering;
- evaluator detection of unsupported claims;
- safe revision instructions; and
- explicit missing-evidence fields.

### Excessive resource use

Controls:

- server-owned profile ceilings;
- bounded queue and worker concurrency;
- one active job per session;
- session-count and idle limits;
- request rate limiting;
- finite model timeouts and retries; and
- bounded correction and evaluation cycles.

### Browser attacks

FastAPI adds:

- `X-Content-Type-Options: nosniff`;
- strict referrer policy;
- restricted permissions policy; and
- same-origin framing.

The frontend does not render arbitrary HTML from model output.

### Session guessing

Session and job IDs use cryptographically random URL-safe values. They are capability
tokens for the local API and must not be logged in full when logs may be shared.

## 5. Binding and network exposure

The documented server command binds to `127.0.0.1`. Users should not bind to
`0.0.0.0` unless they deliberately accept LAN exposure and add authentication,
transport security, and a revised threat model.

Ollama should also remain local. A remotely reachable Ollama endpoint is outside the
supported privacy model.

## 6. Logging policy

Allowed:

- truncated correlation IDs;
- stage, state, timings, model tag, and retry count;
- validation and safe error codes.

Prohibited:

- upload or extracted text;
- candidate notes;
- prompt bodies;
- raw model completions;
- environment files; and
- complete session capability IDs in shared logs.

## 7. User disclosures

The UI must explain:

- model inference runs on the workstation;
- public web research is optional;
- enabling research sends company queries externally;
- session state is temporary and lost on restart;
- generated content requires human review; and
- fit metrics are preparation indicators, not hiring predictions.

## 8. Security verification

- test document type, size, encryption, and extraction failures;
- test prompt-injection resistance with inert document text;
- test profile and selection ceilings at the API boundary;
- verify secrets or document bodies are absent from API configuration and errors;
- scan Python and npm dependencies;
- verify loopback binding in local instructions; and
- review logs from failed model and search operations.
