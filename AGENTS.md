# Repository instructions

These instructions apply to the whole repository. More specific instructions in
`skill/create-auditable-reports/AGENTS.md` also apply inside that package.

1. Keep `artifact.json` as the canonical report intermediate representation.
2. Treat interactive and print HTML as generated output. Do not hand-edit it.
3. Keep the agent skill self-contained under `skill/create-auditable-reports/`.
4. Keep source data, query text, cutoff logic, assumptions, and provenance beside each real report.
5. Do not add credentials, signed URLs, connection strings, customer data, or other secrets.
6. Preserve the project-health fixture as the visual and validation baseline until it is intentionally replaced.
7. Use Paged.js for paginated preview and PDF output. Keep the Paged.js version pinned and block remote resources by default.
8. Run `scripts/Test-Repository.ps1` after changing the skill, scripts, artifact contract, or example.
9. Record source-format and renderer-boundary changes as decisions under `docs/decisions/`.
10. Keep any future Markdown-like syntax declarative. It must compile to `artifact.json`; it must not bypass provenance or validation.
