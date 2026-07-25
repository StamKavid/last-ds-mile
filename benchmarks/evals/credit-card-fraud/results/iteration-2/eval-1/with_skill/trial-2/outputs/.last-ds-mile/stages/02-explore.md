# 02 — EDA

## Amount
Fraud transactions are *not* systematically larger — median fraud amount ($9.25) is
actually lower than genuine ($22.00), though fraud has a fatter tail relatively
(mean $122 vs $88, but max fraud is $2,126 vs genuine max $25,691). Confirms the
`00-frame.md` call that a simple amount-threshold rule would not work.

## Time
Fraud is mildly more common in early-morning hours (median hour 12 vs 15 for
genuine) but the effect is weak — not a strong standalone signal, and only 2 days of
data means this could be noise rather than a real diurnal pattern. Kept as a feature
but not relied on.

## Feature separability
Correlation of each feature with `Class` shows several PCA components with
meaningful (if modest) linear separation: `V17` (-0.33), `V14` (-0.30), `V12` (-0.26),
`V10` (-0.22), `V16`, `V3`, `V7`, `V11`. No single feature is dominant — consistent
with needing a multivariate model rather than a rule on one field, reinforcing the
"do we need ML" answer in `00-frame.md`.

## Class imbalance implication for modeling
492 fraud rows total means even a 5-fold stratified split leaves ~98 fraud examples
per fold — thin enough that variance across folds should be reported, not just an
average.
