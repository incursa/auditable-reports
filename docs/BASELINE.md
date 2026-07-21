# Report baseline

This document defines what “good-looking” means for this repository in terms that remain useful even if the renderer or authoring syntax changes.

## Reader experience

A report should be calm, compact, and answer-first. The reader should be able to understand the conclusion before inspecting the audit detail.

The expected reading order is:

1. Reader-facing title and current-as-of metadata.
2. Executive or technical summary with the answer first.
3. Headline metrics, when they clarify status.
4. Definitions and comparison basis.
5. Findings organized as claim, evidence, interpretation, and implication.
6. Exact detail or exception tables.
7. Recommended actions and unresolved questions.
8. Caveats and source details.

## Visual language

- Use generous whitespace and a narrow reading measure for prose.
- Use a clear hierarchy with restrained typography rather than decorative chrome.
- Use cards only for a small set of distinct headline metrics.
- Use one chart per analytical question and place interpretation beside it.
- Use tables for exact lookup and audit detail; allow horizontal scrolling when columns cannot remain legible.
- Use color sparingly and semantically. Signed positive/negative coloring is appropriate only when direction has a defined meaning.
- Keep report titles and chart titles neutral. Put scope, unit, cutoff, and comparison basis in supporting text.
- Retain useful content in the semantic fallback when scripts or chart rendering are unavailable.
- Materialize selected print charts as embedded images with fixed dimensions and no runtime scripts; retain the exact-value table directly below each image.

The synthetic project-health example under `skill/create-auditable-reports/assets/examples/project-health/` is the initial visual fixture. It is a reference point, not an immutable brand system.

## Evidence language

- Every important number must resolve to saved evidence.
- Cards, charts, and tables must have a valid `sourceId`.
- A quantitative narrative block may cite one source only when all quantitative claims in that block come from that source.
- Facts, inferences, open questions, and recommendations must be distinguishable.
- Source names must identify exact files, tables, views, workbook tabs, documents, or durable queries.
- Credentials, signed URLs, and connection strings never belong in an artifact or rendered report.

## Output contract

The default handoff is a self-contained interactive HTML file plus the canonical artifact and its evidence files. Paginated output is optional and has four explicit stages:

1. `report_print.html`: script-free, self-contained pagination source with CSS Paged Media rules.
2. `report_charted.html`: optional Chart.js-materialized source with embedded PNG visuals and semantic tables.
3. `report_paged.html`: Paged.js browser preview when requested.
4. `report.pdf`: Paged.js PDF handoff when requested.

Acceptance checks:

- The title, visible title, and artifact title agree.
- The first meaningful section is an executive or technical summary.
- Desktop layout has no clipping, overlap, missing chart, or unreadable content.
- Narrow viewports reflow prose and cards; wide tables scroll inside their own region rather than widening the page.
- Source affordances work with pointer, keyboard, and touch input.
- The semantic fallback remains understandable without the interactive runtime.
- Every Chart.js image has a text alternative, fixed capture dimensions, disabled animation, and an adjacent semantic table with exact values.
- The print edition contains no scripts, dialogs, buttons, tooltips, or expandable controls.
- Paged pages show a running report title and `Page X of Y`.
- Deliberate section breaks use `.page-break`; cards, charts, and other atomic content use `.avoid-break` or equivalent component rules.
- Paged.js runs with remote requests blocked unless every remote dependency was reviewed and intentionally allowed.
- Paginated HTML is normalized to remove Paged.js run-specific DOM identifiers. PDF validation is structural because browser-generated PDF metadata may vary between runs.
- Validation passes before handoff.

## Baseline QA status

The supplied example passes artifact, interactive-HTML, Chart.js-materialization, and print-safety checks. It reproduces byte-for-byte through the installed renderer and through the controlled Chart.js/Paged.js browser pipeline in the validated environment.

Desktop rendering is clean after the interactive runtime initializes. At a 390 px viewport, the current enhanced reader widens beyond the viewport: narrative text, chart content, and the detail table are clipped instead of remaining within a horizontally bounded region. This is a renderer-owned gap and must be fixed upstream before mobile responsiveness is considered part of the accepted baseline. Generated HTML should not be patched locally to hide it.
