---
version: "alpha"
name: "Evidence-led Professional Light"
description: "A professional light-mode system with slight warmth, lively ocean and coral primaries, and evidence-led visual structure."
colors:
  ink: "#1B211F"
  muted-ink: "#5F6662"
  canvas: "#F6F5F1"
  paper: "#FFFDF9"
  soft-neutral: "#ECEDEA"
  rule: "#D5D8D3"
  primary: "#EDB86C"
  primary-hover: "#E6AD6A"
  primary-active: "#C68148"
  primary-warm: "#A45F3F"
  primary-warm-hover: "#914F34"
  primary-warm-active: "#7D412C"
  action-link: "#93583A"
  action-link-hover: "#6E3D2C"
  action-link-active: "#52312A"
  activity-backdrop: "#011136"
  activity-panel: "#02225E"
  animation-yellow: "#F4DB95"
  animation-amber: "#E6AD6A"
  deep-patrol: "#1F5552"
  copper: "#8A503B"
  marine: "#294B60"
  success: "#38654F"
  warning: "#7A5B24"
  danger: "#8B453B"
  bar-abyss: "#02225E"
  bar-ocean: "#036D92"
  bar-copper: "#93583A"
  bar-reef: "#49452E"
  bar-marine: "#0E3C75"
  separator-blue: "#70A0C6"
  separator-bronze: "#8A714D"
  highlight-lagoon: "#0387AD"
  highlight-amber: "#C68148"
  highlight-coral: "#B8764B"
typography:
  display:
    fontFamily: "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "4.5rem"
    fontWeight: 600
    lineHeight: 0.96
    letterSpacing: "-0.045em"
  heading:
    fontFamily: "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  body:
    fontFamily: "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.08em"
  editorial:
    fontFamily: "Newsreader, Iowan Old Style, Baskerville, Georgia, serif"
    fontSize: "4.5rem"
    fontWeight: 400
    lineHeight: 0.96
    letterSpacing: "-0.035em"
  mono:
    fontFamily: "IBM Plex Mono, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  list-number:
    fontFamily: "Newsreader, Iowan Old Style, Baskerville, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.02em"
rounded:
  none: "0px"
  sm: "2px"
  md: "4px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "72px"
  4xl: "96px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.ink}"
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "{colors.ink}"
  button-primary-disabled:
    backgroundColor: "{colors.soft-neutral}"
    textColor: "{colors.muted-ink}"
  button-warm:
    backgroundColor: "{colors.primary-warm}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
    height: "44px"
  button-warm-hover:
    backgroundColor: "{colors.primary-warm-hover}"
    textColor: "{colors.paper}"
  button-warm-active:
    backgroundColor: "{colors.primary-warm-active}"
    textColor: "{colors.paper}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
    height: "44px"
  control-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    height: "44px"
  action-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.action-link}"
    typography: "{typography.label}"
  action-link-hover:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.action-link-hover}"
  action-link-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.action-link-active}"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "12px 14px"
    height: "44px"
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24px"
  app-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
  evidence-trace:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.deep-patrol}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "16px"
  divider:
    backgroundColor: "{colors.rule}"
    height: "1px"
  chart-secondary:
    backgroundColor: "{colors.copper}"
    textColor: "{colors.paper}"
  chart-tertiary:
    backgroundColor: "{colors.marine}"
    textColor: "{colors.paper}"
  chart-series-abyss:
    backgroundColor: "{colors.bar-abyss}"
    textColor: "{colors.paper}"
  chart-series-ocean:
    backgroundColor: "{colors.bar-ocean}"
    textColor: "{colors.paper}"
  chart-series-copper:
    backgroundColor: "{colors.bar-copper}"
    textColor: "{colors.paper}"
  chart-series-reef:
    backgroundColor: "{colors.bar-reef}"
    textColor: "{colors.paper}"
  chart-series-marine:
    backgroundColor: "{colors.bar-marine}"
    textColor: "{colors.paper}"
  separator-cool:
    backgroundColor: "{colors.separator-blue}"
    height: "1px"
  separator-warm:
    backgroundColor: "{colors.separator-bronze}"
    height: "1px"
  highlight-cool:
    backgroundColor: "{colors.highlight-lagoon}"
  highlight-warm:
    backgroundColor: "{colors.highlight-amber}"
  highlight-coral:
    backgroundColor: "{colors.highlight-coral}"
  activity-overlay:
    backgroundColor: "{colors.activity-backdrop}"
  activity-lightbox:
    backgroundColor: "{colors.activity-panel}"
    textColor: "{colors.paper}"
    rounded: "{rounded.md}"
    padding: "24px"
  activity-animation-yellow:
    backgroundColor: "{colors.animation-yellow}"
  activity-animation-amber:
    backgroundColor: "{colors.animation-amber}"
  summary-panel:
    backgroundColor: "{colors.activity-panel}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "28px"
  summary-panel-eyebrow:
    backgroundColor: "{colors.activity-panel}"
    textColor: "{colors.animation-yellow}"
    typography: "{typography.label}"
  summary-panel-number:
    backgroundColor: "{colors.activity-panel}"
    textColor: "{colors.animation-yellow}"
    typography: "{typography.list-number}"
  numbered-list-index:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.action-link}"
    typography: "{typography.list-number}"
  status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.paper}"
  status-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.paper}"
  status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.paper}"
---

# DESIGN.md

## Overview

Create professional work that is analytical, calm, lively, and slightly warm. Light
mode is the expected output unless explicitly overridden. The canvas should read as
near-white rather than cream or beige.

The system should feel energetic enough to be approachable, but never childish,
neon, or visually loud. Personality comes from sunlit amber actions, warm coral
counterpoints, deep ocean structure, purposeful typography, and content-specific
composition.

This is a personal design foundation, not a universal template. Before designing,
identify the audience, task, medium, and decision the artifact supports. Choose one
subject-specific visual signature rather than automatically combining oversized
headlines, serif italics, numbering, grids, and editorial columns.

### Signature: the evidence trace

When the subject involves analysis, recommendations, risk, or decisions, connect the
main claim to its provenance:

```text
Finding or decision
│
├─ E01  Source or observation
├─ E02  Supporting measure
└─ A01  Assumption or unresolved limitation
```

The trace may appear as a margin rail, compact source block, annotated rule, or
claim-to-evidence matrix. It must expose something true about the content. For work
without formal evidence, use a decision-rationale trace: choice, reason, implication,
and owner.

## Colors

### Primary system

- **Sunlit amber (`#EDB86C`):** default primary for button backgrounds, selected
  controls, active navigation marks, and high-attention actions. Pair it with Ink.
- **Golden amber (`#E6AD6A`):** hover state.
- **Burnished amber (`#C68148`):** pressed state and compact emphasis.
- **Coral copper (`#A45F3F`):** companion action colour for presentations,
  storytelling, invitations, or a second high-attention moment.
- **Coral copper hover (`#914F34`)** and **active (`#7D412C`)**: interaction states.
- **Action copper (`#93583A`):** accessible action-link text on Paper or Canvas.

Use Sunlit amber as the normal product primary. It should stand out clearly from the
Canvas in the same way as a bright physical highlighter, while remaining warmer and
less fluorescent. Use Coral copper for a second, more grounded action. Do not give
both equal dominance in the same region. Coral copper is expressive colour, not a
substitute for semantic Danger.

### Foundation

- **Ink (`#1B211F`):** primary text and strong structure.
- **Muted ink (`#5F6662`):** supporting text and metadata.
- **Canvas (`#F6F5F1`):** near-white background with only slight warmth.
- **Paper (`#FFFDF9`):** panels, documents, tables, and form surfaces.
- **Soft neutral (`#ECEDEA`):** quiet selection and code surfaces.
- **Rule (`#D5D8D3`):** standard dividers.
- **Deep patrol (`#1F5552`):** restrained supporting tone for evidence and inverse
  sections; no longer the primary brand colour.
- **Success, warning, and danger:** semantic use only.

### Photographic accents

- **Bars:** Abyss navy (`#02225E`), Ocean patrol (`#036D92`), Burnished copper
  (`#93583A`), Reef olive (`#49452E`), and Deep marine (`#0E3C75`).
- **Separators:** Waterline blue (`#70A0C6`) and Kelp bronze (`#8A714D`).
- **Highlights:** Lagoon teal (`#0387AD`), Sunset amber (`#C68148`), and Coral clay
  (`#B8764B`).

Use Ink, Canvas, and Paper for most of the composition. A normal interface region
uses one dominant primary and at most one supporting accent. Charts may use up to
five bar colours when persistent categories require them; otherwise use one focal
series and neutral context.

Use separator colours as fine rules or at 30–50% opacity. Highlights are for small
marks, selected points, annotations, and short strokes—not normal-sized text.

### Verified contrast on Paper

| Colour | Contrast |
|---|---:|
| Ink | 16.10:1 |
| Muted ink | 5.80:1 |
| Ink on Sunlit amber | 9.09:1 |
| Ink on Golden amber | 8.22:1 |
| Ink on Burnished amber | 5.17:1 |
| Paper on Coral copper | 4.82:1 |
| Paper on Coral copper hover | 6.13:1 |
| Paper on Coral copper active | 7.76:1 |
| Action copper on Paper | 5.59:1 |
| Paper on Activity panel | 14.84:1 |

Recheck contrast in the implemented context, including hover, focus, disabled, chart,
and text-on-image states. Do not use colour alone to communicate meaning.

## Typography

Use IBM Plex Sans for interface and working content. Use IBM Plex Mono only for
identifiers, code, commands, configuration, timestamps, and diagnostics.

Newsreader is an optional editorial voice, not a default branding device. Use it for
one short phrase, ordinal, or annotation when a section benefits from reflective
emphasis. Never set long interface text in italics.

- Bound fluid display text approximately between 44px and 72px.
- Use oversized type only for landing statements, section openings, or conclusions.
- Routine dashboards and forms use compact functional headings.
- Use sentence case for headings and controls.
- Reserve uppercase for short classification labels.
- Keep body text at least 16px with line height around 1.5–1.7.
- Keep prose near 60–75 characters per line and never justify body text.
- Use `rem` for scalable type and preserve browser zoom.

## Layout

Use a 12-column desktop grid with a maximum content width around 1180–1280px and an
8px spacing rhythm. Reduce columns predictably for tablet and mobile.

Structure must encode meaning:

- Number stages only when sequence matters.
- Use grid lines only when they support alignment, comparison, or measurement.
- Use tables for repeated exact mappings.
- Use timelines for chronological change.
- Use diagrams for sequence, ownership, state, or dependency.
- Use cards only for independently meaningful objects or actions.
- Create separation with space and alignment before adding containers.

Responsive layouts become one column on small screens. Convert essential tables into
labelled records instead of forcing horizontal scrolling. Maintain 44px touch targets
and support reflow at 200% zoom.

## Elevation & Depth

The system is nearly flat. Hierarchy comes from typography, colour, spacing, rules,
and surface contrast.

- Standard panels use Paper with a 1px Rule border and no shadow.
- Important summary panels use the inverse treatment defined under Components and
  should be visually distinct from ordinary content panels.
- Most structural groupings remain unframed.
- One important temporary region may use a soft neutral shadow.
- A deliberate hard offset shadow is allowed for one project-specific signature.
- Never combine soft and hard shadows.
- Avoid floating card islands, nested elevation, glass effects, and backdrop blur.

## Shapes

Default corners are square or slightly softened at 2–4px.

- Use circles for status dots, identity marks, or data points.
- Use pills only for tags, filters, or compact status.
- Use coloured rules and short strokes to connect related information.
- Avoid decorative blobs, orbs, waves, or abstract neural-network forms.

## Components

### Summary panels

Important summaries must stand out from the light Canvas. Use one deliberate inverse
panel rather than another white card:

- Background: Abyss navy (`#02225E`).
- Primary text: Paper (`#FFFDF9`).
- Eyebrow and list indices: Sunset yellow (`#F4DB95`).
- Optional accent rule or compact callout: Sunlit amber (`#EDB86C`).
- Internal separators: Paper at approximately 14–18% opacity.
- Corners: square or 2px; no soft floating shadow.
- Padding: at least 28px desktop and 22px mobile.

Use a short uppercase eyebrow followed by a large, direct summary title. The panel may
occupy a full-width band or a substantial side column. Do not shrink it into a small
badge, tint it pastel, or repeat the inverse treatment across every section. Normally
use no more than one major summary panel per view.

### Numbered lists

Numbers are navigation anchors and must be easier to scan than body copy:

- Default index size: `2rem` / 32px.
- Sparse or presentation-style lists: up to `2.5rem` / 40px.
- Mobile minimum: `1.75rem` / 28px.
- Use Newsreader or Iowan Old Style with medium weight and tight line height.
- On light surfaces use Action copper (`#93583A`).
- Inside inverse summary panels use Sunset yellow (`#F4DB95`).
- Allocate a fixed 56–72px index column and align the number to the first line.
- Separate items with 20–28px vertical space and a quiet horizontal rule.
- Keep list body text at least 16px; increasing the number must not compress the copy.

Use leading zeroes (`01`, `02`, `03`) only when the sequence, count, or editorial
structure benefits from them. Do not number unrelated decorative cards.

### Actions

- Primary buttons use Sunlit amber with Ink text.
- Warm primary buttons use Coral copper with Paper text.
- Secondary buttons use Paper, an Ink border, and Ink text.
- Tertiary actions use underlined Action copper text. Hover darkens to `#6E3D2C`;
  active darkens to `#52312A`.
- Destructive actions use Danger with explicit wording.
- Keep one visually dominant action per region.
- Labels describe the result: “Build interview plan”, not “Continue”.

### Forms and navigation

- Place persistent labels above fields.
- Use Paper fields with a Rule border and 2px corners.
- Selected controls use Sunlit amber with Ink text.
- Focus uses Burnished amber with a visible 3px ring.
- Validation appears beside the field and in a focusable summary when needed.
- Never use placeholder text as the only label.
- Use an underline, border, or Ink/Ocean inversion for active navigation.
- Navigation must not silently start expensive work or discard state.

### Panels, evidence, and status

- Prefer full-width rows, matrices, tables, and lists over repeated equal cards.
- Never nest cards unless the inner object is independently actionable.
- Evidence traces identify sources (`E`), assumptions (`A`), limitations (`L`), and
  decisions (`D`) using text as well as colour.
- Keep provenance adjacent to the claim it supports.
- Use explicit states such as “Queued”, “Analysing evidence”, or “Needs review”.
- Never invent progress percentages.

### In-progress lightboxes

Use a dark, lively inverse treatment for material in-progress activity:

- Backdrop: Abyss (`#011136`) at approximately 78–84% opacity.
- Lightbox: Abyss navy (`#02225E`) with Paper text.
- Primary animation colour: Sunset yellow (`#F4DB95`).
- Secondary animation colour: Golden amber (`#E6AD6A`).
- Optional completion or hand-off flash: Sunlit amber (`#EDB86C`).

Show the real stage, current activity, and elapsed time. Use a short amber sweep,
sequential dots, or a restrained pulse around a status mark. Recommended timing is
1.1–1.5 seconds with ease-in-out movement. Do not simulate a percentage when progress
is indeterminate, and do not use generic AI orbits or decorative “thinking” particles.
With `prefers-reduced-motion`, replace animation with a static yellow status mark and
live text updates.

### Charts and diagrams

- Every visual answers a named question.
- State the supported conclusion in its title.
- Label units, periods, baselines, and sources.
- For persistent series use: Abyss navy, Ocean patrol, Burnished copper, Reef olive,
  then Deep marine.
- Use Lagoon teal, Sunset amber, and Coral clay for selected marks, thresholds, or
  compact annotations.
- Prefer bars, lines, dot plots, small multiples, and tables.
- Avoid 3D charts, gauges, decorative radial charts, and unnecessary legends.
- Diagrams use one dominant flow direction and labelled boundaries.

## Do's and Don'ts

### Do

- Lead with the finding, decision, or required action.
- Separate facts, interpretation, assumptions, recommendations, and next steps.
- Write in a calm, candid, precise voice with slight human warmth.
- Use real content and cite sources close to claims.
- Mark generated, inferred, placeholder, and verified content.
- Support keyboard use, semantic HTML, visible focus, reduced motion, and meaningful
  alternative text.
- Test contrast, greyscale comprehension, 200% zoom, keyboard flow, mobile reflow,
  empty states, errors, and loading states.
- Define one subject-specific signature before building.

### Don't

- Do not use purple, violet, lavender, lilac, mauve, or magenta.
- Do not use pastel, neon, fluorescent, candy-like, or screaming colour.
- Do not use decorative gradients, glows, blurred colour clouds, or glassmorphism.
- Do not use generic AI imagery: sparkles, brains, robots, circuits, or holograms.
- Do not default to a warm editorial broadsheet for every project.
- Do not automatically combine cream, serif italics, numbered stages, hairline grids,
  and square cards.
- Do not add agent avatars, “AI” badges, or thinking animations without a functional
  reason.
- Do not invent metrics, evidence, citations, or claims to complete a layout.
- Do not rely on hover, colour, position, or motion alone.

### Generation check

1. The artifact is light mode with only slight neutral warmth.
2. Sunlit amber or Coral copper provides a lively but controlled focal point.
3. The visual signature follows from the subject rather than an AI-design trend.
4. Editorial devices are conditional and encode real meaning.
5. Claims expose evidence, rationale, ownership, or limitations where relevant.
6. Component states and recovery paths are explicit.
7. Important summaries are visually distinct from ordinary panels.
8. Numbered lists use prominent, consistently aligned indices.
9. The design works without colour and without motion.
10. Decorative elements can each justify their presence.

Treat YAML tokens as normative values and prose as application guidance. Prioritise
correctness and safety, accessibility and usability, the user’s goal, information
hierarchy, this design direction, then decorative polish.
