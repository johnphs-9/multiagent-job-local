# UX Design

**Status:** Implemented baseline  
**Last updated:** 2026-07-24

## 1. Experience objective

Make a complex multi-agent workflow feel understandable and controlled. The user
should always know:

- what evidence the app is using;
- which stage is running;
- what is generated versus deterministic;
- what can be changed before spending more inference;
- when evidence is missing;
- when results will disappear.

## 2. Information architecture

Use an intake followed by a persistent three-view workspace:

```text
Evidence intake
      |
      v
Company Research <-> Job Fit <-> Interview Coaching
                                      |
                             Questions <-> Answers
```

The workspace navigation remains available after answer coaching. Switching views is a
client-side display operation: it never reruns agents, discards the generated plan, or
clears question selections. Interview Coaching has a secondary switch between the
question bank and coached answers once a report exists.

### Global header

- Product name and concise purpose.
- Service status indicator.
- “How it works” link.
- Privacy link.
- Profile selector when more than one profile is enabled.
- Restart session action.

### Global footer

- Demonstration disclaimer.
- Local model disclosure.
- Link to project/source repository if configured.
- Session-expiry notice.

## 3. Screen designs

### 3.1 Welcome and evidence

Primary objective: start safely with minimal decisions.

Sections:

1. **What this does** — one paragraph and a compact agent-flow explanation.
2. **Try the demo** — prominent action loading safe sample documents.
3. **Use your documents** — JD and candidate upload controls.
4. **Additional evidence** — notes, company hint, and interview focus.
5. **Privacy and research** — local inference statement and web research toggle.
6. **Run settings** — Fast demo shown by default; advanced limits collapsed.
7. **Build interview plan** — single primary action.

Validation appears next to the relevant field and in a focusable summary after submit.

### 3.2 Processing state

Show a stage list instead of an indeterminate spinner:

```text
[done] Validating evidence
[done] Identifying company and role
[active] Analysing role and candidate fit
[next] Designing interview questions
```

Include:

- elapsed time;
- queue position when available;
- a concise explanation that several specialist agents are working;
- cancel when cancellation is safe;
- no fake percentage for an in-progress model call.

### 3.3 Persistent interview workspace

Top summary:

- company;
- role;
- documented fit;
- evidence coverage;
- question count;
- research limitations.

Top-level tabs:

- **Company research** — facts, source badges, talking points, limitations.
- **Job fit** — fit metrics, strengths, gaps, role signals, and the requirement/evidence
  matrix.
- **Interview coaching** — selectable question cards and, after generation, the coached
  answer report.

The Interview Coaching view:

- preselects four diverse questions for the fast demo;
- shows selected count and enforced maximum;
- supports select all within the profile limit;
- warns that more selected questions take longer and use more local resources;
- provides the primary **Generate answers** action.
- retains a **Question bank / Coached answers** secondary switch after a report is
  generated.

### 3.4 Answers

Each answer card includes:

- question and category;
- latest answer;
- score and pass/needs-work text;
- evidence IDs with human-readable excerpts on demand;
- missing evidence;
- strengths and weaknesses;
- unsupported-claim warning;
- revision count.

Filters:

- all;
- needs work;
- unsupported claims;
- missing evidence;
- role/company;
- HR.

The score is not shown by colour alone. A score of 4/5 is displayed as both a number
and “Meets target”.

### 3.5 Report

Summarize:

- job fit and caveats;
- question quality;
- answer quality;
- evidence usage;
- unsupported-claim rate;
- iteration history.

Actions:

- Download Markdown.
- Download JSON.
- Return to questions and select a different subset.
- Start a new session.

Do not imply that a high score predicts an interview or job offer.

## 4. Profile experience

Users normally see:

```text
Fast demo
Designed for a short walkthrough: fewer questions and one review pass.
```

When deep mode is enabled:

```text
Deep analysis
More questions, longer answers, and up to three review passes. Takes longer and may
require substantially more local memory and processing time.
```

Raw model tags live in local configuration rather than the primary form.

## 5. Responsive design

### Desktop

- Maximum content width around 1200–1280 px.
- Two-column evidence form where useful.
- Sticky question selection summary.
- Requirement tables with complete columns.

### Tablet

- Single-column form.
- Two-column metric cards when space permits.
- Horizontal stepper may become compact.

### Mobile

- One column throughout.
- Stepper becomes a vertical or text step indicator.
- Tables become labelled cards.
- Primary actions occupy full available width.
- No horizontal scrolling for core content.

## 6. Visual language

The design should feel analytical and calm rather than game-like.

- Neutral background with one accessible primary accent.
- Green, amber, and red may support status but always include text/icons.
- Cards group evidence and outputs without excessive nested borders.
- Monospace is reserved for identifiers and diagnostics.
- Avoid emoji as the only icon or status signal.
- Motion is brief, optional, and respects `prefers-reduced-motion`.

Use CSS custom properties for colour, spacing, radius, type, and elevation. Start with
project-owned components; avoid adding a large UI framework unless implementation
speed clearly benefits.

## 7. Component inventory

```text
AppShell
  Header
  WorkspaceNavigation
  ServiceStatus
  SessionExpiryNotice

EvidencePage
  ExampleDataAction
  FileDropzone
  CandidateNotes
  PrivacyDisclosure
  ProfileCard
  AdvancedOptions

JobProgress
  StageList
  QueueNotice
  ElapsedTime
  RetryPanel

CompanyResearchView
  IdentitySummary
  ResearchFact
  SourceLink

JobFitView
  MetricCard
  FitInterpretation
  RequirementList/Table

InterviewCoachingView
  CoachingSubnavigation
  QuestionCard
  SelectionBar

AnswersPage
  AnswerFilters
  AnswerCard
  ScoreBadge
  EvidenceDisclosure
  EvaluationPanel

ReportPage
  MetricSummary
  IterationTimeline
  DownloadActions
```

## 8. Content guidelines

- Say “documented alignment,” not “chance of getting the job.”
- Say “The supplied profile does not demonstrate…” rather than “You cannot…”.
- Say “Local model unavailable; check Ollama and try again” rather than exposing stack traces.
- Name the active stage, not a generic “Thinking…”.
- Explain that search snippets are public evidence and may be incomplete.
- Tell users when the model was unable to return valid structured data.
- Keep technical model details available but secondary.

## 9. Accessibility requirements

- Every input has a persistent label.
- File dropzones work through keyboard file selection.
- Validation summary receives focus after failed submission.
- Job status updates use a polite ARIA live region.
- Error announcements use an assertive live region only when necessary.
- Tabs follow WAI-ARIA keyboard behaviour or use ordinary headings/links.
- Focus returns to the page heading after route changes.
- Download actions have descriptive names and formats.
- Source links indicate that they open an external site.
- Minimum touch target is 44 by 44 CSS pixels where practical.

## 10. Empty and failure states

| State | Required response |
|---|---|
| No research sources | Continue with JD-only result and explain limitation |
| Unknown company | Ask for optional company hint; do not block offline planning |
| No candidate evidence | Block answer generation and explain why |
| No generated questions | Offer plan retry and preserve inputs |
| Ollama busy | Show retry guidance and retain completed state |
| Session expired | Explain expiry and offer examples/new upload |
| Ollama unavailable | Explain how to start Ollama and check the selected model |
| Deep profile disabled | Keep Preview and Demo available |

## 11. UX acceptance checks

- A user can complete the example flow without reading documentation.
- A keyboard-only user can complete every step and download a report.
- A user never needs to choose a raw model name.
- The active agent stage is visible during every long operation.
- The interface explains that inference is local and public search is optional.
- The interface remains usable at 360 CSS pixels wide.
- Refresh behaviour is predictable: restore from `sessionStorage` when valid or explain
  that the session has expired.
- Company Research, Job Fit, and Interview Coaching remain switchable after a report is
  generated without another model call.
