# ADR 0005: Add fixed document profiles

- Status: accepted
- Date: 2026-07-21

## Context

The constrained language originally required an Executive Summary or Technical Summary. That vocabulary works for analytical reports but makes lessons and journals read like renamed business documents. Test fixtures need to exercise those narrative forms without introducing themes, templates, or arbitrary layouts.

## Decision

Add an optional flat front-matter property named `document-type`. Support exactly four values: `report`, `technical`, `lesson`, and `journal`. Default to `report` for backward compatibility.

Each profile requires one standard first section: Executive Summary, Technical Summary, Lesson Overview, or Entry Summary respectively. The profile changes only the opening vocabulary. It does not change the artifact contract, CSS, available directives, chart options, table limits, or rendering pipeline.

## Consequences

- Lessons and journals can use natural headings while remaining ordinary Report Markdown.
- Existing sources continue to compile without changes.
- Every document type exercises the same bounded building blocks and print behavior.
- Adding another profile requires a compiler, documentation, and fixture change rather than ad hoc author styling.
