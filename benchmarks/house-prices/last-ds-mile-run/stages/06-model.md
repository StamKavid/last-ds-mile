# 06 — Modeling

**Gate check:** `04-baseline.md` and `05-validate.md` both exist and were read before
modeling began — confirmed.

For this run, modeling was done through the Sealed Bet mechanism (`/ds-seal` →
`/ds-auto` → `/ds-open`) rather than a hand-rolled candidate-model loop — the experiments
table this stage would otherwise contain lives in `.last-ds-mile/LEDGER.md`'s `## Build
(auto)` section (6 iterations, reusing `05-validate.md`'s exact time-based split code
via `run_iteration`), and the baseline comparison lives in `LEDGER.md`'s `## Verdict`
section.

**Summary (full detail in `LEDGER.md`):** iteration 1 (all 76 features) was the winning
framing — every subsequent attempt to reduce the `high_variance` regime (dropping
features, engineering a `total_sf` feature) was rejected by the Ladder as within the
noise floor, and the loop correctly early-stopped after 5 consecutive rejections rather
than exhausting its full 15-iteration budget. Refit on the full dev set, then scored on
the sealed held set: **RMSE = 0.131, lift = 26.4σ over the flat-median baseline** — see
`09-report.md` for the full comparison and `BENCHMARKS.md` for how this compares to
Kaggle's known leaderboard characteristics for this exact problem.
