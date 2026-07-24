---
name: ds-frame
description: Frames a vague data science ask into a crisp problem statement — unit of analysis, target definition, the decision the output feeds, and a success metric tied to that decision. Use when starting a new DS project, when asked to "build a model for X" without a defined target or metric, or when a request has no clear success criterion yet.
---

# ds-frame — Problem Framing

## Overview

Turns a vague ask into a crisp problem before any data is touched: what decision this
feeds, what exactly is being predicted, and how success will be measured against that
decision — not just against a modeling metric.

## When to Use

- Starting a new DS project or a new modeling question within an existing one.
- The user asks for "a model" or "a prediction" without a defined target, decision, or
  success metric.
- NOT for: refining an already-framed problem's features or data (that's `/ds-data` and
  `/ds-prep`); this stage is about the *question*, not the data.

## Core Process

1. Ask what decision this will inform: who acts on the output, how often, and what
   happens today without it.
2. Define the unit of analysis and the target variable precisely — not "churn" but
   "customer with 0 purchases in the next 90 days, as of signup+30 days."
3. Take an **information inventory**: write down what will actually be known at the
   moment of prediction versus what only becomes known after the fact. Calendar, account
   age, and prior-period totals are usually available; same-day outcomes, values that
   arrive later, and anything derived from the target are not. This is the framing-time
   complement to `/ds-prep`'s per-feature check — it decides whether the problem is even
   feasible and tells you what signal to go looking for before anyone builds a feature.
4. Ask whether this needs ML at all, or whether a simple rule or lookup would solve it
   just as well (the "do we even need ML?" gate).
5. Pick a success metric tied to the decision, not only a modeling metric — e.g. "reduce
   false negatives below X because a missed case costs $Y," not just "maximize AUC." Ask
   explicitly whether over- and under-shooting cost the same: if understaffing hurts more
   than overstaffing, a symmetric metric (RMSE, accuracy) optimizes the wrong thing — see
   `metric-selection` for the asymmetric-cost options.
6. Write the brief to `.last-ds-mile/stages/00-frame.md`: problem statement, unit of
   analysis, target definition, the information inventory, decision, success metric, and
   explicit non-goals.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The stakeholders just want 'a model', I don't need to press on the decision" | Without a decision the metric is arbitrary, and you'll optimize the wrong thing. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Success metric is a pure ML metric (accuracy/AUC) with no tie to a business or decision cost | Ask what a 1-point change in that metric is actually worth before treating it as the target to optimize. |
| The target is a future value of a time-indexed series ("predict tomorrow's demand/count/load") | This is forecasting, which this plugin's gates aren't tuned for (see README → Scope). You can still frame and run it here, but say so out loud: a mean/majority baseline is likely a strawman (see `ds-baseline`), and the lag/rolling features that would carry most of the signal are not something these stages build for you. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] Target variable is defined precisely enough that two people would compute it
      identically from raw data.
- [ ] An information inventory — what's known at prediction time vs. only after the fact
      — was written down.
- [ ] The decision this feeds is named explicitly.
- [ ] The "do we even need ML?" question was asked and answered.
- [ ] Over- vs under-prediction cost was checked for asymmetry, not assumed symmetric.
- [ ] If the target is a future value of a time series, the forecasting scope caveat was
      stated rather than left implicit.
- [ ] `.last-ds-mile/stages/00-frame.md` written with problem statement, target,
      information inventory, decision, metric, and non-goals.
