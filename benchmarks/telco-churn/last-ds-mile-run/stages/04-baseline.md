# 04 — Honest Baseline

**Baseline definition:** predict the training set's mean churn rate (a constant
probability) for every held-out row — the standard "dumb" baseline for a classification
problem scored by ROC-AUC, per `sealed_bet.metrics`'s own `baseline_kind="mean"`
convention for this metric.

**"Do we even need ML?" check** (from `00-frame.md`): "target every month-to-month
customer" is a real, simple, non-ML alternative — 42.7% of them churn (`02-explore.md`),
so it would catch a large share of true churners. But it targets ~55% of the whole
customer base (most customers are month-to-month) to catch a 42.7%-churning subset —
very low precision. A constant-probability baseline is even dumber than this rule and
sets the honest floor; a real model needs to beat this floor by a real margin (`>2σ`)
to justify its complexity over even the simple contract-type rule, let alone doing
nothing.

**Score:** computed automatically by `/ds-seal`'s `baseline_score()`, using the training
fold's mean churn rate as the constant prediction — the actual number is recorded in
`LEDGER.md`'s Contract section (`baseline_score`), not duplicated by hand here.

**What "beating it" means:** the sealed model's ROC-AUC must clear the mean-baseline's
ROC-AUC (a mean-prediction baseline scores ~0.5 ROC-AUC by construction, since a constant
prediction has no discriminative power) by more than `2σ` — a materially informative
model, not merely "a bigger number."
