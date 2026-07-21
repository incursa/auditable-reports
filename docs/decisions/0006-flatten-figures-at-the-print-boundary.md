# ADR 0006: Flatten figures at the print boundary

- Status: accepted
- Date: 2026-07-21

## Context

The shared interactive renderer safely places custom HTML blocks in sandboxed `srcdoc` iframes. Report Markdown figures compile to one of those blocks. Paged.js preserves the iframe element, but its paginated capture does not reliably include the nested image, leaving a blank area in HTML preview and PDF output.

## Decision

Keep the sandboxed iframe in interactive HTML. During script-free print extraction, recognize only the compiler-owned `report-figure` vocabulary inside the iframe and flatten it into the print document.

Use an allowlist parser that preserves `figure`, data-URI `img`, `figcaption`, and `span` content. Discard embedded styles, scripts, event handlers, external image URLs, and every other element. Apply fixed print CSS to the extracted figure.

## Consequences

- Figure directives render in Paged.js HTML and PDF output.
- Interactive custom HTML remains isolated in the shared renderer's sandbox.
- Print extraction does not become a general arbitrary-HTML injection path.
- Any future printable custom block needs its own narrow allowlisted extractor.
