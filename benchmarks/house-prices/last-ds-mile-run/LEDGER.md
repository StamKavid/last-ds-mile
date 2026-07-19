# The Sealed Bet — LEDGER

## Contract
- target: `log_saleprice`  ·  task: `regression`  ·  metric: `rmse`
- split: `time`  ·  baseline_score: `0.2487` (`heuristic`)
- ceiling_score: `0.1150`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `71f76f0fcc2f8610`  ·  sealed_at: `2026-07-17T19:56:48+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, N/A for this split strategy)
- **N/A** — strategy="time" — dev/held are supposed to be distinguishable here (held is always later); this probe only certifies random/group splits

## Probe (leakage-adversary, warn-only)
- `OverallQual`: solo_score 0.6688
- `Neighborhood`: solo_score 0.5467
- `GrLivArea`: solo_score 0.4943
- `GarageCars`: solo_score 0.4640
- `BsmtQual`: solo_score 0.4473
- **CLEAR ✅ — no feature solo-predicts the target implausibly well**

## Build (auto)
- iter 1 · baseline · 'full 76-feature set to establish where things stand' → dev 0.1355 · ACCEPTED (new best)
- iter 2 · high_variance · 'dropped redundant collinear features (GarageArea, 1stFlrSF)' → dev 0.1347 · rejected (within noise floor)
- iter 3 · high_variance · 'dropped 7 more weak-correlation numeric features (|corr|<0.1)' → dev 0.1339 · rejected (within noise floor)
- iter 4 · high_variance · 'dropped 8 categoricals dominated by rare levels (Condition2, RoofMatl, etc.)' → dev 0.1364 · rejected (within noise floor)
- iter 5 · high_variance · 'engineered total_sf = GrLivArea + TotalBsmtSF' → dev 0.1327 · rejected (within noise floor)
- iter 6 · high_variance · 'dropped remaining weak porch/room-count features' → dev 0.1337 · rejected (within noise floor)

## Verdict (seal opened once)
- sealed_score: 0.1311 · baseline: 0.2487 · σ (paired, model−baseline): 0.0124
- **lift = 9.46σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: -0.1176
