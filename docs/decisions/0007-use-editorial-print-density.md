# ADR 0007: Use editorial print density

- Status: accepted
- Date: 2026-07-21

## Context

The initial print rules favored large atomic blocks. Whole Markdown sections, visual cards, chart images, figures, and source lists were commonly moved as units. The output was safe but several ordinary fixtures left half a page unused or created a nearly empty sources-only final page.

## Decision

Use a compact editorial rhythm while preserving legibility. Keep 9.5-point body text and standard page width. Reduce vertical spacing modestly, render Chart.js captures at 1280 by 360 pixels, cap print figures and charts near 3.2 inches high, and use slightly smaller metric cards.

Keep headings with their first content and avoid redundant heading-only prose blocks in authored sources when a following chart or table already has a sufficient title. Group each chart heading with its static image, keep metric cards and embedded figures atomic, and keep table rows intact. Allow Markdown sections and visual cards to split at safe internal boundaries. Remove the unconditional page break before Sources; keep each source entry together and use a compact two-column source list so short provenance sections occupy remaining final-page space when they fit.

## Consequences

- Typical reports use fewer pages and less unintentional whitespace without reducing body text to fine print.
- Charts, figures, exact-value tables, and provenance remain present and readable.
- Long source lists may still move to a new page when required.
- Density remains a renderer concern; the DSL does not gain spacing, chart-size, or page-break options.
