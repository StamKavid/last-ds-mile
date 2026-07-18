# 04 — Honest Baseline

**Baseline definition (revised):** the real non-ML rival this stage originally only
described in prose — a neighborhood-median $/sqft lookup, computed on dev data alone and
applied to held rows' `GrLivArea` (`benchmarks/house-prices/baseline.py:
neighborhood_price_per_sqft`) — is now the Contract's actual sealed baseline, via
`sealed_bet.seal`'s `--baseline-py` flag. This closes a real gap found while dogfooding
this exact run: `seal()` previously only supported a flat constant (median/mean)
baseline, so the smarter heuristic this stage always named stayed a paragraph of prose
that was never scored, and the ship gate measured lift over a much dumber floor than the
one this stage itself argued for.

**Sealed score:** `baseline_score = 0.2487` (RMSE, log scale) — `baseline_kind:
heuristic` in `contract.json`. For comparison, the flat median-of-training-fold baseline
(the dumbest reasonable prediction, ignoring every feature) scores **RMSE ≈ 0.408** on
this same held set — the heuristic is a materially harder floor, as expected: it uses
two of this dataset's strongest signals (`Neighborhood`, `GrLivArea`) instead of none.

**"Do we even need ML?" check** (from `00-frame.md`): with the heuristic now actually
scored, this check has a real answer instead of an assumed one: $/sqft-by-neighborhood
alone gets to 0.2487, well short of a model's eventual sealed score (see `06-model.md`)
but not a trivial floor either — a plain lookup a human could compute in a spreadsheet
already explains most of the price variance in this market. ML earns its complexity only
by beating this, not by beating the flat median.

**What "beating it" means:** the ship gate is `lift > 2σ`, where σ is now the standard
deviation of the *paired* bootstrap difference between the model's score and this same
heuristic's score on the same held rows (`sealed_bet.metrics.paired_bootstrap_sigma`) —
not the standard error of the model's own score in isolation, which answers a different
question ("how noisy is my model?") than the one the gate is actually asking ("is my
model better than the realistic alternative, or is that noise?").
