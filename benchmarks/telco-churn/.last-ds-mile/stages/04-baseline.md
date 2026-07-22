# Stage 4 — Honest Baseline

## Baseline definition

Majority-class classifier: predict `Churn=No` for every customer (the majority
class, 73.5%), equivalent to a no-skill classifier for AUC purposes.

## Score, using the exact metric from `/ds-frame`

**ROC-AUC = 0.5** by construction (random ranking). **PR-AUC = the base rate =
0.2654.** Accuracy would be 73.5% — a number that sounds reasonable and is, in fact,
exactly `ds-method`'s "model accuracy matches the majority-class rate" Red Flag; not
reported as a metric anywhere in this run for that reason, same discipline applied
here as at credit-card-fraud despite the milder imbalance.

## What "beating it" means

Any real candidate must clear ROC-AUC meaningfully above 0.5 by more than fold noise
— and PR-AUC meaningfully above 0.2654 — not just "above chance" but by a margin that
survives the fold-to-fold spread reported in `/ds-model`.
