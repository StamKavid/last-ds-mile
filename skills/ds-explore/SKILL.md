---
name: ds-explore
description: Runs systematic EDA — univariate, bivariate, and target-relationship analysis — with a running hypothesis log. Use after data understanding is complete and before feature engineering, or when asked to explore or visualize a dataset.
---

# ds-explore — Exploratory Data Analysis

## Overview

Systematically sweeps a profiled dataset for patterns relevant to the target, logging a
hypothesis for each finding instead of plotting aimlessly.

## When to Use

- After `/ds-data` has produced a data dictionary and integrity findings.
- Before feature engineering begins.
- NOT for: acting on findings by transforming features (that's `/ds-prep`) — this stage
  observes and hypothesizes, it doesn't change the data.

## Core Process

1. Univariate pass: distribution of each key variable (numeric: histogram and summary
   stats; categorical: value counts).
2. Bivariate pass: relationship of each candidate feature to the target, and obvious
   collinearity between candidate features.
3. Log a hypothesis for every pattern noticed ("higher X seems associated with target=1,
   hypothesis: because ...") rather than producing plots with no question behind them.
4. Flag anything that looks too predictive at this stage (see `ds-method`'s Red Flags)
   as a leakage candidate for `/ds-prep` to resolve.
5. Export the 1-3 plots that actually back the strongest findings from steps 1-2 (not
   every plot considered) to `.last-ds-mile/figures/02-<name>.png` — per `data-viz-standards`,
   state the hypothesis before building each one. Typically: the target's distribution
   (and its transform, if skewed) and the single strongest bivariate relationship found.
   This is the "critical/important only" bar, not exhaustive EDA output.
6. Write to `.last-ds-mile/stages/02-explore.md`: key findings, the hypothesis log,
   leakage candidates flagged for follow-up, and a reference to each exported figure next
   to the finding it illustrates.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just make a bunch of plots and see what jumps out" | Aimless plotting produces cherry-picked patterns. Every plot should test a stated hypothesis. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A feature is almost perfectly separated by target in a bivariate plot | Candidate leakage — don't treat it as a modeling win yet. Flag it for `/ds-prep`'s leakage check. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] Univariate and bivariate passes both done.
- [ ] Hypothesis log has one entry per notable finding.
- [ ] Any suspiciously predictive feature is flagged as a leakage candidate, not
      celebrated.
- [ ] The 1-3 most important plots are exported to `.last-ds-mile/figures/`, not just
      described in prose.
- [ ] `.last-ds-mile/stages/02-explore.md` written.
