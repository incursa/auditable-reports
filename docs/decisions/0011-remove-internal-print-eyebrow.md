# Decision 0011: Remove the Internal Renderer Eyebrow from Print Editions

## Context

The portable renderer labels every generated report as `Data Analytics report`.
That label describes the implementation rather than the document's audience or
purpose. It appeared on consulting collateral, legal drafts, operational forms,
and approval records, making otherwise clean documents feel more technical and
template-generated.

## Decision

Hide the generic surface label in the script-free print edition. Keep the
document title, description, local brand wordmark, running title, and page
numbering. The interactive artifact remains unchanged, and a future explicit
surface-label option can be added if a document family needs one.

## Consequences

Print outputs read as client or internal business documents rather than as
renderer diagnostics. The change is presentation-only and does not alter the
canonical artifact, provenance, or generated interactive report.
