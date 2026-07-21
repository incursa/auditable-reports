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

The synthetic project-health example under `skill/create-auditable-reports/assets/examples/project-health/` is the initial visual fixture. It is a reference point, not an immutable brand system.

## Evidence language

- Every important number must resolve to saved evidence.
- Cards, charts, and tables must have a valid `sourceId`.
- A quantitative narrative block may cite one source only when all quantitative claims in that block come from that source.
- Facts, inferences, open questions, and recommendations must be distinguishable.
- Source names must identify exact files, tables, views, workbook tabs, documents, or durable queries.
- Credentials, signed URLs, and connection strings never belong in an artifact or rendered report.

## Output contract

The default handoff is a self-contained interactive HTML file plus the canonical artifact and its evidence files. A script-free print edition is optional.

Acceptance checks:

- The title, visible title, and artifact title agree.
- The first meaningful section is an executive or technical summary.
- Desktop layout has no clipping, overlap, missing chart, or unreadable content.
- Narrow viewports reflow prose and cards; wide tables scroll inside their own region rather than widening the page.
- Source affordances work with pointer, keyboard, and touch input.
- The semantic fallback remains understandable without the interactive runtime.
- The print edition contains no scripts, dialogs, buttons, tooltips, or expandable controls.
- Validation passes before handoff.

## Baseline QA status

The supplied example passes artifact, interactive-HTML, and print-safety checks. It reproduces byte-for-byte through the installed renderer.

Desktop rendering is clean after the interactive runtime initializes. At a 390 px viewport, the current enhanced reader widens beyond the viewport: narrative text, chart content, and the detail table are clipped instead of remaining within a horizontally bounded region. This is a renderer-owned gap and must be fixed upstream before mobile responsiveness is considered part of the accepted baseline. Generated HTML should not be patched locally to hide it.
