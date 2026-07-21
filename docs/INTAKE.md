# Intake record

## Source

- Archive: `C:\shared\downloads\create-auditable-reports.zip`
- SHA-256: `F85F2B072EA6F832EFBF1A9958A05F734C27A8614360DED9C88A272B06EADEB7`
- Intake date: 2026-07-21
- Imported package: `skill/create-auditable-reports/`

The archive was imported without changing its package files. Repository-level documentation and validation were added around it.

## Package inventory

- `SKILL.md` and `agents/openai.yaml` define an installable agent skill.
- `references/` defines the workflow, artifact-authoring conventions, quality checklist, and sample prompts.
- `scripts/new_report.py` creates a synthetic report workspace.
- `scripts/render_report.py` invokes the installed Data Analytics portable renderer.
- `scripts/build_print_report.py` extracts a script-free print edition from the semantic fallback.
- `scripts/check_report.py` performs artifact, interactive HTML, and print-safety checks.
- `assets/starter/` is a synthetic authoring starter.
- `assets/examples/project-health/` is a generated interactive and print fixture.

## Verification performed

- The shipped project-health artifact, interactive HTML, and print HTML pass `check_report.py`.
- Re-rendering the shipped artifact produced the same SHA-256 as the archived `report.html`.
- The Python utilities compile successfully.
- The desktop report was loaded from a local HTTP server in installed Chrome and the interactive chart rendered.
- The report was visually inspected at 1440 px and 390 px widths.

## Strengths worth preserving

- Clear separation between analysis/provenance, canonical artifact, and generated output.
- Answer-first report structure with nearby interpretation.
- Source bindings on metrics, charts, tables, and quantitative narrative.
- Self-contained interactive handoff with semantic fallback.
- Optional script-free print output.
- Synthetic fixtures are labeled honestly.

## Gaps to address deliberately

- The renderer is discovered through the installed Data Analytics plugin cache rather than a versioned package dependency.
- The documented artifact shape does not yet have a formal JSON Schema or compatibility policy.
- Validation checks top-level structure and core references but not every block reference, source path, manifest/top-level source mismatch, or narrative citation rule.
- Browser verification initially reported `structural_only`; explicitly pointing it at installed Chrome timed out during static-chart generation.
- The enhanced mobile reader overflows a 390 px viewport.
- The repo has no selected public license.
- No Markdown-like compiler exists yet, by design.

## Post-intake pagination baseline

Paged.js 0.4.3 was added after intake as the pinned pagination engine. The original archive remains preserved under `skill/create-auditable-reports/` except for intentional follow-up changes to its instructions, print CSS, validation, and scripts.

The updated print path keeps `report_print.html` script-free, adds CSS Paged Media running matter and break rules, and uses `render_paged_output.py` for paginated HTML or PDF. Remote requests are blocked by default.

## Post-intake Chart.js baseline

Chart.js 4.5.1 was added after intake as a pinned build-time visualization adapter. It reads the existing artifact chart definitions, renders supported charts in a controlled local browser with animation disabled, and embeds PNG output in `report_charted.html`. The existing semantic data table remains immediately after each chart for exact lookup and accessibility. `report_charted.html` stays script-free and becomes the preferred Paged.js input when the artifact contains charts.

## Post-intake authoring baseline

Report Markdown v0.1 was added after intake as the default routine authoring surface. It preserves ordinary Markdown prose and code, adds only metrics/chart/table/figure directives, loads bounded datasets and sources from one JSON sidecar, and compiles deterministically to the canonical artifact. The direct artifact workflow remains available for advanced requirements.
