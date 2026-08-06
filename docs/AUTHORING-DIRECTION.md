# Authoring direction

The default authoring source is now constrained `.report.md`. It compiles to the existing canonical artifact, so authoring convenience does not weaken data bounds, source traceability, validation, or renderer compatibility.

## Accepted model

```text
quarterly-health/
  report.report.md        prose, reading order, and standard directives
  report.data.json        reviewed bounded datasets and source records
  images/                 optional screenshots or figures
  output/
    artifact.json         generated and reviewable
    report.html           generated interactive report
    report_print.html     script-free pagination source
    report_charted.html   embedded Chart.js visuals when charts are present
    report_paged.html     Paged.js preview
    report.pdf            print handoff
```

Markdown owns headings, prose, lists, links, blockquotes, and fenced code. Four directives place metric strips, bar/line/pie/scatter charts, tables, and figures. The JSON sidecar owns prepared rows and canonical source metadata.

An optional `document-type` selects an opening profile: `report` uses `Executive Summary`, `technical` uses `Technical Summary`, `lesson` uses `Lesson Overview`, `journal` uses `Entry Summary`, and `decision-brief` uses `Executive Summary` followed by `Immediate Direction`. The decision-brief profile also owns safe stakeholder-edition defaults; all profiles share the same renderer and constrained blocks.

Routine analytical reports use `report.data.json`. Decision briefs and other multi-edition documents use `evidence-package.json` so the canonical requirements, conflicts, decisions, assumptions, recommendations, sources, and provenance remain independent of visible edition choices.

The complete v0.1 syntax and limits are in `skill/create-auditable-reports/references/report-markdown.md`.

## Design boundary

The language is a report outline, not a web framework. It has no arbitrary HTML, JavaScript, CSS, columns, dashboards, themes, component plug-ins, or raw Chart.js configuration. Authors choose the evidence and reading order; the compiler and renderers choose the safe layout.

Hard limits are part of the language: six metrics, twelve bar items, twenty-four line points, fifty scatter points, six pie slices, eight table columns, fifty table rows, and five megabytes per embedded figure. Reports that exceed them should pre-aggregate, split a table, or use a separate audit attachment.

## Evolution rule

Add a directive or option only after multiple real reports show the same missing pattern. Preserve the compilation boundary:

```text
report.report.md + report.data.json -> artifact.json -> renderers
```

Do not add executable MDX or make generated HTML an authoring source.
