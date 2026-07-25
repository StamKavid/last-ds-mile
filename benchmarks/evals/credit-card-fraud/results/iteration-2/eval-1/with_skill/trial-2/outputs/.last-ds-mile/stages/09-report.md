# 09 — Report

See chat summary delivered to the user. Full supporting detail lives in
`00-frame.md` through `08-explain.md`. Key numbers to cite:

- Baseline (predict all genuine): PR-AUC 0.0013, ROC-AUC 0.500, accuracy 99.87%
  (misleading — see `04-baseline.md`).
- Best model (Random Forest, `class_weight="balanced"`): PR-AUC 0.814,
  ROC-AUC 0.959, evaluated on a temporal 30% holdout (never shuffled — see
  `05-validate.md`).
- Operating point trade-off: recall 70% at 99% precision, vs recall 80%+ at ~50%
  precision — threshold choice depends on a business cost input not provided (see
  `00-frame.md` assumptions).
- Known weak spot: recall drops to ~36% for fraud in the $5-$20 transaction range
  (vs ~70% elsewhere) — see `07-evaluate.md` subgroup table.
