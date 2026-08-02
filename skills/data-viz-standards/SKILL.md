---
name: data-viz-standards
description: Chooses the right chart and library for the audience and keeps it honest — no truncated axes, no misleading aggregation. Use when someone asks which chart or plot type to use, or whether to reach for matplotlib, Plotly, or Altair. Use when a figure looks misleading or a chart choice seems arbitrary.
---

# data-viz-standards

## Overview

The right visualization tool depends on who's looking and why — exploratory hypothesis
testing and a stakeholder-facing table need different tools. Also covers the honesty
checks that keep a chart from misleading its audience, intentionally or not.

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
| Fast, hypothesis-driven EDA plots (interactive, notebook-embedded) | Altair | Declarative grammar-of-graphics — state the encoding (x, y, color, facet) directly, mirroring "state the hypothesis, then the chart" |
| Interactive drill-down / a dashboard | Plotly | Best interactivity and browser integration |
| Very large or streaming data | Bokeh | More efficient than Altair/Plotly at genuine scale |
| Stakeholder-facing tables (slice performance, model card figures, report numbers) | `great_tables` | Purpose-built for publication-quality tables — currency/percent formatting, source notes, HTML/image export — a better fit than a chart when exact numbers matter |
| **Committed static evidence** — a stage-doc figure saved to `.last-ds-mile/figures/*.png`, not viewed interactively | **matplotlib** | Altair/Plotly's native output is an interactive spec, the wrong shape for a committed PNG; `savefig` is the direct path. Also what SHAP's own plotting functions render with, so figures share one library. |

Both Altair and Plotly (v6+) accept Polars or pandas directly via the Narwhals
compatibility layer — the dataframe library choice (see `dataframe-performance`)
doesn't force a particular visualization library.

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
