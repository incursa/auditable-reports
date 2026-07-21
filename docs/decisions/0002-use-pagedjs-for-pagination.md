# 0002: Use Paged.js for preview and PDF pagination

- Status: accepted
- Date: 2026-07-21

## Context

The original package produced a script-free print HTML file with basic `@page` sizing. Reliable running headers, page numbers, controlled breaks, paginated preview, and repeatable PDF creation require a dedicated CSS Paged Media implementation.

## Decision

Use Paged.js 0.4.3 as the pinned pagination engine.

Keep `report_print.html` as a script-free, self-contained pagination source. Put page size, margins, running title, page counters, and break rules in its CSS. Use `render_paged_output.py`, Paged.js, and the repository's pinned browser-control dependency to produce `report_paged.html` or `report.pdf`.

Block remote requests by default. Do not add Paged.js to the interactive report, and do not treat paginated DOM or PDF as canonical report source.

Normalize run-specific Paged.js DOM identifiers out of saved paginated HTML. Treat PDF reproducibility as structural and visual rather than byte-for-byte because browser PDF metadata may vary by run.

## Consequences

- Browser preview and PDF use the same CSS pagination model.
- The print source remains inspectable without JavaScript.
- Paged.js and the browser-control dependency are pinned in the repository package lock.
- A local Chrome-compatible browser is required; the wrapper discovers Chrome or Edge on Windows.
- Paged.js output must be regenerated when the print source changes.
