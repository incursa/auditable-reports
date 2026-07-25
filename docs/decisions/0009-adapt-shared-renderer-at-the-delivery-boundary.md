# 0009: Adapt the shared renderer at the delivery boundary

## Status

Accepted

## Context

The installed Data Analytics portable reader sizes its sticky top bar with
`100vw`. On Windows, Chromium reserves 15 pixels for the vertical scrollbar,
so the 1,440-pixel bar is wider than the 1,425-pixel document viewport. The
renderer verifier correctly reports eight pixels of document-level horizontal
overflow after rounding. The default five-second reader startup budget can
also expire while Chromium materializes static charts.

## Decision

Keep the Data Analytics package as the renderer owner. Invoke its exported
delivery and build functions through a repository-local adapter that:

- adds marked desktop and mobile CSS rules for `.analytics-top-bar`, sizing it
  to each padded parent instead of the scrollbar-inclusive viewport;
- uses explicit 30-second reader, 5-second action, and 60-second verification
  budgets; and
- leaves the canonical artifact and embedded payload unchanged.

The existing chartless-report adapter remains separate and continues to remove
its temporary chart before publication.

## Consequences

- Portable HTML passes the shared desktop and mobile browser verifier on
  Windows without maintaining a fork of the reader runtime.
- The compatibility rule is easy to locate and delete after the upstream
  reader stops using scrollbar-inclusive sizing.
- Browser verification is still mandatory; the longer budgets do not turn a
  verifier failure into a warning.
