# 08 — Interpretation

**Feature importance (permutation, on the held set, refit predictor):**

| Feature | Importance |
|---|---|
| `GrLivArea` | 0.055 |
| `OverallQual` | 0.046 |
| `TotalBsmtSF` | 0.015 |
| `OverallCond` | 0.013 |
| `YearRemodAdd` | 0.008 |
| `YearBuilt` | 0.008 |
| `Neighborhood` | 0.007 |
| `BsmtFinSF1` | 0.006 |
| `GarageCars` | 0.005 |

**Sanity check against domain expectations:** the top two drivers — living area and
overall quality rating — are exactly what a real-estate professional would name first,
and match `02-explore.md`'s bivariate correlations (`GrLivArea` r=0.70, `OverallQual`
r=0.82) almost feature-for-feature. No single feature dominates implausibly (top
importance is 0.055, not the near-1.0 "one feature explains everything" pattern
`ds-method`'s Red Flag warns about) — nothing here looks like a leaked or proxy feature.

**No re-check needed:** every top-9 feature is a structural/quality/location attribute
already justified as known-at-prediction-time in `03-prep.md` — none of them are the
sale-transaction fields (`SaleType`/`SaleCondition`/`MoSold`/`YrSold`) that were
correctly excluded there. The `Neighborhood` feature's presence at rank 7 is consistent
with `07-evaluate.md`'s slice finding (older/cheaper neighborhoods are harder to price) —
the model has in fact picked up on location as a real signal, it just isn't enough to
fully close the low-tier error gap on its own.
