# Stage 8 — Interpretation

## Revision note

v1 of this stage used `shap.Explainer` wrapping the entire sklearn `Pipeline`
(encode/decode round-trip through an `OrdinalEncoder`, ~30-row background sample) —
the slow, approximate, callable-wrapping path `ds-explain`'s own skill text reserves
for black-box ensembles (AutoGluon, stacked/blended). A single CatBoost model isn't
one of those, so this rerun uses the fast, exact `shap.TreeExplainer` directly on the
native booster instead, and switched the model itself to CatBoost's native categorical
handling (`build_preprocessor_native`, matching the corrected `/ds-model` candidate) —
no one-hot columns to encode/decode around at all.

## Setup

The shipped model is `Blend(LightGBM + CatBoost-native)` per the corrected
`/ds-model` (see `06-model.md`) — a blend can't be explained by a single feature-
importance ranking in the same way a single model can, so this stage explains the
**CatBoost-native component** specifically (the stronger, more interpretable half of
the blend, and the one whose categorical handling changed), refit on an 85/15
stratified-by-quintile dev/held split, separate from the CV folds, purely for stable
interpretation.

**Held-set RMSE (CatBoost-native, this split): 0.1139** — consistent with its CV mean
(see `06-model.md`), so this split is representative, not an easy or hard draw.

Single base learner (not a multi-model ensemble in itself, even though it's one
component of the shipped blend), so `ds-explain`'s base-model cross-check step doesn't
apply to this component individually — noted explicitly rather than skipped silently.

## Permutation feature importance (held set, 15 repeats)

| Feature | Importance (RMSE increase when shuffled) |
|---|---|
| TotalSF | 0.0546 |
| OverallQual | 0.0406 |
| GrLivArea | 0.0132 |
| OverallCond | 0.0091 |
| GarageFinish | 0.0078 |
| TotalBath | 0.0059 |

![Permutation importance](../.last-ds-mile/figures/08-permutation-importance.png)

## SHAP summary (219 held rows, exact `TreeExplainer` — no sampling needed)

| Feature | Mean \|SHAP\| |
|---|---|
| TotalSF | 0.0588 |
| OverallQual | 0.0546 |
| GrLivArea | 0.0315 |
| GarageFinish | 0.0275 |
| OverallCond | 0.0221 |

![SHAP summary](../.last-ds-mile/figures/08-shap-summary.png)

Native categorical columns needed no encode/decode round-trip — `TreeExplainer` reads
CatBoost's own categorical split structure directly, which is both why this is exact
(not approximate, unlike the generic wrapped path) and why it runs on all 219 held
rows in the time the old approach spent on a 60-row sample.

## Sanity check against domain expectations

**Top-5 agreement between the two methods is now exact**: `{TotalSF, OverallQual,
GrLivArea, OverallCond, GarageFinish}` — the same five features, same rank order for
the top 3, in both permutation importance and SHAP. This is tighter agreement than
the v1 one-hot run had (which agreed on 4 of 5, with a mismatch on `TotalBath` vs.
`LotArea`) — a direct, visible benefit of giving CatBoost its categorical columns
natively instead of splitting them into dozens of sparse one-hot indicators that
divide a single real signal across many low-importance columns.

**A new, previously-invisible driver: `GarageFinish`** (Fin/RFn/Unf/None) ranks 4th-5th
by both methods — it never appeared in the v1 top 10 at all. One-hot-encoding this
4-level categorical had split its signal across up to 4 separate dummy columns, each
individually unremarkable; kept as one native categorical, CatBoost (and both
interpretation methods) see it as the single coherent signal it actually is. This is a
concrete illustration of why the review flagged one-hot-encoding CatBoost as a real
methodology bug, not just a style preference.

**Why permutation importance and SHAP magnitudes still don't match exactly, and why
that's expected, not a discrepancy:** `TotalSF`, `GrLivArea`, and `TotalBsmtSF`
correlate at 0.87 and 0.83 respectively (checked directly, see below). Permutation
importance shuffles one feature while leaving its correlated siblings intact, so a
correlated substitute can partially cover for the shuffled feature — this
systematically *understates* importance for any feature with a strong correlate in
the set. SHAP's Shapley-value attribution splits credit more evenly across correlated
features by construction. That's the mechanism behind `GrLivArea` scoring
proportionally higher under SHAP (0.0315, 3rd) than under permutation (0.0132, 3rd but
a much smaller gap over 4th) — not an inconsistency to resolve, an expected property
of the two methods under real collinearity.

```
             TotalSF  GrLivArea  TotalBsmtSF
TotalSF         1.00       0.87         0.83
GrLivArea       0.87       1.00         0.45
TotalBsmtSF     0.83       0.45         1.00
```

**No implausible driver.** No feature dominates in a way that suggests leakage (the
top feature's SHAP share is well under half of total attribution), and no feature
re-check against `/ds-prep`'s known-at-prediction-time list is triggered. Both methods
still agree with `/ds-explore`'s Stage 2 finding that `OverallQual` is one of the two
dominant drivers, alongside total size.
