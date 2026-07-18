# 07 — Evaluation & Error Analysis

**Metric confirmed:** RMSE of `log1p(SalePrice)` — the same metric from `00-frame.md`,
not substituted. Overall sealed RMSE (from `/ds-open`, `LEDGER.md`): **0.1311** —
reconfirmed within rounding across two re-seals (see `06-model.md`); only the baseline
and σ used to judge it changed meaningfully, not this number (AutoGluon's own internal
model search isn't seeded, per `BENCHMARKS.md`, so a few-thousandths drift between runs
is expected, not a regression).

**Mechanism gap found and closed while re-running this stage:** the slice, calibration,
and error-analysis findings below require the true held-set labels, but
`sealed_bet.score.open_seal()` used to only return an aggregate `{sealed_score,
baseline, sigma, lift, shipped}` dict — never per-row predictions or labels — even
though this exact stage's own `SKILL.md` instructs producing a slice table and
calibration check "on the held set." `open_seal()` now calls a new
`sealed_bet.score.reveal()`, which writes `held/revealed.csv` (the true target plus the
submitted predictions, joinable with the already-readable `held/features.csv` by row
order) as soon as the seal is opened — legitimate because the one-look guarantee has
already been spent by that point; `reveal()` refuses to run before opening. The numbers
below are freshly recomputed from that file, not carried over from the original run.

**Calibration:** not directly applicable in the probabilistic sense (this is a point
regression, not a probability estimate) — the relevant analogue is residual
homoscedasticity, checked via the slice table below.

**Slice performance — by actual price tier (terciles of the held set):**

| Tier | n | Price range | RMSE (log scale) |
|---|---|---|---|
| Low | 97 | $34,900 – $136,500 | **0.1763** |
| Mid | 96 | $137,450 – $190,000 | 0.1017 |
| High | 96 | $190,000 – $611,657 | 0.1001 |

See `figures/07-slice-performance.png` for the same table as a bar chart.

**This is the real finding of this stage, not a clean pass:** the model is meaningfully
worse on cheaper homes (RMSE 0.176, ~73% higher error than the mid tier) than on mid- or
high-priced ones. The overall 0.1311 aggregate hides this — exactly the failure mode
`ds-method`'s "one aggregate metric is enough" Red Flag warns about.

**Error analysis — worst 5 mispredictions**, 4 of 5 in the low-price tier, sharing a
pattern: `IDOTRR` (twice), `Sawyer`, `OldTown` — three of Ames's oldest, lowest-price
neighborhoods — recur among the worst misses (the 5th, a `NAmes` home, falls just inside
the Mid tier). Stable across both re-seals of this benchmark — same neighborhoods, same
order. Hypothesis: for these homes, condition and location-specific idiosyncrasies
(deferred maintenance, lot-specific issues) that aren't well captured by the structural
features (`OverallQual`, `GrLivArea`, etc.) drive price more than they do in mid/high-tier
homes, where size and quality are more uniformly decisive.

**Practical implication for the framed decision** (`00-frame.md`: suggested list price
before a seller sets an asking price): this model's suggested price should be shown with
lower confidence for homes in the low-price tier / older neighborhoods — carried forward
as an explicit limitation in `09-report.md`, not glossed over.
