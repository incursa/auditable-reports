# ADR 0004: Adopt constrained Report Markdown

- Status: accepted
- Date: 2026-07-21

## Context

The canonical artifact is auditable and renderer-friendly but too verbose for routine report authoring. Authors need familiar prose, code blocks, a few bounded visuals, tables, and screenshots. They do not need a general web-component system or access to page-level styling.

## Decision

Adopt `.report.md` as a deterministic source language that compiles to the existing `artifact.json` contract.

Ordinary Markdown owns narrative structure and fenced code. Flat front matter owns report metadata and points to one JSON sidecar containing reviewed datasets and sources. Four fenced directives place `metrics`, `chart`, `table`, and `figure` blocks. Version 0.1 supports bounded bar, line, pie, and scatter charts.

Enforce fixed limits in the compiler: six metrics, twelve bars, six pie slices, eight table columns, fifty table rows, two hundred rows per artifact dataset, and five megabytes per embedded figure. Reject arbitrary HTML, JavaScript, CSS, chart options, and unsafe file paths.

The compiled artifact remains reviewable and is still the only input to the interactive renderer, Chart.js materializer, and Paged.js paginator.

## Consequences

- Routine report authors write Markdown instead of HTML or the full artifact schema.
- Data and provenance remain explicit in a sidecar rather than being hidden in prose.
- A small vocabulary keeps rendering and printing predictable.
- The compiler can fail early on misleading pies, overly wide tables, missing fields, unknown sources, and unsafe images.
- Expanding the language requires a demonstrated repeated need and a compiler/fixture update.
