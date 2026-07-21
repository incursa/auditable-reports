# ADR 0003: Use Chart.js for static chart materialization

- Status: accepted
- Date: 2026-07-21

## Context

The canonical artifact already defines chart types, datasets, source bindings, row limits, and x/y encodings. The shared Data Analytics renderer uses those definitions for the interactive report, but the script-free print source can contain only the semantic data table when browser chart verification is unavailable. Paged.js paginates HTML; it does not turn data into charts.

Chart.js is a mature canvas charting library, but canvas has two relevant constraints: it needs an explicit accessible alternative, and responsive canvas sizing requires special handling when printing. Directly leaving a live canvas in the Paged.js input would also make the handoff dependent on runtime JavaScript.

## Decision

Pin Chart.js 4.5.1 as a build-time visualization adapter for selected `bar`, `line`, and `scatter` charts. `render_chartjs_output.py` reads `artifact.json` and `report_print.html`, renders each chart in a local controlled browser with fixed dimensions and animations disabled, converts it to an embedded PNG, and writes script-free `report_charted.html`.

The embedded image is placed immediately before the existing semantic chart table. It receives a text alternative that names the chart and points readers to the table for exact values. Remote requests are always blocked. Paged.js receives `report_charted.html`, not a live Chart.js canvas.

The shared Data Analytics renderer remains the owner of `report.html`. Chart.js does not define a second artifact format, interpret sources, or replace the semantic table.

## Consequences

- Print and PDF editions now contain a visible chart without requiring client-side JavaScript.
- The canonical artifact remains the only chart-data contract.
- The exact-value table continues to support audit review and non-visual access.
- Reproduction requires Node.js, the pinned npm packages, and installed Chrome or Edge.
- Raster output is deterministic within the validated browser/font environment; byte identity is not promised across different operating systems or browser/font versions.
- Unsupported chart types fail explicitly instead of silently degrading.

## References

- [Chart.js documentation](https://www.chartjs.org/docs/latest/)
- [Responsive charts and printing](https://www.chartjs.org/docs/latest/configuration/responsive.html)
- [Canvas accessibility](https://www.chartjs.org/docs/latest/general/accessibility.html)
- [Animation configuration](https://www.chartjs.org/docs/latest/configuration/animations.html)
