# Report quality checklist

## Analysis

- The report answers a stated question for a named audience.
- The population, grain, period, cutoff, denominator, and comparison are explicit.
- Control totals, row counts, duplicates, null keys, and material exceptions were checked.
- Every important number is traceable to saved evidence.
- Facts, inferences, and unresolved questions are distinguishable.

## Narrative

- The visible title matches the document title.
- A visible Executive Summary or Technical Summary appears first.
- Each major section begins with its takeaway.
- Each major finding pairs evidence with interpretation and an implication.
- Recommendations are supported by evidence.
- Decision-relevant caveats appear near the affected finding or in a visible caveat section.

## Visuals and tables

- Each chart answers one analytical question.
- Chart type matches the comparison and the data is sufficiently dense.
- Titles are neutral and subtitles state scope, units, or comparison basis.
- No redundant color encoding or misleading scale is used.
- Every chart has an adjacent explanatory paragraph.
- Chart.js print captures use fixed dimensions, disabled animation, blocked remote requests, and a text alternative.
- Tables use readable labels and reserve signed coloring for movement columns.
- The semantic chart table remains useful when browser chart rendering is unavailable.

## Provenance

- Every source-backed card, chart, and table resolves to a canonical source.
- Quantitative markdown has a source only under the single-source rule.
- Source names identify the exact file, table, view, or document.
- Queries record engine, execution time, and a readable description.
- No credentials, local secrets, or unsafe paths appear in the artifact.

## Output

- Standard reports compile from `.report.md` and `report.data.json`; advanced direct-artifact authoring is intentional and disclosed.
- Report Markdown uses only the documented metrics, bar/pie chart, table, and figure directives and stays within their hard limits.
- `artifact.json` validates and is preserved beside the report.
- The interactive HTML is self-contained and not edited by hand.
- Renderer verification is `passed` or the `structural_only` limitation is disclosed.
- The optional print HTML contains no scripts, dialogs, buttons, tooltips, or expandable controls.
- When charts are present, `report_charted.html` contains one embedded image per artifact chart and retains each exact-value semantic table.
- The print page uses readable page size, margins, table headers, and page breaks.
- CSS Paged Media defines a running title, `Page X of Y`, and explicit break utilities.
- Paged.js pagination runs with the pinned version and remote resources blocked unless reviewed assets require them.
- Paginated HTML contains Paged.js page elements, and PDF output has been opened or structurally checked before handoff.
