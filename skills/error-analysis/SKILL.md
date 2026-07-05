---
name: error-analysis
description: Systematically slices residuals and errors to find where a model fails, rather than reporting one aggregate score. Use during or after /ds-evaluate, when a model's overall metric looks acceptable but stakeholder trust requires knowing where it underperforms, or when asked to debug why a model is "wrong" on specific cases.
---

# error-analysis

## Overview

An aggregate metric answers "how good on average" — error analysis answers "good for
whom, and wrong how." This is the systematic version of what `/ds-evaluate` does
inline, useful any time a deeper failure-mode investigation is needed.

## When to Use

- After a model's aggregate metric is known and acceptable, before trusting it
  broadly.
- Debugging a specific complaint ("the model is bad for X") by finding the actual
  pattern, not guessing.
- NOT for: picking the metric itself (see `metric-selection`) — this skill assumes
  the metric is already chosen and asks where performance diverges from that
  metric's average.

## Core Process

1. Compute out-of-fold (not in-sample) predictions for every row — error analysis on
   training-set-fit predictions is optimistic and misleading.
2. Slice error by every dimension the decision cares about: a segment, a time
   period, a feature range, a subgroup — not just one arbitrary cut.
3. Pull the worst N individual mispredictions and look for a shared trait (not just
   eyeball them one at a time with no hypothesis).
4. State the finding as a concrete, actionable pattern ("underperforms on X because
   Y"), not a vague "some errors exist."

## Techniques/Patterns

| Technique | What it reveals |
|---|---|
| Slice metric by categorical subgroup (segment, region, neighborhood, product line) | Whether one subgroup is silently much worse than the aggregate suggests |
| Slice metric by a continuous feature's quantile bins (e.g. price quintile, age decile) | Whether performance degrades at one end of a range — often the extremes |
| Residual vs. predicted-value plot (or a groupby summary of the same) | Systematic over/under-prediction bias at specific value ranges, not just noise |
| Worst-N mispredictions table, sorted by absolute error | Concrete cases to trace back to a shared root cause (a data issue, an undermodeled feature, an edge case) |
| Residual vs. time (for any temporal data) | Whether the model is drifting/degrading as time moves away from the training window |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The aggregate metric is good, that's enough" | This is `ds-method`'s "one aggregate metric is enough to report" rationalization by another name — a good average can hide a subgroup or range where the model is unusable. |
| "I looked at a few bad predictions, nothing jumped out" | A handful of examples eyeballed without a slicing table rarely surfaces a pattern — run the systematic slices first, then look at examples *within* the worst slice. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Every slice has been checked except the one the stakeholder actually cares about most | The analysis technically satisfies "slice performance exists" while missing the decision-relevant cut — go back and add it |

See `ds-method`'s Red Flags — "overall metric is good but never checked per-slice" is
this skill's direct trigger.

## Verification

- [ ] Predictions used for error analysis are out-of-fold, not in-sample.
- [ ] At least one slice matches a dimension the actual decision (from `/ds-frame`)
      cares about, not just a convenient one.
- [ ] The worst mispredictions were examined for a shared pattern, not just listed.
