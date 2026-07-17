# 04 — Honest Baseline

**Baseline definition:** predict the median `log_saleprice` from the training split for
every held-out row, regardless of the house's features — the dumbest reasonable
prediction for a regression problem, per `ds-baseline`'s Core Process step 1. Scored with
the exact metric from `00-frame.md`: RMSE of `log1p(SalePrice)`.

**Illustrative score** (on a throwaway 80/20 split, seed 0, *not* the actual sealed
dev/held split — that number is computed automatically by `/ds-seal`'s
`baseline_score()`, using this identical median-of-training-fold definition, so it isn't
duplicated by hand here): **RMSE ≈ 0.39** on the log scale. Median prediction ≈ $163,000
for every house, regardless of size, quality, or location.

**"Do we even need ML?" check** (from `00-frame.md`): a slightly smarter non-ML
alternative — $/sqft by neighborhood — would clearly beat the flat median (neighborhood
alone showed real price spread in `02-explore.md`), so this isn't a "no ML needed" case.
But it sets the real bar: a model has to beat *at least* neighborhood-adjusted $/sqft to
be worth the added complexity, not just the flat median. The Sealed Bet's ship gate
(`lift > 2σ` over the flat median) is the harder, more conservative bar actually enforced
end to end — beating it convincingly implies also beating the $/sqft heuristic.

**What "beating it" means:** the sealed model's RMSE on the *actual* held set must be
enough lower than the actual baseline RMSE (computed by `/ds-seal`) to clear `lift > 2σ`
— not merely "a smaller number," which could be noise at this sample size (1460 rows,
~20% held ≈ 290 rows).
