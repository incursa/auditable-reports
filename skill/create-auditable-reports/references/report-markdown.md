# Report Markdown v0.1

Use `.report.md` for ordinary prose and a small set of fenced report directives. Compile it to the canonical `artifact.json`; never render the DSL directly.

## Document shape

Begin with flat front matter and one level-one title:

```markdown
---
description: One-sentence report scope.
generated-at: 2026-07-21T21:00:00Z
status: ready
data: report.data.json
---
# Quarterly Delivery Health
```

The four front-matter properties are required. `status` is `ready`, `partial`, `blocked`, or `fixture`. The data path must be relative to the Markdown file.

The JSON sidecar contains exactly `datasets` and `sources`:

```json
{
  "datasets": {
    "projects": [
      {"project": "Atlas", "variance": 280000}
    ]
  },
  "sources": [
    {
      "id": "project_snapshot",
      "label": "Reviewed project snapshot",
      "path": "projects.csv"
    }
  ]
}
```

Keep datasets reviewed and bounded. The compiler allows at most 200 rows in any artifact dataset.

## Ordinary Markdown

Use headings, paragraphs, bold/emphasis, links, lists, blockquotes, horizontal rules, inline code, and triple-backtick code fences normally. The compiler creates one artifact Markdown block per `##` section.

Attach one source to a quantitative prose section with an HTML comment anywhere in that section:

```markdown
## Three projects explain the gap

<!-- source: project_snapshot -->

Atlas and Cedar account for most of the current variance.
```

Do not use Markdown image syntax. Use the `figure` directive so the compiler can validate and embed the image.

## Metric strip

```markdown
::: metrics
id: headline_metrics
dataset: headline
source: project_snapshot
metric: active_projects | Active projects | number | Projects in the reviewed scope.
metric: forecast_variance | Forecast variance | currency | Forecast less approved budget. | signed
:::
```

Use 1–6 metrics. Each `metric` line is `field | label | format | optional description | optional signed`. Formats are `number`, `currency`, or `percent`.

## Bar chart

```markdown
::: chart
id: variance_by_project
type: bar
title: Forecast variance by project
subtitle: Current forecast less approved budget
dataset: projects
source: project_snapshot
category: project
value: variance
category-label: Project
value-label: Forecast less budget
format: currency
:::
```

Bar charts accept 2–12 prepared rows. The compiler supplies the layout and styling; authors cannot set colors, axes, legends, or arbitrary Chart.js options.

## Pie chart

```markdown
::: chart
id: budget_by_region
type: pie
title: Approved budget by region
dataset: regions
source: project_snapshot
category: region
value: budget
format: currency
:::
```

Pie charts accept 2–6 unique categories with positive values. Pre-aggregate small categories into `Other` before compiling. Do not use pie charts for signed values or comparisons where bar length is clearer.

## Table

```markdown
::: table
id: project_detail
title: Project detail
subtitle: Current reviewed snapshot
dataset: projects
source: project_snapshot
column: project | Project | text
column: owner | Owner | text
column: completion | Completion | percent
column: variance | Variance | currency | movement
sort: variance | desc
:::
```

Tables accept 1–8 columns and datasets of at most 50 rows. Column formats are `text`, `date`, `number`, `currency`, or `percent`. `movement` is the only optional visual semantic. `sort` is optional.

## Figure or screenshot

```markdown
::: figure
id: workflow_screenshot
path: images/workflow.png
alt: Workflow screen showing the approved review state.
caption: Review state after the July close.
source: workflow_capture
:::
```

Figures accept relative PNG, JPEG, WebP, GIF, or SVG files up to 5 MB. `alt` is required; `caption` and `source` are optional. The compiler embeds the file as a data URI for a self-contained report and escapes all supplied text.

## Deliberate exclusions

Version 0.1 has no columns, arbitrary HTML, JavaScript, CSS, chart themes, multi-series charts, nested directives, dashboards, or component plug-ins. Revise the compiler only after repeated reports demonstrate a missing standard block.
