---
name: create-auditable-reports
description: Create evidence-backed documents from constrained Report Markdown or the canonical artifact format as self-contained interactive HTML, with optional Chart.js visuals and Paged.js paginated HTML/PDF editions. Use for analytical reports, stakeholder decision briefs, technical reviews, lesson plans, journals, and revisions that need prose, code, screenshots, bounded tables, simple charts, source metadata, or a canonical evidence package.
---

# Create Auditable Reports

Build reports from a canonical `artifact.json`, then let the shared Data Analytics renderer create the HTML. Keep analysis, provenance, presentation, and generated output separate so a future agent can revise the report without reverse-engineering the page.

## Start the job

1. Define the question, audience, decision, time window, comparison basis, and cutoff date.
2. Inventory every source and note whether it honors the requested cutoff.
3. Select one document profile: `report`, `decision-brief`, `technical`, `lesson`, or `journal`. Keep quantitative claims source-backed in every profile.
4. Create a dedicated output directory. Preserve the source extracts or durable queries, reviewed result datasets, `artifact.json`, `source_notes.md`, and generated page together.
5. Read [report-workflow.md](references/report-workflow.md). For standard authoring, read [report-markdown.md](references/report-markdown.md); for direct artifact work, read [artifact-authoring.md](references/artifact-authoring.md).

When the Data Analytics plugin is available, use its focused analysis skill first when appropriate, then use `$data-analytics:build-report` and `$data-analytics:visualize-data`. Treat those skills as authoritative for the current renderer and chart contract.

## Analyze before rendering

- Reconcile totals to the stated control and grain before drafting conclusions.
- Apply date cutoffs in source-system fields, not only file creation dates.
- Save reusable SQL or transformation code and bounded reviewed result files.
- Distinguish observed facts, inferred explanations, and unresolved questions.
- Never invent a metric, source, mapping, or historical state.
- Record unsupported requests and the evidence needed to answer them.

## Author the report

For a standard report, write `report.report.md` plus its `report.data.json` sidecar. For a decision brief, write `stakeholder-report.md` plus `evidence-package.json`; the evidence package remains complete even when the stakeholder edition hides sources or omits charts. Use ordinary Markdown for prose and code. Use only the standard metrics, optional bar/pie chart, semantic table, and figure directives. Compile before rendering:

```powershell
py scripts/compile_report.py --input path\to\report.report.md --output path\to\artifact.json
```

Use direct artifact authoring only when a reviewed requirement cannot fit the constrained language.

## Author the canonical artifact

Use `assets/starter/artifact.json` as a working example, not as a blank form. Replace all synthetic content and keep these top-level elements:

- `surface: "report"`
- `manifest` with the title, description, cards, charts, tables, sources, and ordered blocks
- `snapshot.datasets` containing bounded reviewed rows
- `sources` containing canonical provenance and query metadata

Open with the visible summary required by the selected document profile. Put interpretation in markdown blocks adjacent to the evidence it explains. Use metric cards for top-line status, charts for shape or comparison, and tables for exact lookup or audit detail. Give every source-backed card, chart, table, and single-source quantitative narrative block a valid `sourceId`.

## Render the report

Run from this skill directory or provide absolute paths:

```powershell
py scripts/render_report.py --artifact path\to\artifact.json --output path\to\report.html
```

The wrapper locates the installed Data Analytics plugin and invokes its canonical portable builder. Do not hand-code a parallel interactive page or edit generated `report.html` directly. Revise `artifact.json` and rerender.

Prefer the complete bundle command for printable work:

```powershell
py scripts/build_report_bundle.py --input path\to\report.report.md --output-dir path\to\output
```

It compiles, renders, produces a script-free print source, materializes charts only when present, creates paginated HTML on every run, and writes the PDF atomically. Front matter controls the safe print profile; `--orientation`, `--page-size`, `--pdf-name`, `--source-display`, and `--date-display` override it. If the requested PDF is locked, the build preserves it and writes a clearly named `.locked-<timestamp>.pdf` fallback.

Use the individual stages only for diagnosis. Pass `--artifact` to print and pagination stages so semantic widths and page-level checks remain active.

When the artifact contains a supported chart, read [chartjs-visuals.md](references/chartjs-visuals.md), then use pinned Chart.js to materialize it into the script-free print source:

```powershell
py scripts/render_chartjs_output.py --artifact path\to\artifact.json --input path\to\report_print.html --output path\to\report_charted.html
```

Then use pinned Paged.js to create a browser-previewable paginated HTML file or PDF. Use `report_charted.html` when it exists; otherwise use `report_print.html`:

```powershell
py scripts/render_paged_output.py --input path\to\report_charted.html --output path\to\report_paged.html
py scripts/render_paged_output.py --input path\to\report_charted.html --output path\to\report.pdf
```

Run `npm install` at the repository root once to install pinned Chart.js, Paged.js, and browser-control dependencies. Both wrappers locate installed Chrome or Edge and do not modify the interactive report. The Chart.js stage always blocks remote requests. Paged.js blocks them by default; use `--allow-remote` only when reviewed report assets genuinely require it.

## Validate and hand off

Run:

```powershell
py scripts/check_report.py --artifact path\to\artifact.json --html path\to\report.html --print-html path\to\report_print.html --charted-html path\to\report_charted.html --paged-html path\to\report_paged.html --pdf path\to\report.pdf
```

Apply [quality-checklist.md](references/quality-checklist.md). Treat the renderer receipt as the HTML structural/browser result. If it reports `structural_only`, keep the semantic chart table and disclose that compatible Chromium was unavailable.

Hand off the interactive HTML first, followed by the print edition only when requested. List the canonical artifact and relevant SQL/data/source notes as supporting files; do not replace the report with a chat summary.

## Bootstrap a new report

Use the starter copier when a blank report workspace is useful. It creates `rebuild-report.ps1` beside the editable sources:

```powershell
py scripts/new_report.py --name "Quarterly Delivery Health" --output path\to\new-report
```

For a decision brief:

```powershell
py scripts/new_report.py --name "Contract Direction" --document-type decision-brief --output path\to\contract-direction
```

The default starter uses Report Markdown. Pass `--format artifact` only for advanced direct-artifact work. All copied files are synthetic placeholders; replace them before presenting the report as real evidence.

## Package resources

- `references/report-workflow.md`: end-to-end workflow and folder conventions
- `references/artifact-authoring.md`: canonical artifact patterns and examples
- `references/report-markdown.md`: constrained Markdown syntax, standard blocks, and hard limits
- `references/test-library.md`: synthetic lesson, report, journal, and incident-review fixtures
- `references/chartjs-visuals.md`: supported Chart.js print forms and deterministic capture rules
- `references/quality-checklist.md`: pre-handoff validation checklist
- `references/sample-prompts.md`: reusable request patterns
- `assets/starter/`: synthetic starter artifact, data, brief, and source notes
- `assets/examples/project-health/`: rendered interactive, Chart.js, and paginated print examples
- `assets/examples/report-markdown/`: source, data, figure, and compiled DSL fixture
- `assets/examples/test-library/`: varied synthetic authoring fixtures for feature and print testing
- `scripts/`: deterministic scaffolding, rendering, print extraction, Chart.js materialization, Paged.js pagination, and validation tools
