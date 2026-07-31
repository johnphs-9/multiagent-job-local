# Project assets

This directory holds public, non-sensitive assets used by the repository README and
other project documentation.

## Architecture

Presentation-ready technical diagrams belong in `architecture/`. Prefer SVG for
scalable text and shapes, use a descriptive filename, and include an accessible title
and description inside the SVG.

The current local deployment diagram is:

```markdown
![Detailed local HTML deployment architecture](assets/architecture/local-html-deployment-architecture.svg)
```

## Screenshots

Place major interface screenshots in `screenshots/`. Suggested filenames are:

- `01-start-screen.png`
- `02-company-research.png`
- `03-job-fit.png`
- `04-interview-questions.png`
- `05-answer-coaching.png`

Use PNG or WebP, crop out browser chrome where practical, and remove names, contact
details, CV content, API tokens, and other personal information before committing.

Reference a screenshot from the root README with a relative path such as:

```markdown
![Company Research screen](assets/screenshots/02-company-research.png)
```

## Downloads

Place safe example files intended for readers to download in `downloads/`, such as a
sample generated interview report. Do not put runtime output, real job applications,
private CVs, or large model files here.

Use descriptive, stable filenames and link them from the root README with a relative
path such as:

```markdown
[Download the sample report](assets/downloads/sample-interview-report.md)
```
