# 04 — Honest Baseline

Implementation: `baseline.py`. Evaluated on the full deduplicated dataset
(283,726 rows, 473 fraud, prevalence 0.1667%) using the metrics chosen in
`/ds-frame`: PR-AUC as primary, recall-at-precision as decision-relevant
secondary.

## Baseline A — prior-probability / majority-class (formal no-skill floor)
Predict every transaction's fraud probability as the dataset's prior rate
(0.1667%).
- **PR-AUC: 0.001667** (equal to prevalence by construction — this is the
  mathematical floor for PR-AUC, not a meaningful "model").
- **ROC-AUC: 0.500** (by construction).

This is reported only as the formal floor, not used as the comparison
anchor: on this dataset, majority-class is a strawman (per the skill's own
warning) — with several raw PCA columns individually achieving AUC > 0.9
(see `/ds-explore`), any real anchor must be stronger than "predict the
prior" or a later model's "lift" over it would be meaningless.

## Baseline B — comparison anchor: single raw feature, no fitting
Score each transaction by `-V14` (raw column, sign flipped based on the
direction observed in `/ds-explore` — fraud has strongly negative `V14`).
This requires no parameter fitting: it's an existing column used as-is with
a direction inferred from EDA, the strongest defensible "no modeling"
anchor available given this dataset has no card/customer ID or merchant
field to build a manual fraud-ops rule from.

- **PR-AUC: 0.6050**
- **ROC-AUC: 0.9471**
- Recall at precision ≥ 0.90: **10.6%**
- Recall at precision ≥ 0.70: **55.8%**
- Recall at precision ≥ 0.50: **74.2%**

## What "beating the baseline" means
`/ds-model`'s candidate model(s) must exceed **PR-AUC 0.605** (Baseline B) to
demonstrate the multivariate model is earning its complexity over simply
thresholding the single strongest raw column. At the review-queue-relevant
precision band (50–90%), the model should materially improve recall over
Baseline B's 10.6–74.2% range at matching precision — that's the concrete,
decision-tied bar, not just a higher aggregate PR-AUC.
