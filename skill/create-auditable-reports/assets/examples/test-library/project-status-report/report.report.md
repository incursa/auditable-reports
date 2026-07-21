---
document-type: report
description: A fictional project portfolio status report with bounded management visuals and audit detail.
generated-at: 2026-07-21T22:10:00Z
status: fixture
data: report.data.json
---
# Northwind Modernization: July Portfolio Review

## Executive Summary

<!-- source: portfolio_snapshot -->

- **The six-workstream portfolio is forecast $150K over its $7.6M plan.** Field Enablement and Data Migration account for the largest unfavorable movements.
- **Four workstreams remain on track.** Two are classified at risk, with recovery actions assigned and dated.
- **The next decision is narrow.** Hold the $90K contingency reserve until the Data Migration rehearsal completes on August 2.

::: metrics
id: portfolio_headline
dataset: headline
source: portfolio_snapshot
metric: approved_budget | Approved budget | currency | Approved budget across six synthetic workstreams.
metric: forecast_variance | Forecast variance | currency | Current estimate less approved budget. | signed
metric: at_risk | At-risk workstreams | number | Workstreams requiring active recovery.
metric: completion | Overall completion | percent | Weighted completion across the fictional portfolio.
:::

## Two workstreams account for the forecast pressure

<!-- source: portfolio_snapshot -->

Field Enablement and Data Migration together contribute $290K of unfavorable variance. Favorable forecasts in Infrastructure and Integration offset $140K of that pressure.

::: chart
id: variance_by_workstream
type: bar
title: Forecast variance by workstream
subtitle: Positive values are unfavorable; synthetic dollars
dataset: workstreams
source: portfolio_snapshot
category: workstream
value: variance
category-label: Workstream
value-label: Forecast variance
format: currency
:::

## Delivery effort is spread across four areas

The allocation view is intentionally limited to four mutually exclusive categories.

::: chart
id: budget_allocation
type: pie
title: Approved budget allocation
subtitle: Synthetic portfolio plan by delivery area
dataset: delivery_areas
source: portfolio_snapshot
category: area
value: budget
category-label: Delivery area
value-label: Approved budget
format: currency
:::

## Workstream detail

::: table
id: portfolio_table
title: Portfolio workstream status
subtitle: Current fictional review snapshot
dataset: workstreams
source: portfolio_snapshot
column: workstream | Workstream | text
column: owner | Owner | text
column: status | Status | text
column: completion | Complete | percent
column: budget | Budget | currency
column: forecast | Forecast | currency
column: variance | Variance | currency | movement
column: next_gate | Next gate | date
sort: variance | desc
:::

## Management view

::: figure
id: portfolio_board
path: portfolio-board.svg
alt: A synthetic portfolio board with six workstream cards, two amber risk indicators, and a milestone timeline.
caption: Illustrative management-board capture used to test a wide figure in print.
source: portfolio_illustration
:::

## Decisions and follow-up

1. Keep the contingency reserve unallocated through the migration rehearsal.
2. Review training attendance daily during the first rollout week.
3. Require written exit criteria before the integration performance gate.

This entire portfolio, including names, dates, values, status, and image, is fictional test data.
