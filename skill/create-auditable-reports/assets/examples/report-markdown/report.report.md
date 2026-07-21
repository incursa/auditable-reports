---
description: A synthetic example of the constrained Markdown authoring format and its standard report blocks.
generated-at: 2026-07-21T21:00:00Z
status: fixture
data: report.data.json
---
# Simple Delivery Review

## Executive Summary

<!-- source: delivery_snapshot -->

- **The six-project portfolio is forecast $320K over budget.** Two projects account for most of the unfavorable variance.
- **The work remains concentrated in the Central region.** That region holds 39% of approved budget.
- **Keep the report simple.** A short narrative, bounded charts, exact table, reproducible code, and one screenshot are sufficient for this review.

::: metrics
id: headline_metrics
dataset: headline
source: delivery_snapshot
metric: project_count | Active projects | number | Projects in the reviewed scope.
metric: approved_budget | Approved budget | currency | Approved budget across the portfolio.
metric: forecast_variance | Forecast variance | currency | Forecast less approved budget. | signed
metric: at_risk_count | At-risk projects | number | Projects requiring management attention.
:::

## Variance is concentrated in two projects

<!-- source: delivery_snapshot -->

Atlas and Cedar contribute $430K of unfavorable variance, partly offset by favorable forecasts elsewhere.

::: chart
id: variance_by_project
type: bar
title: Forecast variance by project
subtitle: Current forecast less approved budget; synthetic snapshot
dataset: projects
source: delivery_snapshot
category: project
value: variance
category-label: Project
value-label: Forecast less budget
format: currency
:::

## Central holds the largest budget share

<!-- source: delivery_snapshot -->

The pie is intentionally limited to four positive, mutually exclusive regional totals.

::: chart
id: budget_by_region
type: pie
title: Approved budget by region
subtitle: Four mutually exclusive regions; synthetic snapshot
dataset: regions
source: delivery_snapshot
category: region
value: budget
category-label: Region
value-label: Approved budget
format: currency
:::

## Project detail remains available for exact lookup

::: table
id: project_detail
title: Project budget and forecast detail
subtitle: Six synthetic active projects
dataset: projects
source: delivery_snapshot
column: project | Project | text
column: owner | Owner | text
column: region | Region | text
column: risk | Risk | text
column: completion | Completion | percent
column: budget | Budget | currency
column: forecast | Forecast | currency
column: variance | Variance | currency | movement
sort: variance | desc
:::

## Reproducible method

The report can include ordinary fenced code without an HTML component:

```sql
SELECT
  project,
  forecast - budget AS variance
FROM reviewed_projects
ORDER BY variance DESC;
```

## Supporting screenshot

Use a figure directive rather than raw HTML or Markdown image syntax so the file is validated and embedded.

::: figure
id: review_state
path: review-state.svg
alt: Synthetic review screen with six projects loaded and the report marked ready.
caption: Synthetic workflow capture demonstrating the standard figure treatment.
source: workflow_capture
:::

## Caveats and assumptions

This fixture contains invented values and an illustrative interface image. It demonstrates authoring and rendering behavior only and must not be used for an operational decision.
