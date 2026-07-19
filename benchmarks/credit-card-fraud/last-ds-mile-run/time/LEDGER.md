# The Sealed Bet — LEDGER

## Contract
- target: `Class`  ·  task: `classification`  ·  metric: `auprc`
- split: `time`  ·  baseline_score: `0.0518` (`heuristic`)
- ceiling_score: `0.8500`  ·  ceiling_source: `human`  ·  budget: `15`
- input_mode: `full`  ·  data_hash: `76274b691b16a6c4`  ·  sealed_at: `2026-07-19T07:36:23+00:00`

## Experiments (dev only — none of these count yet)


## Probe (split-adversary, N/A for this split strategy)
- **N/A** — strategy="time" — dev/held are supposed to be distinguishable here (held is always later); this probe only certifies random/group splits

## Probe (leakage-adversary, warn-only)
- `V14`: solo_score 0.9513 ⚠
- `V12`: solo_score 0.9411
- `V4`: solo_score 0.9361
- `V11`: solo_score 0.9185
- `V10`: solo_score 0.9182
- **⚠ SUSPECT — 1 feature(s) solo-predict the target implausibly well**

## Verdict (seal opened once)
- sealed_score: 0.8158 · baseline: 0.0518 · σ (paired, model−baseline): 0.0374
- **lift = 20.45σ** → SHIPPED ✅  (ship iff lift > 2σ)
- sealed−baseline gap: +0.7640
