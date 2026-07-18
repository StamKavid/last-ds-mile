# The Sealed Bet — LEDGER

## Contract
- target: `Churn`  ·  task: `classification`  ·  metric: `roc_auc`
- split: `random`  ·  baseline_score: `0.7420` (`heuristic`)
- ceiling_score: `0.8500`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `07e3f18757c64d47`  ·  sealed_at: `2026-07-17T19:57:00+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, warn-only)
- train-vs-held AUC: 0.5038 · σ: 0.0083 · lift: 0.46σ
- **CERTIFIED ✅**

## Probe (leakage-adversary, warn-only)
- `tenure`: solo_score 0.7367
- `Contract`: solo_score 0.7324
- `OnlineSecurity`: solo_score 0.7006
- `TechSupport`: solo_score 0.6980
- `InternetService`: solo_score 0.6903
- **CLEAR ✅ — no feature solo-predicts the target implausibly well**

## Build (auto)
- iter 1 · baseline · 'full 19-feature set to establish where things stand' → dev 0.8517 · ACCEPTED (new best)
- iter 2 · high_variance · 'dropped weak predictors gender, PhoneService' → dev 0.8395 · rejected (within noise floor)
- iter 3 · high_variance · 'dropped 3 more weak categoricals (MultipleLines, StreamingTV, StreamingMovies)' → dev 0.8402 · rejected (within noise floor)
- iter 4 · high_variance · 'engineered tenure_bucket ordinal feature on top of iter2 set' → dev 0.8489 · rejected (within noise floor)
- iter 5 · high_variance · 'dropped 7 weak/redundant service columns' → dev 0.8442 · rejected (within noise floor)
- iter 6 · high_variance · 'dropped 3 weakest categoricals only (lighter cut than iter5)' → dev 0.8494 · rejected (within noise floor)

## Verdict (seal opened once)
- sealed_score: 0.8471 · baseline: 0.7420 · σ (paired, model−baseline): 0.0090
- **lift = 11.68σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: +0.1050
