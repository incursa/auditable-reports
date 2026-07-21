---
name: create-auditable-reports
description: Create evidence-backed analytical reports as self-contained interactive HTML, with an optional static print edition. Use when Codex needs to turn spreadsheets, CSV files, database queries, extracts, or reviewed analytical results into a durable executive or technical report with an answer-first narrative, metric cards, charts, audit tables, caveats, recommendations, and traceable source metadata; also use when revising or reproducing reports built from the canonical Data Analytics artifact format.
---

# Create Auditable Reports

Build reports from a canonical `artifact.json`, then let the shared Data Analytics renderer create the HTML. Keep analysis, provenance, presentation, and generated output separate so a future agent can revise the report without reverse-engineering the page.

## Start the job

1. Define the question, audience, decision, time window, comparison basis, and cutoff date.
2. Inventory every source and note whether it honors the requested cutoff.
3. Select one audience: `product stakeholders` for answer-first business reporting or `technical` for methods-first reporting.
4. Create a dedicated output directory. Preserve the source extracts or durable queries, reviewed result datasets, `artifact.json`, `source_notes.md`, and generated page together.
5. Read [report-workflow.md](references/report-workflow.md). Read [artifact-authoring.md](references/artifact-authoring.md) before writing `artifact.json`.

When the Data Analytics plugin is available, use its focused analysis skill first when appropriate, then use `$data-analytics:build-report` and `$data-analytics:visualize-data`. Treat those skills as authoritative for the current renderer and chart contract.

## Analyze before rendering

- Reconcile totals to the stated control and grain before drafting conclusions.
- Apply date cutoffs in source-system fields, not only file creation dates.
- Save reusable SQL or transformation code and bounded reviewed result files.
- Distinguish observed facts, inferred explanations, and unresolved questions.
- Never invent a metric, source, mapping, or historical state.
- Record unsupported requests and the evidence needed to answer them.

## Author the canonical artifact

Use `assets/starter/artifact.json` as a working example, not as a blank form. Replace all synthetic content and keep these top-level elements:

- `surface: "report"`
- `manifest` with the title, description, cards, charts, tables, sources, and ordered blocks
- `snapshot.datasets` containing bounded reviewed rows
- `sources` containing canonical provenance and query metadata

Open with a visible `Executive Summary`. Put interpretation in markdown blocks adjacent to the evidence it explains. Use metric cards for top-line status, charts for shape or comparison, and tables for exact lookup or audit detail. Give every source-backed card, chart, table, and single-source quantitative narrative block a valid `sourceId`.

## Render the report

Run from this skill directory or provide absolute paths:

```powershell
py scripts/render_report.py --artifact path\to\artifact.json --output path\to\report.html
```

The wrapper locates the installed Data Analytics plugin and invokes its canonical portable builder. Do not hand-code a parallel interactive page or edit generated `report.html` directly. Revise `artifact.json` and rerender.

If the user explicitly requests a print/PDF-friendly companion page, create it from the generated semantic fallback:

```powershell
py scripts/build_print_report.py --input path\to\report.html --output path\to\report_print.html
```

The print edition must contain no scripts, dialogs, buttons, tooltip elements, or expandable controls. It defaults to Letter landscape and includes static sources.

## Validate and hand off

Run:

```powershell
py scripts/check_report.py --artifact path\to\artifact.json --html path\to\report.html --print-html path\to\report_print.html
```

Apply [quality-checklist.md](references/quality-checklist.md). Treat the renderer receipt as the HTML structural/browser result. If it reports `structural_only`, keep the semantic chart table and disclose that compatible Chromium was unavailable.

Hand off the interactive HTML first, followed by the print edition only when requested. List the canonical artifact and relevant SQL/data/source notes as supporting files; do not replace the report with a chat summary.

## Bootstrap a new report

Use the starter copier when a blank report workspace is useful:

```powershell
py scripts/new_report.py --name "Quarterly Delivery Health" --output path\to\new-report
```

The copied files are synthetic placeholders. Replace them before presenting the report as real evidence.

## Package resources

- `references/report-workflow.md`: end-to-end workflow and folder conventions
- `references/artifact-authoring.md`: canonical artifact patterns and examples
- `references/quality-checklist.md`: pre-handoff validation checklist
- `references/sample-prompts.md`: reusable request patterns
- `assets/starter/`: synthetic starter artifact, data, brief, and source notes
- `assets/examples/project-health/`: rendered interactive and print examples
- `scripts/`: deterministic scaffolding, rendering, print extraction, and validation tools
