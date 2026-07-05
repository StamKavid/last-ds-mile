---
name: data-viz-standards
description: Chooses the right chart type and library for the audience — Altair for hypothesis-driven EDA, great_tables and Plotly for stakeholder-facing reports — and keeps charts honest (no distorted axes, no misleading aggregation). Use when building EDA plots, preparing figures or tables for a stakeholder report, or when a chart choice seems arbitrary or potentially misleading.
---

# data-viz-standards

## Overview

The right visualization tool depends on who's looking at it and why — an exploratory
hypothesis test and a stakeholder-facing table have different jobs and different
tools. This skill also covers the honesty checks that keep any chart from misleading
its audience, intentionally or not.

## When to Use

- Building plots during `/ds-explore` to test a hypothesis.
- Preparing tables or charts for `/ds-evaluate`'s slice performance or `/ds-report`'s
  stakeholder narrative.
- A chart's axis, aggregation, or scale choice seems like it could mislead, even
  unintentionally.
- NOT for: deciding which slices/subgroups to analyze in the first place (see
  `error-analysis`) — this skill is about how to present a finding, not which
  findings to look for.

## Core Process

1. Identify the audience first: exploratory (you, testing a hypothesis) or
   stakeholder-facing (someone deciding based on this). The right tool differs.
2. For exploratory work, pick the chart type from the decision table below and state
   the hypothesis it's testing (per `/ds-explore`'s own discipline) before building
   it.
3. For stakeholder-facing work, prefer a table (`great_tables`) over a chart when the
   audience needs to read specific numbers, and a chart only when a pattern or trend
   is the point.
4. Before finalizing any chart or table, run the honesty checklist (below) — a
   technically-correct chart can still mislead through axis or aggregation choices.

## Techniques/Patterns

### Library choice by purpose

| Purpose | Recommended library | Why |
|---|---|---|
| Fast, hypothesis-driven EDA plots | Altair | Declarative grammar-of-graphics — you state the encoding (x, y, color, facet) directly, which mirrors "state the hypothesis, then the chart" rather than imperative plot-building |
| Interactive drill-down / a dashboard | Plotly | Best interactivity and browser integration; native support in Streamlit/Dash if the project grows that direction |
| Very large or streaming data | Bokeh | More efficient than Altair/Plotly at genuinely large scale |
| Stakeholder-facing tables (slice performance, model card figures, report numbers) | `great_tables` | Purpose-built for publication-quality tables — currency/percent formatting, source notes, exports to HTML/image — a better fit than a chart when the audience needs exact numbers |

Both Altair and Plotly (v6+) accept Polars or pandas DataFrames directly via the
Narwhals compatibility layer — the dataframe library choice (see
`dataframe-performance`) doesn't force a particular visualization library or vice
versa.

### Honesty checklist

| Distortion | How it misleads | Fix |
|---|---|---|
| Truncated/non-zero y-axis on a bar chart | Exaggerates the visual difference between bars | Start bar charts at zero; a truncated axis is defensible only on a line chart showing a trend, and even then label it clearly |
| Aggregating away the subgroup that matters | A stakeholder sees an average that hides a real subgroup weakness | Cross-check against `error-analysis`'s slicing before finalizing a report chart — don't let the report chart re-introduce the aggregation problem the pipeline's evaluation stage already solved |
| Dual y-axes implying a correlation | Two unrelated-scale series plotted together can visually suggest a relationship that isn't in the data | Avoid dual-axis charts for anything used to justify a decision; use small multiples (faceting) instead |
| Cherry-picked date range or filter | Making a trend look better/worse than the full data supports | State the filter/date range explicitly in the chart title or caption, and check the same chart over the full available range before presenting the filtered version |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just use whatever chart type matplotlib defaults to" | The default isn't wrong, but picking deliberately (per the purpose table above) produces a chart that fits its audience instead of one that happens to render |
| "The chart looks more dramatic if I truncate the axis, and it's technically still accurate" | Technically accurate and honest are not the same thing — a truncated bar-chart axis is a well-documented way to mislead even without changing a single number |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A stakeholder report chart doesn't match the slice/subgroup findings already documented in `/ds-evaluate` | The report re-aggregated away a known weakness — go back and use the same slices, not a friendlier aggregation |

See `ds-method`'s shared Red Flags for the broader discipline this skill supports.

## Verification

- [ ] The chart or table type was chosen deliberately for its audience (exploratory
      vs. stakeholder-facing), not by default.
- [ ] Bar chart axes start at zero; any non-zero-start line chart is explicitly
      labeled.
- [ ] Any chart used to support a decision reflects the same slices/subgroups
      already documented in `/ds-evaluate`, not a more flattering aggregation.
