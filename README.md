# Auditable Reports

This repository is the source home for Incursa's reusable analytical-report baseline. It contains the `create-auditable-reports` agent skill, a constrained Markdown authoring language, deterministic build utilities, and synthetic golden examples.

The core design decision is simple:

```text
       report.report.md
        + report.data.json
           |
           v
     artifact.json          canonical, auditable intermediate representation
           |
           v
 shared Data Analytics renderer
           |
           +--> report.html
           +--> report_print.html (optional, script-free pagination source)
                        |
                        v
                 Chart.js 4.5.1
                        |
                        v
                 report_charted.html (embedded static charts)
                        |
                        v
                 Paged.js 0.4.3
                        |
                        +--> report_paged.html
                        +--> report.pdf
```

Generated HTML is an output, not an authoring format. Routine reports should start from `.report.md`; its compiler produces the same reviewable `artifact.json` used by advanced authors and every downstream renderer.

## Why this is a separate repository

This package owns an artifact contract, executable tooling, fixtures, validation, and an installable agent skill. It therefore does not belong in `incursa-docs`, which publishes documentation owned by other source repositories. A focused repo also lets the authoring syntax, schema, renderer adapter, and tests evolve together without coupling them to a product codebase.

## Repository layout

- `skill/create-auditable-reports/` — self-contained agent skill imported from the source archive.
- `docs/BASELINE.md` — the report content, visual, evidence, and output baseline.
- `docs/AUTHORING-DIRECTION.md` — accepted `.report.md` authoring model and boundaries.
- `docs/INTAKE.md` — archive provenance, inventory, validation evidence, and identified gaps.
- `docs/decisions/` — durable architectural decisions.
- `scripts/Test-Repository.ps1` — local repository validation.
- `package.json` and `package-lock.json` — pinned Chart.js visualization and Paged.js browser-pagination tooling.

## Quick start

Create a synthetic Markdown working directory:

```powershell
py skill\create-auditable-reports\scripts\new_report.py `
  --name "Quarterly Delivery Health" `
  --output .work\quarterly-delivery-health
```

Install the pinned browser tooling once, replace every synthetic value and source record, then render:

```powershell
npm install
```

```powershell
py skill\create-auditable-reports\scripts\build_report_bundle.py `
  --input .work\quarterly-delivery-health\report.report.md `
  --output-dir .work\quarterly-delivery-health\output
```

This one command compiles the Markdown, renders interactive HTML, embeds Chart.js visuals, paginates with Paged.js, and creates a PDF. Read [Report Markdown v0.1](skill/create-auditable-reports/references/report-markdown.md) for the four directives and fixed limits.

Build the four synthetic lesson, project-report, journal, and incident-review fixtures together:

```powershell
py skill\create-auditable-reports\scripts\build_test_library.py `
  --output-dir .work\test-library
```

The fixture catalog and feature coverage are documented in [Synthetic test library](skill/create-auditable-reports/references/test-library.md). None of the examples contain personal, customer, email, or ClickUp content.

For direct artifact work or individual stages, use `compile_report.py`, `render_report.py`, `build_print_report.py`, `render_chartjs_output.py`, and `render_paged_output.py` separately.

Validate the repository and shipped example:

```powershell
pwsh -File scripts\Test-Repository.ps1
```

Read `skill/create-auditable-reports/SKILL.md` before producing a real report.

To run the individual print stages instead, create the script-free source and paginate it:

```powershell
py skill\create-auditable-reports\scripts\build_print_report.py `
  --input .work\quarterly-delivery-health\report.html `
  --output .work\quarterly-delivery-health\report_print.html

py skill\create-auditable-reports\scripts\render_chartjs_output.py `
  --artifact .work\quarterly-delivery-health\artifact.json `
  --input .work\quarterly-delivery-health\report_print.html `
  --output .work\quarterly-delivery-health\report_charted.html

py skill\create-auditable-reports\scripts\render_paged_output.py `
  --input .work\quarterly-delivery-health\report_charted.html `
  --output .work\quarterly-delivery-health\report.pdf
```

The Chart.js stage supports the initial `bar`, `line`, `pie`, and `scatter` artifact forms and leaves the exact-value semantic table beside every embedded chart. If a report has no charts, pass `report_print.html` directly to Paged.js. The same pagination command creates a browser preview when the output ends in `.html`. Both browser-controlled stages use installed Chrome or Edge and block remote requests by default.

## Current boundaries

- The interactive renderer is supplied by the installed Data Analytics plugin; this repo intentionally does not fork that runtime.
- Chart.js 4.5.1 is the pinned build-time adapter for selected print visuals; it does not replace the interactive renderer, artifact, or semantic chart tables.
- Paged.js 0.4.3 is the pinned print-pagination engine; it does not replace the interactive renderer or canonical artifact.
- The project-health fixture is synthetic and must never be presented as operational evidence.
- The artifact contract is documented but does not yet have a versioned JSON Schema.
- Report Markdown v0.1 is intentionally constrained to ordinary Markdown plus metrics, bar/pie chart, table, and figure directives.
- No public license has been selected for this imported package.
