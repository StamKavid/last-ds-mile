---
name: ds-prep
description: Cleans data and engineers features with leakage prevention as the organizing principle — every transform is fit on training data only and wrapped in a pipeline. Use when building features, encoding variables, or imputing missing values for a model.
---

# ds-prep — Cleaning & Feature Engineering

## Overview

Turns profiled, explored data into model-ready features, with leakage prevention as the
non-negotiable constraint on every transform.

## When to Use

- After `/ds-explore` has produced a hypothesis log and flagged leakage candidates.
- Building features, encoding categorical variables, or imputing missing values.
- NOT for: choosing the validation split (that's `/ds-validate`) — features must be
  leakage-safe regardless of how the data is later split.

## Core Process

1. Log every cleaning decision: what was changed, why, and what the alternative would
   have been.
2. For every candidate feature, ask: "would this value have been known at prediction
   time?" Reject or flag anything derived from future information or from the target
   itself.
3. Wrap every fit-requiring transform (scalers, encoders, imputers) in a pipeline or
   `ColumnTransformer` so it is fit on training folds only — never on the full dataset
   before splitting.
4. Resolve every leakage candidate flagged in `/ds-explore` explicitly before proceeding.
5. Write to `.last-ds-mile/stages/03-prep.md`: the cleaning log, the feature list with a
   known-at-prediction-time justification per feature, and the pipeline definition.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just fit the scaler on the whole dataset, it's just scaling, not really 'modeling'" | Any statistic computed across train+test before the split (mean, min/max, target encoding) leaks test-set information into training. No exceptions. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A feature is a rolling or aggregate statistic computed using the full dataset's date range | The time-traveling-feature pattern — recompute it using only data available as of each row's own timestamp. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] Every feature has an explicit known-at-prediction-time justification.
- [ ] All fit-requiring transforms live inside a pipeline, not fit on the full dataset.
- [ ] Every leakage candidate flagged in `/ds-explore` has been resolved, not ignored.
- [ ] `.last-ds-mile/stages/03-prep.md` written.
