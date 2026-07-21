# Canonical artifact authoring

The shared renderer accepts one canonical JSON object. Keep report content in the artifact and never maintain a second hand-coded HTML layout.

## Top-level shape

```json
{
  "surface": "report",
  "manifest": {
    "version": 1,
    "surface": "report",
    "title": "Reader-facing title",
    "description": "One-sentence scope",
    "generatedAt": "2026-07-21T12:00:00Z",
    "cards": [],
    "charts": [],
    "tables": [],
    "sources": [],
    "blocks": []
  },
  "snapshot": {
    "version": 1,
    "generatedAt": "2026-07-21T12:00:00Z",
    "status": "ready",
    "datasets": {}
  },
  "sources": []
}
```

Use `ready`, `partial`, `blocked`, or `fixture` for snapshot status. Use `fixture` for synthetic examples.

## Ordered blocks

Blocks define the visible reading order:

```json
[
  {"id": "title", "type": "markdown", "body": "# Portfolio Health"},
  {"id": "executive_summary", "type": "markdown", "body": "## Executive Summary\n\n- **Answer first.** ..."},
  {"id": "headline_metrics", "type": "metric-strip", "cardIds": ["portfolio_count", "variance"]},
  {"id": "variance_finding", "type": "markdown", "body": "## Three projects drive the gap\n\n...", "sourceId": "portfolio_snapshot"},
  {"id": "variance_chart_block", "type": "chart", "chartId": "variance_chart"},
  {"id": "detail_block", "type": "table", "tableId": "project_detail"}
]
```

Use one peer report section per markdown block. Apply `sourceId` to a quantitative markdown block only when all quantitative claims in it come from that source.

## Metric cards

Each card has one headline metric and may include short comparison metrics tied to it:

```json
{
  "id": "forecast_variance",
  "description": "Current forecast less approved budget.",
  "dataset": "headline",
  "sourceId": "portfolio_snapshot",
  "metrics": [
    {"label": "Forecast variance", "field": "forecast_variance", "format": "currency", "signed": true}
  ]
}
```

Common formats include `number`, `percent`, and `currency`. Store percentages as decimal fractions when the renderer expects percent formatting.

## Charts

Define a chart against reviewed snapshot rows:

```json
{
  "id": "variance_chart",
  "title": "Forecast variance by project",
  "subtitle": "Current forecast less approved budget; synthetic example",
  "type": "bar",
  "dataset": "project_detail",
  "sourceId": "portfolio_snapshot",
  "intent": "comparison",
  "question": "Which projects drive the portfolio variance?",
  "rationale": "A category bar chart makes signed project differences comparable.",
  "encodings": {
    "x": {"field": "project", "type": "nominal", "label": "Project"},
    "y": {"field": "variance", "type": "quantitative", "format": "currency", "label": "Forecast less budget"},
    "tooltip": [
      {"field": "budget", "type": "quantitative", "format": "currency", "label": "Budget"},
      {"field": "forecast", "type": "quantitative", "format": "currency", "label": "Forecast"},
      {"field": "risk", "type": "text", "label": "Risk"}
    ]
  },
  "valueFormat": "currency",
  "layout": "full",
  "maxRows": 8
}
```

Keep chart datasets richer than only x and y when reviewed context is safe. Do not use a color/series encoding that duplicates the category axis.

## Tables

Tables are for exact lookup and audit detail:

```json
{
  "id": "project_detail",
  "title": "Project detail",
  "subtitle": "Current approved budget and forecast",
  "dataset": "project_detail",
  "sourceId": "portfolio_snapshot",
  "defaultSort": {"field": "variance", "direction": "desc"},
  "density": "spacious",
  "layout": "full",
  "columns": [
    {"field": "project", "label": "Project", "type": "text"},
    {"field": "budget", "label": "Budget", "format": "currency"},
    {"field": "forecast", "label": "Forecast", "format": "currency"},
    {"field": "variance", "label": "Variance", "format": "currency", "movement": true}
  ]
}
```

Use movement color only for truly directional fields with signed values.

## Sources

Add a compact source record to `manifest.sources` and the canonical record to top-level `sources`:

```json
{
  "id": "portfolio_snapshot",
  "label": "Synthetic project health snapshot",
  "path": "project_health.csv",
  "query": {
    "engine": "duckdb",
    "id": "project-health-example",
    "executed_at": "2026-07-21T12:00:00Z",
    "description": "Loads the reviewed project-level snapshot.",
    "sql": "SELECT * FROM read_csv_auto('project_health.csv', header = true)"
  }
}
```

Use relative, non-secret paths. Never include credentials, signed URLs, connection strings, or parent-traversing paths.
