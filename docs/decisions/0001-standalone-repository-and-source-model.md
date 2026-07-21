# 0001: Use a standalone repository and preserve the artifact as the intermediate representation

- Status: accepted
- Date: 2026-07-21

## Context

The imported package contains an agent skill, executable utilities, a canonical JSON artifact, data and provenance examples, and generated HTML. It is more than published documentation and is not tied to a single application. Authors should eventually be able to create reports without writing HTML.

## Decision

Maintain the package in the standalone `auditable-reports` repository. Keep the installable agent skill in `skill/create-auditable-reports/`.

Treat `artifact.json` as the canonical intermediate representation. Treat interactive and print HTML as disposable renderer outputs. If a custom Markdown-like format is introduced, compile it to the artifact contract instead of rendering it directly to HTML.

Keep visual rendering in the shared Data Analytics renderer until a concrete requirement proves that the renderer must be replaced or versioned independently.

## Consequences

- Report semantics, validation, examples, and future authoring tools have one clear owner.
- `incursa-docs` may publish selected documentation later, but it is not the source of truth.
- Existing skill behavior remains installable and self-contained.
- A future authoring format can change without invalidating the renderer boundary.
- The current dependency on an installed plugin remains visible and must be addressed before reproducible CI can be guaranteed.
