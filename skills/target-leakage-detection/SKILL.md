---
name: target-leakage-detection
description: Detects target leakage — features that encode the future, the target itself, or contamination between train and test data. Use when a metric looks too good on the first try, when engineering features from time-ordered or aggregated data, or when a single feature dominates an importance ranking.
---

# target-leakage-detection

## Overview

Leakage is the single most common way a DS project's offline metric lies about real
world performance. This skill gives concrete detection techniques for the four ways it
usually happens, rather than a vague "watch out for leakage" reminder.

## When to Use

- A metric looks implausibly good on the first real attempt (see `ds-method`'s Red
  Flags).
- Building a feature from an aggregate, a rolling window, or a join that could include
  future rows.
- A single feature dominates importance rankings in `/ds-explain` or an ad hoc check.
- NOT for: choosing a validation split (that's `validation-strategy`) — this skill is
  about what's *inside* a feature, not how data is split.

## Core Process

1. For every candidate feature, ask the "would this value have been known at
   prediction time" question from `/ds-prep` — but here go one level deeper: check the
   actual computation, not just the column name.
2. Run the four checks in the table below against every feature that wasn't hand-
   verified already.
3. If a check fires, don't quietly drop the feature — trace it to its source (a join?
   an aggregate? a leaked label?) and record what was fixed.

## Techniques/Patterns — four leakage types and how to catch each

| Leakage type | How it slips in | Detection technique | Fix |
|---|---|---|---|
| Post-outcome feature | A column is only populated *after* the target is known (e.g. "cancellation_reason" when predicting churn, "days_to_close" when predicting whether a deal closes) | Ask each feature's owner/source system when it's populated relative to the target event, not just what it's named | Drop it, or replace with a version computed strictly before the target event |
| Full-dataset aggregate ("time-traveling feature") | A rolling mean/sum/rank computed once over the whole dataset instead of per-row as-of-date | Recompute the same aggregate using only rows with an earlier timestamp than the row being predicted, and diff against the original — if they differ, the original leaked | Recompute as an as-of, expanding/rolling-window aggregate |
| Train/test contamination | The same real-world entity (customer, house, patient) appears in both train and validation, or a transform (scaler, encoder, target encoding) was fit on the full dataset before splitting | Check for duplicate/near-duplicate rows or shared keys across the split; confirm every fit-requiring transform lives inside a pipeline fit per-fold | Group-aware splitting (see `validation-strategy`); move every stateful transform inside the CV loop |
| Direct target derivation | A feature is an arithmetic function of the target itself (e.g. "profit_margin" when predicting "profit", where margin = profit/revenue) | Compute the correlation AND check the literal formula/join that produced the feature, not just the correlation number | Drop the feature; if the underlying real-world quantity is genuinely available at prediction time, recompute it without touching the target |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The correlation isn't 1.0, so it's probably not leakage" | Real leaks are rarely perfectly 1.0 — noise in the source system, encoding quirks, or partial contamination all produce a merely "very high" rather than perfect correlation. A 0.95 correlation is still worth tracing. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

See `ds-method`'s Red Flags — "metric looks too good on the first try" and "a single
feature has near-perfect importance" are this skill's primary triggers.

## Verification

- [ ] Every feature that triggered a Red Flag was traced to its actual computation,
      not just its column name.
- [ ] Any full-dataset aggregate was recomputed as an as-of / per-fold statistic and
      re-checked.
- [ ] The fix (drop, recompute, or re-split) is recorded, not just "removed the
      suspicious column."
