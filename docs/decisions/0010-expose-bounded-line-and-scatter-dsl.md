# Decision 0010: Expose Bounded Line and Scatter Charts in Report Markdown

## Context

The canonical artifact and pinned Chart.js print adapter already support line
and scatter charts, but Report Markdown exposed only bar and pie directives.
That forced otherwise ordinary trend and relationship reports into direct
artifact authoring, which made them less reproducible and harder to review.

## Decision

Expose `line` and `scatter` through the constrained chart directive:

- line charts accept 2–24 rows with unique x-axis values and one y series;
- scatter charts accept 2–50 rows and require numeric x and y fields;
- both retain the existing source binding, semantic data, and fixed renderer
  styling; authors still cannot provide arbitrary Chart.js options.

## Consequences

Trend and relationship reports can now use the same Markdown → artifact →
interactive/print pipeline as other standard reports. Multi-series, stacked,
waterfall, distribution, and matrix visuals remain intentionally out of scope.
The compiler, documentation, and unit tests must continue to enforce the
bounded forms.
