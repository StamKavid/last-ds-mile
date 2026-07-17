# 02 — Exploratory Data Analysis

**Univariate — target:** `SalePrice` is right-skewed (skew = 1.88, as expected for a
price variable); `log1p(SalePrice)` is close to symmetric (skew = 0.12), confirming the
log-target choice from `00-frame.md`.

**Bivariate — target relationship (numeric features, by |corr| with `log_saleprice`):**

| Feature | Corr. w/ log(SalePrice) | Hypothesis |
|---|---|---|
| `OverallQual` | 0.82 | Overall material/finish quality rating — expected to dominate; it's a holistic quality score assessors assign, so a strong single-feature correlation here is expected domain signal, not a leakage red flag (unlike a near-1.0 correlation would be). |
| `GrLivArea` | 0.70 | More living area → higher price — textbook driver. |
| `GarageCars` | 0.68 | Garage capacity — likely partly a proxy for overall house size/quality. |
| `GarageArea` | 0.65 | Same signal as `GarageCars` (see collinearity below). |
| `TotalBsmtSF` | 0.61 | Basement size — another size proxy. |
| `1stFlrSF` | 0.60 | First-floor area — same family as `TotalBsmtSF`. |
| `FullBath` | 0.59 | More full bathrooms → higher price. |
| `YearBuilt` | 0.59 | Newer homes command a premium in this market/period. |

**Collinearity flagged:** `GarageCars` vs `GarageArea` (r = 0.88) and `TotalBsmtSF` vs
`1stFlrSF` (r = 0.82) — both pairs are effectively measuring the same underlying "size"
signal twice. Not a leakage concern (both are legitimately known at prediction time —
they describe the house's physical structure, not the sale outcome), but flagged for
`/ds-prep` as a candidate to consolidate or for the model to handle via regularization
rather than treating both as fully independent signals.

**Leakage-candidate check (`ds-method` Red Flag: "near-perfect importance / correlation"):**
No feature exceeds 0.82 correlation with the target — well short of the "too good to be
true" range that would suggest a feature secretly encodes the sale price itself (e.g. an
assessed-value-at-sale-time field). `OverallQual` at 0.82 is domain-plausible (it's a
subjective quality rating, not a price-derived statistic) and is treated as a legitimate
feature, not a leakage candidate.

**Categorical spot-check:** `Neighborhood` (25 categories) shows a wide spread of median
`SalePrice` across neighborhoods (a well-known driver in this market) — flagged as a
feature `/ds-prep` should encode with care (high cardinality; target-encoding it naively
on the full dataset before splitting would leak, per `ds-prep`'s own Red Flag — must be
fit within the pipeline on training folds only).
