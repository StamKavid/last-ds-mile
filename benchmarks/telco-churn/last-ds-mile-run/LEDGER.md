# The Sealed Bet — LEDGER

## Contract
- target: `Churn`  ·  task: `classification`  ·  metric: `roc_auc`
- split: `random`  ·  baseline_score: `0.5000`
- ceiling_score: `0.8500`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `07e3f18757c64d47`  ·  sealed_at: `2026-07-17T13:35:31+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, warn-only)
- probe skipped: could not convert string to float: 'Male'

## Build (auto)
- iter 1 · baseline · 'full 19-feature set to establish where things stand' → dev 0.8497 · ACCEPTED (new best)
- iter 2 · high_variance · 'dropped weak predictors gender, PhoneService' → dev 0.8503 · rejected (within noise floor)
- iter 3 · high_variance · 'dropped 3 more weak categoricals (MultipleLines, StreamingTV, StreamingMovies)' → dev 0.8480 · rejected (within noise floor)
- iter 4 · high_variance · 'engineered tenure_bucket ordinal feature on top of iter2 set' → dev 0.8503 · rejected (within noise floor)
- iter 5 · high_variance · 'dropped 7 weak/redundant service columns' → dev 0.8420 · rejected (within noise floor)
- iter 6 · high_variance · 'dropped 3 weakest categoricals only (lighter cut than iter5)' → dev 0.8491 · rejected (within noise floor)

## Verdict (seal opened once)
- sealed_score: 0.8268 · baseline: 0.5000 · σ: 0.0120
- **lift = 27.27σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: +0.3268
