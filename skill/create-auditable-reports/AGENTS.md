# Report package agent instructions

These instructions apply to all work inside this package.

1. Read `SKILL.md` before creating or revising a report.
2. Treat `artifact.json` as the source of truth and generated HTML as disposable output.
3. Create each real report in its own directory outside `assets/starter/` and `assets/examples/`.
4. Preserve reviewed datasets, source queries, cutoff logic, assumptions, and provenance beside the artifact.
5. Use the installed Data Analytics portable renderer through `scripts/render_report.py`; do not build a second interactive HTML runtime.
6. Do not overwrite example outputs unless the task explicitly updates the package.
7. Never replace synthetic labels with real claims until source data has been inspected and validated.
8. Keep machine-local credentials, connection strings, signed URLs, and secrets out of artifacts and HTML.
9. Validate every generated report with `scripts/check_report.py` before handoff.
10. Create a script-free print source only when requested or when the report brief explicitly requires one; use pinned Paged.js for paginated HTML preview or PDF output.
