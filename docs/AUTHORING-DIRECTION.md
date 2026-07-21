# Authoring direction

The long-term goal is to let a report author write mostly Markdown while retaining structured visuals, datasets, validation, and source traceability.

## Recommended model

Use a declarative `.report.md` source that compiles to `artifact.json`. Keep datasets, source metadata, and reusable queries in adjacent files.

```text
quarterly-health/
  report.report.md
  report.yaml             optional structured definitions too large for front matter
  sources.yaml
  queries/
  data/
  artifact.json           generated and reviewable
  report.html             generated
  report_print.html       script-free pagination source, generated when requested
  report_charted.html     embedded Chart.js visuals, generated when charts are present
  report_paged.html       Paged.js preview, generated when requested
  report.pdf              Paged.js PDF, generated when requested
```

Markdown should own prose and reading order. Declarative directives should place metric strips, charts, tables, caveats, and source references. YAML should own structured definitions that are awkward or error-prone in prose. Arbitrary JavaScript and arbitrary embedded HTML should not be part of the authoring language.

An illustrative shape, not accepted syntax:

```markdown
---
title: Quarterly Delivery Health
audience: product stakeholders
cutoff: 2026-06-30
status: ready
---

# Executive Summary

The portfolio is within the approved tolerance. [@portfolio-snapshot]

::: metric-strip
cards: [active-projects, forecast-variance, at-risk-projects]
:::

## Three projects explain most of the variance

The exception is concentrated rather than portfolio-wide. [@portfolio-snapshot]

::: chart
id: variance-by-project
:::
```

The compiler would resolve the directives and citations against structured definitions, enforce the evidence rules, and emit the existing canonical artifact. The interactive renderer would remain unchanged. When print output is requested, selected artifact charts would be materialized by Chart.js before the generated source passes through Paged.js for paginated preview or PDF.

## Why not plain Markdown or MDX

Plain Markdown cannot safely express chart encodings, metric definitions, reviewed datasets, or exact source bindings without conventions layered on top. MDX can express them, but executable components weaken reproducibility and make security review harder. A small declarative extension keeps authoring approachable and output deterministic.

## Sequencing

1. Use the current artifact workflow on several real reports and revise the visual baseline based on actual reader feedback.
2. Formalize the accepted artifact contract as a versioned JSON Schema and add semantic validation for block references, datasets, source bindings, and safe paths.
3. Collect repeated artifact-authoring patterns from those reports.
4. Specify the smallest `.report.md` directive set that covers those patterns.
5. Build a deterministic compiler from `.report.md` plus adjacent YAML/data to `artifact.json`.
6. Add golden tests proving that source, artifact, and rendered outputs remain reproducible.

Do not implement syntax before steps 1 through 3 produce evidence about what authors actually repeat.
