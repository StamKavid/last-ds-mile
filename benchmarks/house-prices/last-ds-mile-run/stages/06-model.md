# 06 — Modeling

**Gate check:** `04-baseline.md` and `05-validate.md` both exist and were read before
modeling began — confirmed.

For this run, modeling was done through the Sealed Bet mechanism (`/ds-seal` →
`/ds-auto` → `/ds-open`) rather than a hand-rolled candidate-model loop — the experiments
table this stage would otherwise contain lives in `last-ds-mile-run/LEDGER.md`'s `## Build
(auto)` section (6 iterations, reusing `05-validate.md`'s exact time-based split code
via `run_iteration`), and the baseline comparison lives in `LEDGER.md`'s `## Verdict`
section.

**Re-run note:** this stage was re-run twice after a series of fixes to `sealed_bet`
itself, surfaced by dogfooding this exact benchmark (see `BENCHMARKS.md`): (1) the
Contract's baseline is now the neighborhood-$/sqft heuristic named in `04-baseline.md`,
not a flat median; (2) the ship gate's σ is now the paired bootstrap difference between
the model's and baseline's scores on the same held rows, not the model's own score
variance in isolation; (3) the split-adversary probe now skips (rather than
misleadingly firing "SUSPECT") for this dataset's `time` split; (4) the leakage-adversary
probe, previously dead code, now actually runs. None of these touched the modeling
approach — the same iteration framings from the original run were reused verbatim across
both re-runs, since that feature-engineering research doesn't change just because the
verdict math got corrected. (A stratified-split fix landed between the two re-runs too,
but it only affects classification + `random` splits — this dataset's `time` strategy is
unaffected, which is why these numbers barely moved between re-runs.)

**Summary (full detail in `LEDGER.md`):** iteration 1 (all 76 features) was again the
winning framing — every subsequent attempt to reduce the `high_variance` regime (dropping
features, engineering a `total_sf` feature) was again rejected by the Ladder as within the
noise floor, and the loop again early-stopped after 5 consecutive rejections. Refit on the
full dev set, then scored on the sealed held set: **RMSE = 0.1311, baseline (heuristic)
= 0.2487, paired σ = 0.0124, lift = 9.46σ → SHIPPED.** This lift is smaller than the
26.4σ this stage originally reported — expected and correct, since that number was lift
over a flat median (a much weaker floor) using an unpaired σ (a different, looser
denominator); a lift of 9.46σ over a real $/sqft-by-neighborhood heuristic is the more
honest and more demanding comparison, and the model still clears it decisively. See
`09-report.md` for the full comparison and `BENCHMARKS.md` for how this compares to
Kaggle's known leaderboard characteristics for this exact problem.
