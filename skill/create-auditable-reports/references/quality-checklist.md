# Report quality checklist

## Analysis

- The report answers a stated question for a named audience.
- The population, grain, period, cutoff, denominator, and comparison are explicit.
- Control totals, row counts, duplicates, null keys, and material exceptions were checked.
- Every important number is traceable to saved evidence.
- Facts, inferences, and unresolved questions are distinguishable.

## Narrative

- The visible title matches the document title.
- The visible first section matches the document profile: Executive Summary, Technical Summary, Lesson Overview, or Entry Summary.
- Decision briefs place Immediate Direction directly after Executive Summary and keep that material on page 1.
- Each major section begins with its takeaway.
- Avoid a heading-only Markdown section immediately before a titled chart or table unless the extra section label adds meaning.
- Each major finding pairs evidence with interpretation and an implication.
- Recommendations are supported by evidence.
- Decision-relevant caveats appear near the affected finding or in a visible caveat section.

## Visuals and tables

- Every included chart answers one analytical question; charts are not required.
- Chart type matches the comparison and the data is sufficiently dense.
- Titles are neutral and subtitles state scope, units, or comparison basis.
- No redundant color encoding or misleading scale is used.
- Every chart has an adjacent explanatory paragraph.
- Chart.js print captures use fixed dimensions, disabled animation, blocked remote requests, and a text alternative.
- Tables use readable labels and reserve signed coloring for movement columns.
- Decision tables use semantic column roles; no rendered column falls below its readable minimum or overflows the page.
- The semantic chart table remains useful when browser chart rendering is unavailable.

## Provenance

- Every source-backed card, chart, and table resolves to a canonical source.
- Quantitative markdown has a source only under the single-source rule.
- Source names identify the exact file, table, view, or document.
- Queries record engine, execution time, and a readable description.
- No credentials, local secrets, or unsafe paths appear in the artifact.
- A stakeholder edition may hide sources or omit charts, but the canonical evidence package still retains every selected and unselected requirement, conflict, decision, source, and provenance record.
- Evidence item IDs are unique across all evidence collections.

## Output

- Standard reports compile from `.report.md` and `report.data.json`; advanced direct-artifact authoring is intentional and disclosed.
- Report Markdown uses only the documented metrics, bar/pie chart, table, and figure directives and stays within their hard limits.
- `artifact.json` validates and is preserved beside the report.
- The interactive HTML is self-contained and not edited by hand.
- Renderer verification is `passed` or the `structural_only` limitation is disclosed.
- The optional print HTML contains no scripts, dialogs, buttons, tooltips, or expandable controls.
- When charts are present, `report_charted.html` contains one embedded image per artifact chart and retains each exact-value semantic table.
- The print page uses explicit dimensions for the requested size/orientation, readable margins, table headers, and page breaks.
- Every PDF page `MediaBox` matches the requested size and orientation.
- Source visibility matches the edition policy; `date-only` output contains no time or timestamp.
- Charts omitted from the edition do not leave companion chart tables behind.
- Pagination does not leave avoidable half-empty pages; headings stay with their first content, atomic visuals stay intact, and short source lists use remaining final-page space when available.
- CSS Paged Media defines a running title, `Page X of Y`, and explicit break utilities.
- Paged.js pagination runs with the pinned version and remote resources blocked unless reviewed assets require them.
- Paginated HTML is generated for every PDF build and contains Paged.js page elements.
- Automated pagination checks cover table overflow, semantic minimum widths, intermediate blank pages, stranded headings, and awkwardly split short numbered lists; warnings are reviewed.
- The PDF is written atomically or a clearly named locked-file fallback is reported, and the final file has been opened or structurally checked before handoff.
