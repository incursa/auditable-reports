# Chart.js print visuals

Use Chart.js only as a build-time adapter for selected report visuals. The canonical `artifact.json` remains the source of chart type, dataset, row bound, source, and encodings. Do not add Chart.js-only data or executable configuration to the report artifact.

## Supported initial forms

- `bar`: comparisons, rankings, and signed variance across categories
- `line`: trends with a meaningful ordered x-axis and enough observed periods
- `pie`: part-to-whole views with 2–6 positive, mutually exclusive slices
- `scatter`: relationships between same-grain quantitative observations

Use a table or narrative when these forms do not fit. Unsupported types should fail during materialization rather than be approximated.

## Rendering rules

- Run `render_chartjs_output.py` only after `build_print_report.py`.
- Keep animations and browser events disabled.
- Use fixed canvas dimensions and an explicit device pixel ratio for capture.
- Block all remote requests; package assets locally through the pinned dependency.
- Export the canvas to an embedded PNG and remove every script and canvas from the output.
- Give the image a concise text alternative naming the relationship shown.
- Preserve the adjacent semantic table with exact values and the original `sourceId` path through the artifact.
- Use neutral color unless the artifact and nearby narrative define directional meaning.
- Treat the chart as explanatory evidence, not a substitute for the adjacent finding.

`report_charted.html` is a generated intermediate. Do not edit it by hand. Revise the artifact or renderer and regenerate it.
