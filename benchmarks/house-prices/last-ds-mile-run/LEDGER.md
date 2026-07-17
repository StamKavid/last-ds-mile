# The Sealed Bet — LEDGER

## Contract
- target: `log_saleprice`  ·  task: `regression`  ·  metric: `rmse`
- split: `time`  ·  baseline_score: `0.4075`
- ceiling_score: `0.1150`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `71f76f0fcc2f8610`  ·  sealed_at: `2026-07-17T13:19:01+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, warn-only)
- probe skipped: could not convert string to float: 'RL'

## Build (auto)
- iter 1 · baseline · 'full 76-feature set to establish where things stand' → dev 0.1353 · ACCEPTED (new best)
- iter 2 · high_variance · 'dropped redundant collinear features (GarageArea, 1stFlrSF)' → dev 0.1347 · rejected (within noise floor)
- iter 3 · high_variance · 'dropped 7 more weak-correlation numeric features (|corr|<0.1)' → dev 0.1396 · rejected (within noise floor)
- iter 4 · high_variance · 'dropped 8 categoricals dominated by rare levels (Condition2, RoofMatl, etc.)' → dev 0.1347 · rejected (within noise floor)
- iter 5 · high_variance · 'engineered total_sf = GrLivArea + TotalBsmtSF on iter4 feature set' → dev 0.1341 · rejected (within noise floor)
- iter 6 · high_variance · 'dropped remaining weak porch/room-count features' → dev 0.1358 · rejected (within noise floor)

## Verdict (seal opened once)
- sealed_score: 0.1309 · baseline: 0.4075 · σ: 0.0105
- **lift = 26.43σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: -0.2766
