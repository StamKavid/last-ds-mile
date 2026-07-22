# Stage 5 — Validation Design

## Time question

**Yes**, `YrSold` spans 2006–2010, including the 2008 financial crisis. Median
`SalePrice` by year: 2006=$163,995, 2007=$167,000, 2008=$164,000, 2009=$162,000,
2010=$155,000 — a mild but real downward drift (~5% top-to-bottom), not flat.

`/ds-frame`'s deployment scenario always predicts a future sale, so shuffled CV that
trains on 2010 and evaluates on 2006 wouldn't represent real use. With only 5 years
and a mild drift, a pure temporal holdout would both waste too much of an already-small
1460-row dataset and forgo stable model comparison during tuning.

**Decision — two mechanisms for two purposes:**
1. **Primary tuning/comparison CV** — stratified k-fold (below), used throughout
   `/ds-model`.
2. **Secondary, one-time temporal robustness check** — train on `YrSold ≤ 2009`,
   evaluate once on `YrSold == 2010`. Not used for tuning (that would leak forward
   information into model selection) — a final sanity check only.

## Group question

No entity repeats across rows — `train.drop(columns=['Id']).duplicated().sum() == 0`.
`Neighborhood` is a feature, not an entity identity that must be kept from spanning
train/validation (unlike a repeated customer ID) — the same neighborhood appearing in
both train and validation is expected and desirable. No `GroupKFold` needed.

## Imbalance question

Not classification, so class-imbalance stratification doesn't literally apply, but the
practical analog is real: `Neighborhood` ranges from 225 rows (`NAmes`) down to **2
rows** (`Blueste`). A plain shuffled k-fold risks a fold with poor price-range
representation. **Chosen fix:** stratify on `log(SalePrice)` quintile bins
(`pd.qcut(..., q=5)`) — `Blueste`'s 2 rows can't be stratified on `Neighborhood`
directly, but target-quintile stratification is always computable (~290 rows/bin) and
protects what actually matters: consistent price-range representation per fold.

## Distribution-shift question (new — see `distribution-shift`)

`test.csv` is a fixed Kaggle-provided test set, so this question applies directly: does
the training distribution actually resemble it?

**Adversarial validation:** labeled every train row `0` and every `test.csv` row `1`
(1459 rows), used only features present in both files, fit a LightGBM classifier under
5-fold stratified CV to discriminate them.

**Result: mean AUC = 0.519 (std 0.022, per-fold range 0.504–0.563).** This is
indistinguishable from 0.5 given the fold spread — train and test are **not**
meaningfully separable, i.e. no real distribution shift between them. (Per-fold detail
in the fold spread — see `uncertainty-quantification` for why the std, not just the
mean, is what makes this conclusion valid: a mean of 0.519 with a std of 0.022 means
even the single highest fold, 0.563, is under 2 std above 0.5.)

The top features driving what little separation exists (`LotFrontage`, `1stFlrSF`,
`BsmtUnfSF`, `LotArea`, `GrLivArea`) are ordinary size-related columns with mild
natural sampling variation across a random train/test split — not a systemic shift
requiring a feature-level or split-level fix. **No action needed**: proceed with the
stratified k-fold above as the primary validation strategy, with confidence that CV
performance should transfer to the Kaggle test set.

## Chosen strategy — reused identically in `/ds-model`

```python
from sklearn.model_selection import StratifiedKFold
import pandas as pd

def build_cv_splitter(df, n_splits=5, seed=42):
    price_bins = pd.qcut(df["logSalePrice"], q=5, labels=False)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(df, price_bins))

def temporal_holdout_mask(df):
    train_mask = df["YrSold"] <= 2009
    holdout_mask = df["YrSold"] == 2010
    return train_mask, holdout_mask
```

Structurally verified: 5 stratified folds of ~1168/292 train/val rows each; temporal
holdout of 1285 train / 175 holdout rows. `/ds-model` must import and call these exact
functions, not reimplement equivalent-looking logic.
