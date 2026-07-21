---
document-type: journal
description: A fictional weekly journal combining reflection, small quantitative visuals, a log table, and an illustration.
generated-at: 2026-07-21T22:20:00Z
status: fixture
data: report.data.json
---
# A Week of Smaller Commitments

## Entry Summary

<!-- source: journal_log -->

This fictional week was less about finishing a dramatic project and more about making promises small enough to keep. Seven brief entries captured the pattern: energy improved after time outdoors, focused work was best before lunch, and the most satisfying moments were ordinary conversations.

> The question I want to carry forward is simple: what deserves unhurried attention today?

::: metrics
id: week_snapshot
dataset: headline
source: journal_log
metric: entries | Journal entries | number | One short entry for each day.
metric: focused_hours | Focused hours | number | Total protected focus time in the synthetic log.
metric: outdoors_minutes | Minutes outdoors | number | Total outdoor time in the synthetic log.
metric: average_energy | Average energy | number | Average self-rating on a ten-point scale.
:::

## Energy rose toward the weekend

<!-- source: journal_log -->

The daily scores are not a health measure; they are a lightweight reflection cue. The strongest days also included a walk and fewer evening commitments.

::: chart
id: daily_energy
type: bar
title: Daily energy check-in
subtitle: Fictional self-rating from 1 to 10
dataset: days
source: journal_log
category: day
value: energy
category-label: Day
value-label: Energy score
format: number
:::

## Time went mostly to work and relationships

::: chart
id: time_allocation
type: pie
title: Deliberate time allocation
subtitle: Twenty-eight fictional discretionary hours
dataset: allocation
source: journal_log
category: category
value: hours
category-label: Category
value-label: Hours
format: number
:::

## Daily log

::: table
id: daily_table
title: Seven-day reflection log
subtitle: Small observations rather than comprehensive tracking
dataset: days
source: journal_log
column: day | Day | text
column: sleep | Sleep | number
column: focus | Focus | number
column: outdoors | Outdoors | number
column: energy | Energy | number
column: note | One-line note | text
:::

## A reusable evening prompt

The report also exercises a code-style block for text that should preserve line breaks:

```text
NOTICE: What held my attention?
NAME:   What feeling or need was present?
NEXT:   What is one kind, concrete next step?
```

## Memory map

::: figure
id: weekly_memory_map
path: week-map.svg
alt: A desk with an open journal, a mug, a small plant, and seven colored day markers connected by a loose line.
caption: Synthetic journal illustration used to test a decorative figure alongside reflective prose.
source: journal_illustration
:::

## Things worth carrying forward

- Put the phone in another room during the first focus block.
- Ask one better follow-up question in each important conversation.
- Leave one evening unscheduled.
- Treat the journal as a place to notice, not a scorecard to optimize.

Every entry, number, and image in this document is invented for report testing.
