# 0008: Separate canonical evidence from stakeholder editions

## Status

Accepted

## Context

The original pipeline treated every document as an analytical report whose visible content and audit record were effectively the same selection. A stakeholder decision brief proved that model too narrow. Sources may need to remain internal, charts may be inappropriate, and the edition may show only a few decisions even though the durable record must retain requirements, conflicts, assumptions, recommendations, sources, and provenance.

Print behavior also depended on manual CSS and stage-by-stage commands. That exposed page-orientation bugs, collapsed table columns, locked-file failures, and output that was difficult to inspect at page level.

## Decision

The authoring model has two explicit layers:

1. `evidence-package.json` is the canonical evidence package. It retains versioned collections, datasets, sources, and provenance.
2. `.report.md` is an edition manifest expressed through constrained Markdown, front matter, and standard directives.

The compiler embeds the complete evidence package in `artifact.json` while exposing scalar evidence rows as bounded widget datasets. Edition choices such as hidden sources or an omitted chart never remove canonical evidence.

The `decision-brief` profile requires Executive Summary followed immediately by Immediate Direction. It defaults to Letter portrait, hidden sources, and date-only output, and it does not require a chart.

Print settings are safe configuration, not author CSS. Named page sizes compile to explicit width and height. Semantic table roles compile to proportional widths and are measured after pagination. The bundle command forwards print overrides, always creates paginated HTML, validates PDF `MediaBox` values, and replaces final output atomically. A locked PDF produces a timestamped fallback rather than losing the new build.

## Consequences

- Authors can maintain one complete evidence record and produce multiple stakeholder editions.
- Decision briefs can remain compact and chartless without bypassing the normal artifact pipeline.
- Generated CSS and HTML remain build products; ordinary authors edit Markdown, JSON evidence, and safe settings only.
- The installed Data Analytics renderer still validates report artifacts as chart-bearing. The local adapter adds a temporary compatibility chart only during packaging, then removes it and restores the canonical chartless payload. This boundary should be deleted if the upstream renderer accepts chartless reports.
- Page-level checks now fail on orientation mismatch, table overflow, unreadable semantic columns, nearly blank intermediate pages, source/date policy violations, and chart-edition mismatches. Stranded headings and split short numbered lists are surfaced as warnings for review.
