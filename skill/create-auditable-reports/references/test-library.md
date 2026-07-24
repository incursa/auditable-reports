# Synthetic test library

Use these fixtures to exercise the standard authoring blocks without bringing customer, email, ClickUp, or other personal content into the repository.

| Fixture | Profile | Primary coverage |
| --- | --- | --- |
| `sunday-school-lesson` | lesson | teaching outline, blockquote, metrics, pie chart, activity table, illustration |
| `project-status-report` | report | executive prose, signed bar chart, pie chart, eight-column table, dashboard-style figure |
| `weekly-journal` | journal | reflective prose, lists, code-style template, daily bar chart, time-allocation pie, journal illustration |
| `incident-review` | technical | technical narrative, log/code block, timeline table, incident bar chart, architecture figure |
| `decision-brief` | decision-brief | canonical evidence vs stakeholder edition, portrait print, hidden sources, date-only output, no charts, semantic decision/incompatibility tables, long text |

Every claim and image is synthetic. The fixtures are for rendering, pagination, and authoring tests only.

Build the complete library from the repository root:

```powershell
py skill\create-auditable-reports\scripts\build_test_library.py `
  --output-dir .work\test-library
```

Each output directory contains the compiled artifact, interactive HTML, script-free print source, Paged.js preview, and PDF. Chart.js materialization appears only when the fixture includes charts. The test suite also simulates a locked final PDF and verifies the named fallback behavior.
