# Reusable report workflow

## 1. Frame the decision

Write a short report brief before querying data:

- Question the report must answer
- Audience and decision owner
- Time window and cutoff date
- Population, grain, and exclusions
- Control or comparison baseline
- Requested outputs
- Conditions for sign-off

If the user has not specified a technical audience, default to product/business stakeholders and lead with the answer.

## 2. Establish an evidence workspace

Use one directory per report:

```text
report-name/
  stakeholder-report.md    # or report.report.md
  evidence-package.json    # or report.data.json for a simple analytical report
  rebuild-report.ps1
  source_notes.md
  queries/
  data/
  analysis/
  output/
    artifact.json
    stakeholder-report.html
    stakeholder-report_print.html
    stakeholder-report_paged.html
    stakeholder-report.pdf
```

Keep raw inputs read-only. Save normalized or aggregated report datasets separately. Use deterministic file names and stable field names.

## 3. Bound and validate the data

For every source, capture:

- Exact file, table, view, workbook tab, or document
- Query or transformation used
- Query execution timestamp
- Requested cutoff and the field enforcing it
- Row grain and expected population
- Known limitations or historical-state gaps

Run control checks before interpretation:

- Row counts and distinct entity counts
- Null and duplicate keys
- Totals by scope
- Date minimum/maximum
- Reconciliation deltas
- Coverage and match rates
- Largest exceptions

Do not assume that an extract date equals an accounting cutoff. A current database can contain late-posted rows assigned to an earlier period; note that distinction when it matters.

## 4. Build the report spine

Plan the reading order before writing the edition:

1. Title
2. Executive or technical summary
3. Metric/cohort/control definitions
4. Headline metrics when useful
5. Evidence sections, each with claim, evidence, interpretation, and implication
6. Exact detail or exception table
7. Recommendations or monitoring actions
8. Open questions
9. Caveats and uncertainty

Every included chart needs an adjacent narrative block explaining the takeaway and why it matters. Charts are optional. Tables carry exact values; they do not replace interpretation.

For a decision brief, maintain two layers:

- Canonical evidence package: requirements, conflicts, decisions, assumptions, recommendations, datasets, sources, and provenance.
- Stakeholder edition: the selected narrative, tables, figures, and visibility settings.

Edition choices never delete canonical evidence.

## 5. Choose evidence forms

- Metric cards: a few distinct top-line values
- Bar chart: comparison, ranking, or signed variance across categories
- Line chart: a true trend with roughly 8–12 or more observed periods
- Stacked bar: part-to-whole with an explicit denominator
- Scatter: relationships with enough same-grain observations
- Table: audit detail, exact lookup, or exceptions
- Narrative: definitions, interpretation, uncertainty, and actions

Avoid charts when the dataset is too sparse to show a trustworthy pattern. Use a table, discrete-period bars, or concise prose instead.

## 6. Author and render

Run `scripts/new_report.py` for the Report Markdown starter. Use `--document-type decision-brief` for the evidence/edition starter. Replace the synthetic prose, data, figure, and source metadata, then run the generated `rebuild-report.ps1`. Use `--format artifact` only when the constrained syntax cannot express a reviewed requirement.

The bundle command forwards safe page size, orientation, PDF name, source visibility, and date visibility. It always creates paginated HTML before the PDF. If the artifact contains supported charts, it materializes them with Chart.js; chartless reports skip that stage. Paged.js owns pagination, running matter, page counters, and CSS break behavior. Neither tool owns report semantics or evidence.

The renderer owns the shared interactive reader, responsive layout, source affordances, semantic fallback, and visual styles. Do not patch those into the generated page manually.

## 7. Revise safely

When revising an existing report:

- Start from the full existing evidence package and edition source, not generated output.
- Preserve unrelated block IDs, order, data, prose, and sources.
- Patch only the requested section and directly dependent elements; preserve unselected canonical evidence.
- Rerender the complete report.
- Compare old and new artifact structure before handoff.

## 8. Validate and deliver

Run `scripts/check_report.py` and the checklist in `quality-checklist.md`. Deliver clickable paths to the interactive report, optional print source, paginated HTML/PDF, canonical artifact, and the most relevant supporting evidence.
