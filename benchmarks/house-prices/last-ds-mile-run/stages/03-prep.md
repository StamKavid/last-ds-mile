# 03 — Cleaning & Feature Engineering

**Known-at-prediction-time check (the actual finding of this stage):** `SaleType`,
`SaleCondition`, `MoSold`, `YrSold` all describe *the sale transaction itself* — not the
house. Per `00-frame.md`'s decision framing (a suggested list price shown to a seller
**before** any sale exists), none of these four columns would be known at prediction
time: you can't know whether a sale will be "Partial" (new-construction, sold before
completion) or "Abnorml" (foreclosure/short sale) before a buyer exists. Verified this is
a real, not just theoretical, concern: median `log(SalePrice)` for `SaleCondition=Partial`
is 12.41 vs. 11.98 for `Normal` — a genuine ~1.5x price association, exactly the kind of
signal that would inflate a backtest score without being usable in production. **All four
columns are dropped from the feature set** for this reason — this is the one real
leakage-for-this-specific-decision finding from this run, not a hypothetical example.

**"NA means a real category, not missing" columns** (per `01-data.md`'s integrity
findings and `data_description.txt`): `PoolQC`, `MiscFeature`, `Alley`, `Fence`,
`FireplaceQu`, `GarageType`/`GarageFinish`/`GarageQual`/`GarageCond`,
`BsmtQual`/`BsmtCond`/`BsmtExposure`/`BsmtFinType1`/`BsmtFinType2`, `MasVnrType` — `NaN`
recoded to the explicit string `"None"` (a real category meaning "doesn't have this
feature"), not imputed with a mode/mean, which would fabricate a value for something that
genuinely doesn't exist on that house.

**Genuinely missing (not "NA-means-none") columns:** `LotFrontage` (259 missing),
`MasVnrArea` (8), `GarageYrBlt` (81, all rows with no garage — recoded to 0 alongside the
`GarageType="None"` recode above, consistent with "no garage" rather than "unknown
garage year"), `Electrical` (1). Deliberately **not** hand-imputed with a full-dataset
statistic here (e.g. neighborhood-median `LotFrontage`) — that would be exactly the
"fit a statistic across the whole dataset before splitting" leak `ds-prep`'s Red Flag
warns about. Left as `NaN` and handled by AutoGluon's own per-fold imputation inside
`run_iteration`'s outer-train/outer-val split (verified in Phase C's own test suite that
the outer split happens before any fit) — the fold-safety guarantee lives in the model
step, not a hand-rolled `ColumnTransformer`, since the model step *is* the pipeline here.

**Collinearity** (`GarageCars`/`GarageArea`, `TotalBsmtSF`/`1stFlrSF`, flagged in
`02-explore.md`): left as-is. Both features in each pair are legitimately
known-at-prediction-time; AutoGluon's tree-based learners handle correlated features
without the numerical instability a linear model would have, so there's no leakage or
correctness reason to drop either — only a (non-blocking) interpretability note carried
forward to `08-explain.md`.

**Final feature set:** all columns except `Id`, `SalePrice` (target), `SaleType`,
`SaleCondition` — plus one addition decided in `05-validate.md`: `MoSold`/`YrSold` are
replaced by a single derived `sale_period = YrSold*12 + MoSold`, kept as a feature (a
coarse "current calendar month" signal *is* legitimately known at prediction time, unlike
the sale-outcome fields) and reused as `/ds-validate`'s time-split boundary. 76 features
total. `Id` is not predictive (a row identifier); everything else is a
structural/quality/timing attribute known before a sale exists.

**Target:** `log_saleprice = log1p(SalePrice)`, per `00-frame.md`.
