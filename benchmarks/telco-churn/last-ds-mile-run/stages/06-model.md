# 06 — Modeling

**Gate check:** `04-baseline.md` and `05-validate.md` both exist and were read before
modeling began — confirmed.

Modeling done through the Sealed Bet mechanism (`/ds-seal` → `/ds-auto` → `/ds-open`);
the full experiments table lives in `last-ds-mile-run/LEDGER.md`'s `## Build (auto)`
section (path corrected here — every skill hardcodes `.last-ds-mile/`, which is
`.gitignore`d, so a committed benchmark run has to use a different directory name; see
`BENCHMARKS.md`).

**Re-run note:** this stage was re-run twice after a series of fixes to `sealed_bet`
itself, surfaced by dogfooding this exact benchmark (see `BENCHMARKS.md`): (1) the
Contract's baseline is now the per-`Contract`-type historical churn rate named in
`04-baseline.md`, not a constant 0.5-AUC-by-construction prediction; (2) the ship gate's
σ is now the paired bootstrap difference between the model's and baseline's scores on the
same held rows, not the model's own score variance in isolation; (3) the leakage-adversary
probe, previously dead code, now actually runs; (4) `strategy="random"` on a
classification target now stratifies by `Churn` automatically (see `05-validate.md`) —
this last fix changed the actual dev/held row membership between the second and third
seal of this benchmark, which is why the numbers below differ slightly from an
intermediate re-run, not just AutoGluon's own unseeded search noise. The same five
iteration framings from the original run were reused verbatim across all re-runs.

**Summary:** iteration 1 (all 19 features) won again. The same five subsequent attempts
to resolve the `high_variance` regime (dropping weak categoricals, engineering a
`tenure_bucket` feature) were again all rejected by the Ladder as within the noise
floor — the same pattern seen in the House Prices case (`../house-prices/`), and the
loop again early-stopped after 5 consecutive rejections. Refit on full dev, scored on the
sealed held set: **AUC = 0.8471, baseline (heuristic) = 0.7420, paired σ = 0.0090, lift
= 11.68σ → SHIPPED.** This lift is smaller than the 27.3σ this stage originally
reported — expected and correct, since that number was lift over a constant 0.5-AUC
prediction (a floor that's identical for every classification dataset, not specific to
this one) using an unpaired σ; a lift of 11.68σ over a real per-segment churn-rate
heuristic is the more honest and more demanding comparison, and the model still clears it
decisively. See `09-report.md` and `BENCHMARKS.md`.
