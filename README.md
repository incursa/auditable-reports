# Auditable Reports

This repository is the source home for Incursa's reusable analytical-report baseline. It preserves the supplied `create-auditable-reports` agent skill, its deterministic utilities, and a synthetic golden example while leaving room for a friendlier authoring format later.

The core design decision is simple:

```text
human-friendly source (future)
           |
           v
     artifact.json          canonical, auditable intermediate representation
           |
           v
 shared Data Analytics renderer
           |
           +--> report.html
           +--> report_print.html (optional, script-free pagination source)
                        |
                        v
                 Paged.js 0.4.3
                        |
                        +--> report_paged.html
                        +--> report.pdf
```

Generated HTML is an output, not an authoring format. The current authoring source is `artifact.json`. A future Markdown-like source should compile to the same artifact rather than replace the evidence and provenance model.

## Why this is a separate repository

This package owns an artifact contract, executable tooling, fixtures, validation, and an installable agent skill. It therefore does not belong in `incursa-docs`, which publishes documentation owned by other source repositories. A focused repo also lets the authoring syntax, schema, renderer adapter, and tests evolve together without coupling them to a product codebase.

## Repository layout

- `skill/create-auditable-reports/` — self-contained agent skill imported from the source archive.
- `docs/BASELINE.md` — the report content, visual, evidence, and output baseline.
- `docs/AUTHORING-DIRECTION.md` — proposed path toward declarative `.report.md` authoring.
- `docs/INTAKE.md` — archive provenance, inventory, validation evidence, and identified gaps.
- `docs/decisions/` — durable architectural decisions.
- `scripts/Test-Repository.ps1` — local repository validation.
- `package.json` and `package-lock.json` — pinned Paged.js browser-pagination tooling.

## Quick start

Create a synthetic working directory:

```powershell
py skill\create-auditable-reports\scripts\new_report.py `
  --name "Quarterly Delivery Health" `
  --output .work\quarterly-delivery-health
```

Replace every synthetic value and source record, then render:

```powershell
py skill\create-auditable-reports\scripts\render_report.py `
  --artifact .work\quarterly-delivery-health\artifact.json `
  --output .work\quarterly-delivery-health\report.html
```

Validate the repository and shipped example:

```powershell
pwsh -File scripts\Test-Repository.ps1
```

Read `skill/create-auditable-reports/SKILL.md` before producing a real report.

For paginated output, install the pinned tooling once:

```powershell
npm install
```

Then create the script-free print source and paginate it:

```powershell
py skill\create-auditable-reports\scripts\build_print_report.py `
  --input .work\quarterly-delivery-health\report.html `
  --output .work\quarterly-delivery-health\report_print.html

py skill\create-auditable-reports\scripts\render_paged_output.py `
  --input .work\quarterly-delivery-health\report_print.html `
  --output .work\quarterly-delivery-health\report.pdf
```

The same pagination command creates a browser preview when the output ends in `.html`. It uses installed Chrome or Edge and blocks remote requests by default.

## Current boundaries

- The interactive renderer is supplied by the installed Data Analytics plugin; this repo intentionally does not fork that runtime.
- Paged.js 0.4.3 is the pinned print-pagination engine; it does not replace the interactive renderer or canonical artifact.
- The project-health fixture is synthetic and must never be presented as operational evidence.
- The artifact contract is documented but does not yet have a versioned JSON Schema.
- The custom Markdown-like authoring format is a proposal, not implemented syntax.
- No public license has been selected for this imported package.
