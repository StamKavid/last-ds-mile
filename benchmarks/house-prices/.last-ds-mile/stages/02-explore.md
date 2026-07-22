# Stage 2 — Exploratory Data Analysis

## Univariate — target distribution

`SalePrice` is heavily right-skewed (skew = **1.88**) — a handful of expensive homes
stretch the tail. `log1p(SalePrice)` brings skew down to **0.12**, close to symmetric.
**Hypothesis:** the skew is why `/ds-frame` chose the log-space metric, and why every
downstream model should be trained on `logSalePrice` directly rather than raw dollars
— confirmed visually in the figure below.

![Target distribution](../.last-ds-mile/figures/02-target-distribution.png)

## Bivariate — strongest relationships with `log(SalePrice)`

| Feature | Correlation with `log(SalePrice)` |
|---|---|
| OverallQual | **0.82** |
| GrLivArea | 0.70 |
| GarageCars | 0.68 |
| GarageArea | 0.65 |
| TotalBsmtSF | 0.61 |
| 1stFlrSF | 0.60 |
| FullBath | 0.59 |
| YearBuilt | 0.59 |

**Hypothesis:** `OverallQual` (an assessor-rated 1–10 quality score, not leakage —
recorded at the time of listing, before sale) is the single strongest driver, well
ahead of raw size (`GrLivArea`). This makes sense: quality captures finish level and
condition that raw square footage doesn't.

![OverallQual vs log(SalePrice)](../.last-ds-mile/figures/02-top-correlation.png)

**Leakage check on the strongest correlation:** 0.82 is high but not the "near-perfect"
(≥0.95) shape `ds-method`'s Red Flags warn about, and `OverallQual` is assessed at
listing time per `data_description.txt` — known-at-prediction-time, not flagged as a
leakage candidate.

## Collinearity

`TotalBsmtSF` and `1stFlrSF` correlate at **0.82** with each other — for many homes
without a raised layout the first floor sits directly on the basement footprint, so
this is expected structural collinearity, not a data error. Noted for `/ds-prep`: a
tree-based model tolerates this fine; a linear baseline may want one of the two
dropped or combined.

## Hypothesis log

1. **Higher `OverallQual` → higher price**, because it directly summarizes finish and
   condition quality that buyers pay for. Confirmed (r=0.82).
2. **Larger `GrLivArea` → higher price**, the standard size-price relationship.
   Confirmed (r=0.70), weaker than quality — size alone doesn't dominate this market.
3. **Garage capacity (`GarageCars`/`GarageArea`) correlates with price nearly as
   strongly as basement/first-floor size**, likely because garage size is itself a
   proxy for overall home size/quality tier rather than garages being independently
   valuable — worth watching in `/ds-explain`'s feature-importance step for whether
   this holds up once quality and size are both in the model.
4. **`YrSold`/`MoSold` show near-zero raw correlation with price** (`YrSold`: −0.04) —
   consistent with `/ds-data`'s finding of only a mild year-over-year price drift, not
   a strong trend a naive scatter would catch.

## Leakage candidates flagged for `/ds-prep`

None found at this pass — no feature shows near-perfect separation, and the top
correlate (`OverallQual`) is legitimately known before sale. `/ds-prep` should still
re-run the "known at prediction time" check per-feature per its own process, since
EDA correlation alone doesn't rule out subtler leakage (e.g. a derived aggregate).
