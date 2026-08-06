# Decision 0012: Keep List Items Together in Print Editions

## Context

Several contract and operational drafts contained short checklist or clause
lists that split at a page boundary. In the worst case, a continuation word
appeared at the top of the next page, which made the document look unfinished.

## Decision

Apply `break-inside: avoid` to individual list items in the script-free print
edition. This preserves the source and canonical artifact while keeping short
checklist and clause items readable across pages.

## Consequences

Short lists may leave a small amount of unused space at the bottom of a page,
but they will no longer strand a single line or word. Long narrative sections
and tables retain their existing pagination behavior.
