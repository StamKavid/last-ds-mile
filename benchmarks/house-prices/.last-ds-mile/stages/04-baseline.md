# Stage 4 — Honest Baseline

## Baseline definition

**Dumbest baseline (the anchor):** predict the training set's median `log(SalePrice)`
for every row, regardless of any feature. Median chosen over mean for a regression
target this skewed (see `/ds-frame`'s log-space metric choice, and `metric-selection`'s
regression table).

- Median `SalePrice`: **$163,000** (median `log1p(SalePrice)` = 12.0014).
- **Anchor RMSE (log-space): 0.3999.**

## Secondary reference point (not the anchor — context only)

A neighborhood-median lookup (still "dumb" — no model, just a coarser grouping) scores
**RMSE 0.2637** in-sample. This is reported only to answer `/ds-frame`'s "do we even
need ML?" gate honestly: even a trivial grouping beats the flat median by a wide
margin, which is expected (location is the single biggest lever in real estate) and
argues for a model that can combine `Neighborhood` with the other ~85 features rather
than stopping at a lookup table. This number is **not** the baseline any model is
compared against below — it's computed in-sample (each row's own value contributes to
its own group median) and is not a fair apples-to-apples comparison to a properly
cross-validated model score. The flat-median anchor above is the actual bar.

## What "beating it" concretely means

Any candidate in `/ds-model` must score a cross-validated `log(SalePrice)` RMSE
**meaningfully below 0.3999**, where "meaningfully" is defined relative to that
candidate's own fold-to-fold standard deviation (see `uncertainty-quantification`) —
not just numerically lower on a single run.
