# Report Generation Agent Guide

This document is a standalone operating description for an agent that creates
auditable reports with this repository. It explains the current authoring
language, report structures, evidence rules, rendering pipeline, validation
contract, and known gaps.

The default objective is not “generate attractive HTML.” The objective is:

> Turn reviewed evidence into a durable, answer-first report whose prose,
> numbers, visuals, exact-value tables, assumptions, and sources can be revised
> and regenerated without reverse-engineering the rendered page.

## Agent mission

The report-generation agent should:

1. Frame the question, audience, decision, time window, cutoff, population,
   grain, exclusions, and comparison basis.
2. Inspect and validate the supplied evidence before drafting conclusions.
3. Write ordinary reports in constrained Report Markdown.
4. Keep reviewed datasets and source metadata in the JSON sidecar.
5. Compile the authoring files into the canonical `artifact.json`.
6. Use the shared renderer for interactive HTML.
7. Use Chart.js and Paged.js only at the controlled print boundary.
8. Validate the complete bundle before handoff.
9. Preserve limitations and missing evidence instead of inventing data,
   provenance, mappings, historical state, or methodology.

## Non-negotiable architecture

```text
report.report.md
  + report.data.json
          |
          v
     artifact.json          canonical intermediate representation
          |
          v
 shared Data Analytics renderer
          |
          +--> report.html  self-contained interactive report
          |
          +--> report_print.html
                    |
                    v
             Chart.js 4.5.1
                    |
                    v
             report_charted.html
                    |
                    v
              Paged.js 0.4.3
                    |
                    +--> report_paged.html
                    +--> report.pdf
```

The boundaries matter:

- `report.report.md` owns prose, reading order, and standard report blocks.
- `report.data.json` owns bounded, reviewed rows and source records.
- `artifact.json` is the canonical, auditable representation used by every
  renderer.
- `report.html`, print HTML, paginated HTML, and PDF are generated output.
- Generated HTML must never become the authoring source.
- Chart.js materializes static print charts; it does not define report
  semantics.
- Paged.js paginates an already-authored report; it does not interpret evidence.
- The installed Data Analytics renderer owns the interactive reader, shared
  styling, source affordances, responsive behavior, and semantic fallback.

If a requirement cannot fit Report Markdown, use the canonical artifact
directly or extend the compiler deliberately. Do not bypass the artifact by
hand-writing a separate HTML report.

## Required intake

Before authoring, establish a short report brief containing:

- Question the report must answer
- Primary audience and decision owner
- Decision or action the report should support
- Reporting period and cutoff date
- Population and row grain
- Material inclusions and exclusions
- Denominator or control total
- Comparison baseline
- Requested outputs: interactive HTML, print preview, PDF, or supporting files
- Conditions for sign-off
- Known missing evidence or access limitations

For every input, record:

- Exact file, workbook tab, table, view, query, document, or system
- Query or transformation that produced exposed rows
- Query execution or extraction timestamp
- Field used to enforce the reporting cutoff
- Expected population and grain
- Row counts, distinct keys, nulls, duplicates, and control totals
- Known historical-state limitations

Do not assume that an extract date is the accounting cutoff. A current database
may contain late-posted activity assigned to an earlier period.

## Recommended report workspace

Use one directory per real report:

```text
report-name/
  report-brief.md
  report.report.md
  report.data.json
  source_notes.md
  artifact.json
  report.html
  report_print.html
  report_charted.html
  report_paged.html
  report.pdf
  queries/
  data/
  images/
  analysis/
```

Keep raw inputs read-only. Save normalized, aggregated, or reviewed report rows
separately. Use deterministic file names and stable dataset, source, block,
chart, and table IDs.

Real customer reports should normally remain outside public fixtures and
examples. Never commit credentials, signed URLs, connection strings, secrets,
or customer data to this repository.

## Report Markdown v0.1

Report Markdown uses ordinary Markdown plus four bounded directives:

- `metrics`
- `chart`
- `table`
- `figure`

It is a report outline, not a web framework. The compiler chooses safe layout
and produces `artifact.json`; the DSL is never rendered directly.

### Front matter and title

Every file begins with flat front matter and exactly one level-one title:

```markdown
---
document-type: report
description: Review of portfolio delivery health through June 30.
generated-at: 2026-07-23T15:00:00Z
status: ready
data: report.data.json
---
# Portfolio Delivery Health
```

Required fields:

| Field | Meaning |
| --- | --- |
| `description` | One-sentence scope |
| `generated-at` | ISO timestamp for this snapshot |
| `status` | `ready`, `partial`, `blocked`, or `fixture` |
| `data` | Relative path to the JSON sidecar |

`document-type` is optional and defaults to `report`.

### Document profiles

Profiles change the required opening vocabulary, not the design:

| `document-type` | Required first section | Typical use |
| --- | --- | --- |
| `report` | `## Executive Summary` | Business, leadership, reconciliation, status, or decision reports |
| `technical` | `## Technical Summary` | Methods, validation, system, or engineering reviews |
| `lesson` | `## Lesson Overview` | Lesson plans and instructional documents |
| `journal` | `## Entry Summary` | Reflective or journal-style documents |

All profiles use the same blocks, artifact contract, renderer, and limits.

### Ordinary Markdown

Use normal Markdown for:

- Headings
- Paragraphs
- Bold and emphasis
- Ordered and unordered lists
- Links
- Blockquotes
- Horizontal rules
- Inline code
- Triple-backtick code blocks

Each peer `##` section becomes one ordered artifact Markdown block. Use a
separate `##` section for each major independently editable report segment.
Use `###` only for subordinate material that belongs inside the same segment.

Do not use Markdown image syntax. Use the `figure` directive so the compiler can
validate, embed, describe, and print the image safely.

### Source a quantitative narrative section

When every quantitative statement in one Markdown section comes from the same
source, add:

```markdown
## Two projects explain the remaining variance

<!-- source: project_snapshot -->

Atlas and Cedar account for $3.2M of the current difference.
```

One Markdown block may reference only one source. Split a section when its
quantitative claims come from different sources. Do not attach a source merely
to create a source button, and never guess provenance.

### JSON sidecar

The sidecar contains exactly `datasets` and `sources`:

```json
{
  "datasets": {
    "projects": [
      {
        "project": "Atlas",
        "budget": 1200000,
        "forecast": 1480000,
        "variance": 280000
      }
    ]
  },
  "sources": [
    {
      "id": "project_snapshot",
      "label": "Reviewed project forecast snapshot",
      "path": "data/projects.csv",
      "query": {
        "engine": "duckdb",
        "language": "sql",
        "id": "project-health",
        "executed_at": "2026-07-23T14:45:00Z",
        "description": "Loads the reviewed project-level forecast snapshot.",
        "sql": "SELECT * FROM read_csv_auto('data/projects.csv', header = true)"
      }
    }
  ]
}
```

The agent must prepare chart- and table-ready rows before authoring the DSL.
The DSL does not calculate joins, derived fields, rolling windows, cohorts,
controls, or aggregations.

### Metric strip

Use metric cards for a small set of distinct headline values:

```markdown
::: metrics
id: headline_metrics
dataset: headline
source: project_snapshot
metric: active_projects | Active projects | number | Projects in the reviewed scope.
metric: forecast_variance | Forecast variance | currency | Forecast less approved budget. | signed
metric: completion | Overall completion | percent | Weighted portfolio completion.
:::
```

Each metric line is:

```text
field | label | format | optional description | optional signed
```

Formats are `number`, `currency`, and `percent`. Percent values are decimal
fractions: use `0.99` for `99%`.

Use `signed` only when positive and negative direction has a defined meaning.
Do not use metric strips as decorative dashboard tiles or repeat the same
measure in several forms.

### Bar chart

Use a bar chart for comparisons, rankings, or signed variances:

```markdown
::: chart
id: variance_by_project
type: bar
title: Forecast variance by project
subtitle: Forecast less approved budget through June 30
dataset: projects
source: project_snapshot
category: project
value: variance
category-label: Project
value-label: Forecast variance
format: currency
:::
```

The title should describe what is plotted. Put the finding and implication in
the adjacent Markdown section, not in the chart title.

### Pie chart

Use a pie chart only for a rough part-to-whole comparison with a small number of
positive, mutually exclusive categories:

```markdown
::: chart
id: budget_by_region
type: pie
title: Approved budget by region
subtitle: Current portfolio plan
dataset: regions
source: project_snapshot
category: region
value: budget
category-label: Region
value-label: Approved budget
format: currency
:::
```

Aggregate small categories into `Other`. Do not use a pie chart for signed
values or when comparing bar length would be clearer.

### Table

Use tables for exact lookup, reconciliation, and audit detail:

```markdown
::: table
id: project_detail
title: Project reconciliation detail
subtitle: Reviewed values through June 30
dataset: projects
source: project_snapshot
column: project | Project | text
column: owner | Owner | text
column: budget | Budget | currency
column: forecast | Forecast | currency
column: variance | Variance | currency | movement
column: completion | Completion | percent
sort: variance | desc
:::
```

Column formats are:

- `text`
- `date`
- `number`
- `currency`
- `percent`

`movement` is the only visual semantic. Apply it only to a signed,
decision-relevant movement column. The `sort` field must be one of the displayed
columns.

### Figure or screenshot

Use a figure for screenshots, diagrams, illustrations, or other supplied
images:

```markdown
::: figure
id: workflow_screenshot
path: images/workflow.png
alt: Workflow screen showing the approved review state.
caption: Review state after the June close.
source: workflow_capture
:::
```

Supported files are relative PNG, JPEG, WebP, GIF, or SVG files. `alt` is
required. The compiler embeds the image so the report remains self-contained.

The interactive reader isolates the figure in a sandbox. The print extractor
flattens only the compiler-owned figure vocabulary and discards scripts,
styles, events, external images, and unrecognized markup.

## Current hard limits

These are compiler rules, not suggestions:

| Item | Limit |
| --- | ---: |
| Metrics in one strip | 1–6 |
| Bar-chart rows | 2–12 |
| Pie slices | 2–6 |
| Table columns | 1–8 |
| Table rows | 50 |
| Rows in any artifact dataset | 200 |
| Embedded figure size | 5 MB |

When a report exceeds a limit:

1. Pre-aggregate the data.
2. Split evidence into purposeful sections or tables.
3. Keep the decision-relevant subset in the report.
4. Put long-form audit detail in a separate supporting attachment.
5. Use direct artifact authoring only when the richer requirement remains
   appropriate for the report reader.

Do not silently truncate evidence.

## Recommended report structures

### Executive or reconciliation report

1. Title
2. Executive Summary
3. Headline metrics, when useful
4. Scope, definitions, cutoff, and control basis
5. Finding sections with nearby charts or tables
6. Exact exception detail
7. Recommended actions
8. Further questions
9. Caveats, uncertainty, and source limitations

### Technical report

1. Title
2. Technical Summary
3. System or population definition
4. Method and validation controls
5. Findings with exact evidence
6. Failure modes or exceptions
7. Recommendations
8. Reproduction notes and caveats

### Lesson

1. Title
2. Lesson Overview
3. Outcomes and definitions
4. Teaching sequence
5. Visual aid or example
6. Discussion prompts
7. Facilitator notes
8. Sources and safeguards

### Journal

1. Title
2. Entry Summary
3. Narrative or observations
4. Small supporting table or chart when meaningful
5. Reflection
6. Next action or question
7. Optional source context

### Complex report pattern

For a complicated report, organize by analytical question rather than data
source:

```text
Executive Summary
Definitions and comparison basis

Finding A
  claim and interpretation
  metric strip or chart
  exact-value table when needed
  implication or action

Finding B
  claim and interpretation
  chart or figure
  caveat close to the affected evidence

Cross-cutting exceptions
  bounded audit-detail table

Recommendations
Further questions
Caveats and assumptions
```

Every chart must have an adjacent explanatory paragraph answering:

- What does the chart show?
- What is the supported takeaway?
- Why does it matter?
- What caveat changes the interpretation?

Tables provide exact values; they do not replace narrative interpretation.

## Provenance and status rules

Every card, chart, and table must resolve to a canonical source. Quantitative
Markdown should use a source only under the one-source-per-block rule.

Prefer a source record containing:

- Stable source ID
- Human-readable label
- Relative file or query path
- Actual runnable SQL or reproducible transformation
- Query engine and language
- Execution timestamp
- Query description
- Tables or files used
- Cutoff filters and material exclusions
- Metric definitions when business logic is not obvious

Use report status honestly:

| Status | Meaning |
| --- | --- |
| `ready` | Evidence and required controls are complete enough for the stated use |
| `partial` | Useful report, but material evidence, provenance, or validation is incomplete |
| `blocked` | The report cannot answer its question without named missing evidence or access |
| `fixture` | Synthetic test material only |

### Document-derived widget data

The current portable artifact validator expects cards, charts, and tables to
have runnable SQL provenance or a source path ending in `.sql`. This is stricter
than the general source model, which also allows files and documents.

For values reconstructed from a supplied document or HTML report:

1. Preserve the original document as an upstream source.
2. Create an honest, runnable extraction or literal-value reconstruction query
   that reproduces the exposed rows.
3. Label that query as a reconstruction, not as a source-system query.
4. Bind quantitative widgets to the reconstruction source.
5. Bind narrative claims to the original document when that is the actual
   evidence.
6. Mark the report `partial` if upstream workbooks, queries, extracts, or
   controls were not available for independent recalculation.

Never invent SQL or imply that a reconstruction queried the operational system.

## Build commands

Run commands from the repository root.

Create a starter:

```powershell
py skill\create-auditable-reports\scripts\new_report.py `
  --name "Quarterly Delivery Health" `
  --output .work\quarterly-delivery-health
```

Install pinned browser dependencies once:

```powershell
npm install
```

Build the complete default bundle:

```powershell
py skill\create-auditable-reports\scripts\build_report_bundle.py `
  --input .work\quarterly-delivery-health\report.report.md `
  --output-dir .work\quarterly-delivery-health
```

The bundle command compiles, renders interactive HTML, creates script-free print
HTML, materializes supported charts, paginates HTML, and creates PDF.

Compile only:

```powershell
py skill\create-auditable-reports\scripts\compile_report.py `
  --input path\to\report.report.md `
  --output path\to\artifact.json
```

Render only:

```powershell
py skill\create-auditable-reports\scripts\render_report.py `
  --artifact path\to\artifact.json `
  --output path\to\report.html
```

Create portrait print output with individual stages:

```powershell
py skill\create-auditable-reports\scripts\build_print_report.py `
  --input path\to\report.html `
  --output path\to\report_print.html `
  --page-size Letter `
  --orientation portrait
```

```powershell
py skill\create-auditable-reports\scripts\render_chartjs_output.py `
  --artifact path\to\artifact.json `
  --input path\to\report_print.html `
  --output path\to\report_charted.html
```

```powershell
py skill\create-auditable-reports\scripts\render_paged_output.py `
  --input path\to\report_charted.html `
  --output path\to\report_paged.html

py skill\create-auditable-reports\scripts\render_paged_output.py `
  --input path\to\report_charted.html `
  --output path\to\report.pdf
```

The bundle currently uses the print builder's default `Letter landscape`.
Use the individual print stages when another orientation or CSS page size is
required.

## Validation contract

Validate every handoff:

```powershell
py skill\create-auditable-reports\scripts\check_report.py `
  --artifact path\to\artifact.json `
  --html path\to\report.html `
  --print-html path\to\report_print.html `
  --charted-html path\to\report_charted.html `
  --paged-html path\to\report_paged.html `
  --pdf path\to\report.pdf
```

The agent should also verify:

- Visible title matches the artifact title.
- Required opening section matches the document profile.
- Important numbers reconcile to saved evidence.
- Population, grain, period, cutoff, denominator, and comparison are explicit.
- Facts, inferences, recommendations, and unresolved questions are distinct.
- Every widget source resolves.
- Every chart has an adjacent interpretation.
- Chart signs, scales, labels, and units are honest.
- Tables remain readable and preserve exact values.
- Figures have meaningful alternative text.
- Interactive HTML is self-contained.
- Desktop and narrow layouts do not clip or widen the page.
- Source controls open and expose the expected metadata.
- Print HTML contains no scripts, dialogs, buttons, or tooltips.
- Charted print HTML contains one static image and one semantic table per chart.
- Paged HTML has running matter and `Page X of Y`.
- PDF and paginated HTML have no blank or avoidably sparse pages.
- Remote requests remain blocked unless explicitly reviewed.

If the renderer reports `structural_only`, disclose it. The Chart.js and
Paged.js wrappers may still use installed Chrome or Edge even when the shared
renderer cannot find its preferred Chromium headless-shell executable.

Run the repository suite after changing the compiler, renderer adapters,
contract, skill, or examples:

```powershell
pwsh -NoProfile -File scripts\Test-Repository.ps1
```

## Safe revision behavior

When revising an existing report:

1. Start from the existing `report.report.md`, `report.data.json`, and full
   `artifact.json`.
2. Preserve unrelated IDs, section order, prose, data, and source metadata.
3. Change only the requested section and directly dependent datasets or
   references.
4. Recompile and rerender the complete report.
5. Compare the old and new artifact structure.
6. Reconcile affected values again.
7. Re-run report validation and rendered QA.

Never edit generated HTML to make a report-specific correction. Fix the source
Markdown, data, artifact, or shared renderer boundary and regenerate.

## Intentional constraints

Report Markdown v0.1 intentionally has no:

- Arbitrary HTML, JavaScript, or CSS
- MDX or executable Markdown
- Themes or per-report styling
- Columns or dashboard layouts
- Nested directives
- Component plug-ins
- Raw Chart.js options
- Arbitrary colors, axes, legends, or chart annotations
- Multi-series charts
- Conditional blocks, loops, variables, or formulas
- In-DSL joins, aggregations, or transformations

These constraints keep reports predictable, auditable, printable, and safe.

## Known implementation gaps

These gaps may matter for complicated reports.

### 1. DSL chart coverage is narrower than the artifact and print adapter

The DSL supports only `bar` and `pie`. Direct artifact authoring and the
Chart.js print adapter also understand initial `line` and `scatter` forms.

Likely extension: add constrained line and scatter directives with explicit
minimum data-density rules, fixtures, compiler validation, and print QA.

### 2. No multi-series, grouped, stacked, waterfall, distribution, or matrix visuals

Complex operational reports may need plan versus actual, composition over time,
drivers, distributions, or cohort matrices.

Current response: precompute a simpler decision-relevant view, use multiple
single-question charts, use a table, or author the canonical artifact directly
when it already supports the required form.

Likely extension: add only repeated chart patterns demonstrated by several real
reports. Do not expose raw Chart.js configuration.

### 3. File and document provenance is stricter for widgets than for narrative

The portable validator currently requires runnable SQL or a `.sql` source path
for cards, charts, and tables. Narrative blocks may cite ordinary files or
documents directly.

Likely fix: make file/document/reproducible-transformation provenance a
first-class widget source without requiring an SQL-shaped bridge.

### 4. No formal JSON Schema or compatibility policy

The artifact is validated by executable code, but there is no versioned public
JSON Schema defining compatibility and migrations.

Likely fix: publish a schema, add schema fixtures, define versioning rules, and
test backward-compatible artifact migrations.

### 5. Renderer dependency is discovered from the installed plugin cache

The repository does not yet pin the interactive renderer as an ordinary
versioned dependency. Reproduction can depend on the locally installed Data
Analytics plugin version.

Likely fix: package or version the renderer contract independently, or add an
explicit compatibility lock and CI matrix.

### 6. Bundle command does not expose print orientation or page size

`build_print_report.py` supports page size and portrait/landscape orientation,
but `build_report_bundle.py` currently uses the default Letter landscape
settings.

Likely fix: forward `--page-size` and `--orientation` through the bundle command
and record them in build metadata.

### 7. DSL has no deliberate page-break or keep-together controls

Paged.js supports page breaks and the print CSS has safe component rules, but
Report Markdown deliberately does not expose layout classes.

Current response: rely on the editorial pagination baseline, split overly large
sections, and use individual stages for page orientation.

Likely extension: add a very small semantic print-break directive only after
repeated reports prove that content structure alone is insufficient.

### 8. Long audit appendices exceed the standard table contract

Tables are capped at 50 rows and eight columns. This is appropriate for the
reader-facing report but not for every audit population.

Current response: show the decision-relevant exceptions in the report and
deliver the full reviewed CSV, workbook, or separate audit attachment.

Likely extension: add a bounded appendix/attachment contract rather than making
the primary report an unbounded data browser.

### 9. No reusable report templates beyond fixed opening profiles

The four document profiles change only the first-section vocabulary. There is
no reusable section schema for recurring reconciliation, status, incident,
monthly close, or customer-review reports.

Likely extension: introduce optional scaffolding templates that generate normal
Report Markdown. Templates should not add hidden renderer behavior.

### 10. No table-of-contents, footnote, cross-reference, or section-numbering system

Long technical and regulatory reports may need stable figure/table references,
footnotes, or a generated contents page.

Likely extension: add compiler-owned references and deterministic numbering,
then validate links in interactive and paginated output.

### 11. Mobile behavior remains renderer-owned and version-dependent

The baseline previously documented overflow at 390 pixels. Some later reports
pass narrow-width smoke testing, so mobile behavior must still be checked per
report and should not be assumed from desktop success.

Likely fix: resolve responsive defects in the shared renderer and add stable
desktop/narrow browser verification to CI.

### 12. Browser verification can be structurally complete without being visually complete

The portable renderer may report `structural_only` when its preferred Chromium
headless-shell is unavailable, even though installed Chrome can be used by the
print stages.

Current response: preserve semantic chart tables, run independent installed
Chrome QA when appropriate, and disclose the limitation.

Likely fix: align browser discovery across the shared renderer, Chart.js, and
Paged.js wrappers.

### 13. No built-in source ingestion or analytical transformation language

The reporting system consumes reviewed datasets; it does not crawl documents,
query databases, interpret arbitrary spreadsheets, or perform business logic
inside the DSL.

Current response: use focused analysis, extraction, SQL, notebook, or
data-quality workflows first. Save their reviewed outputs and transformations
beside the report.

### 14. No public license has been selected

The package should not be treated as publicly redistributable until licensing
is decided.

## Extension decision rule

When a complicated report does not fit, classify the requirement:

1. **Data-shaping problem** — solve it before authoring and save the
   transformation.
2. **Narrative-structure problem** — use additional Markdown sections.
3. **Standard evidence problem** — use an existing metric, chart, table, or
   figure directive.
4. **Advanced artifact problem** — author `artifact.json` directly while
   preserving sources and validation.
5. **Repeated language gap** — propose a constrained DSL extension with:
   - at least two or three real motivating examples
   - syntax and hard limits
   - artifact mapping
   - compiler errors
   - fixture coverage
   - interactive and print behavior
   - accessibility behavior
   - provenance rules
   - migration and documentation updates
6. **Renderer problem** — fix the shared renderer or print adapter, not an
   individual generated HTML file.

Keep this invariant:

```text
report.report.md + report.data.json
  -> artifact.json
  -> shared interactive and print renderers
```

## Agent completion contract

The agent is finished only when it can hand off:

- The primary interactive `report.html`
- `report.report.md`
- `report.data.json`
- Canonical `artifact.json`
- `source_notes.md`
- Relevant queries, reviewed data, and images
- Paginated HTML and PDF when requested
- Validation result
- Browser or structural-verification status
- Known limitations that affect interpretation

The handoff should lead with the actual report artifact, not a chat summary.

## Authoritative repository references

- `skill/create-auditable-reports/SKILL.md`
- `skill/create-auditable-reports/references/report-workflow.md`
- `skill/create-auditable-reports/references/report-markdown.md`
- `skill/create-auditable-reports/references/artifact-authoring.md`
- `skill/create-auditable-reports/references/chartjs-visuals.md`
- `skill/create-auditable-reports/references/quality-checklist.md`
- `docs/BASELINE.md`
- `docs/AUTHORING-DIRECTION.md`
- `docs/decisions/`
