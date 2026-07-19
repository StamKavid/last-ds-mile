# The Sealed Bet — LEDGER

## Contract
- target: `Class`  ·  task: `classification`  ·  metric: `auprc`
- split: `random`  ·  baseline_score: `0.1327` (`heuristic`)
- ceiling_score: `0.8500`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `76274b691b16a6c4`  ·  sealed_at: `2026-07-19T07:39:26+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, warn-only)
- train-vs-held AUC: 0.4990 · σ: 0.0013 · lift: -0.76σ
- **CERTIFIED ✅**

## Probe (leakage-adversary, warn-only)
- `V14`: solo_score 0.9529 ⚠
- `V4`: solo_score 0.9363
- `V12`: solo_score 0.9356
- `V11`: solo_score 0.9224
- `V10`: solo_score 0.9162
- **⚠ SUSPECT — 1 feature(s) solo-predict the target implausibly well**

## Verdict (seal opened once)
- sealed_score: 0.6882 · baseline: 0.1327 · σ (paired, model−baseline): 0.0439
- **lift = 12.65σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: +0.5555
