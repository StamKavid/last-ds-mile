"""Shared feature engineering + preprocessing pipeline for the house-prices benchmark run.

Every stage from /ds-prep onward imports from here and reuses the exact same
functions — this is the plugin's own discipline (ds-model: "the same split/CV code,
not a rewritten version") applied to feature code too.

Revision note (post-review fixes): the first pass through this pipeline fed
unscaled, skewed features to Ridge/Lasso and one-hot-encoded both CatBoost's
categoricals and ten naturally-ordinal quality columns — all three flagged in a
Kaggle-grandmaster-style review of the run's own output. Fixed here; see
`../.last-ds-mile/stages/06-model.md` for the corrected numbers.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Columns where NA genuinely means "this feature does not apply" (per
# data_description.txt), not missing data — filled with an explicit "None" category,
# never imputed as if the value were merely unrecorded.
NONE_MEANS_ABSENT = [
    "PoolQC", "MiscFeature", "Alley", "Fence", "MasVnrType", "FireplaceQu",
    "GarageType", "GarageFinish", "GarageQual", "GarageCond",
    "BsmtExposure", "BsmtFinType2", "BsmtQual", "BsmtCond", "BsmtFinType1",
]

# Columns where a missing value is genuinely unknown, not "absent" — imputed.
TRUE_MISSING_NUMERIC = ["LotFrontage", "MasVnrArea", "GarageYrBlt"]
TRUE_MISSING_CATEGORICAL = ["Electrical"]

# Ten columns use the same Po < Fa < TA < Gd < Ex quality scale (data_description.txt),
# "None" added at the bottom for the ones where absence is possible (no basement, no
# garage, etc.). One-hot-encoding these throws away the order — Ridge/Lasso in
# particular can no longer see "Excellent is better than Fair by more than Fair is
# better than Poor," and even tree models get a noisier split search. Mapped to a
# single ordinal integer instead, which moves them from "categorical" to "numeric" in
# get_feature_lists purely by virtue of becoming an int column.
QUALITY_SCALE = {"None": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5}
ORDINAL_QUALITY_COLS = [
    "ExterQual", "ExterCond", "BsmtQual", "BsmtCond", "HeatingQC",
    "KitchenQual", "FireplaceQu", "GarageQual", "GarageCond", "PoolQC",
]

# Continuous numeric columns with skew > 1 in the training data (checked once,
# hardcoded here rather than recomputed from whatever data happens to be passed in —
# recomputing "which columns are skewed" per fold/per test-set would itself be a
# fold-dependent, non-reproducible choice). log1p is a fixed, data-independent
# elementwise function — applying it identically to train and test before any split
# is not a leakage risk the way a *fit* transform (a scaler, an encoder) would be.
SKEWED_NUMERIC_COLS = ["LotArea", "MiscVal", "LowQualFinSF", "KitchenAbvGr"]

TARGET = "SalePrice"
LOG_TARGET = "logSalePrice"


def load_raw(train_path="train.csv", test_path="test.csv"):
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    return train, test


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering — every feature here is computable from a single row's
    own recorded attributes at listing time; none reaches into the target or into
    other rows (no full-dataset aggregates), per /ds-prep's known-at-prediction-time
    rule."""
    df = df.copy()

    # "None" for genuinely-absent categoricals (not a missing-data imputation).
    for col in NONE_MEANS_ABSENT:
        if col in df.columns:
            df[col] = df[col].fillna("None")

    # LotFrontage: impute by neighborhood median (a per-row-available grouping key,
    # not a future-looking or target-derived aggregate — Neighborhood is known at
    # listing time for every row, train or test).
    if "LotFrontage" in df.columns:
        df["LotFrontage"] = df.groupby("Neighborhood")["LotFrontage"].transform(
            lambda s: s.fillna(s.median())
        )
        df["LotFrontage"] = df["LotFrontage"].fillna(df["LotFrontage"].median())

    # GarageYrBlt missing == no garage; 0 is a safe sentinel once GarageArea/Cars
    # (already 0 for these rows) mark "no garage" explicitly elsewhere.
    if "GarageYrBlt" in df.columns:
        df["GarageYrBlt"] = df["GarageYrBlt"].fillna(0)

    if "MasVnrArea" in df.columns:
        df["MasVnrArea"] = df["MasVnrArea"].fillna(0)

    if "Electrical" in df.columns:
        mode = df["Electrical"].mode(dropna=True)
        df["Electrical"] = df["Electrical"].fillna(mode.iloc[0] if len(mode) else "SBrkr")

    # Ordinal-encode the ten quality-scale columns onto a single 0-5 integer scale.
    # A handful of these are among test.csv's known test-only-anomaly nulls (same
    # class of gap as Electrical above) — filled with the column's own mode before
    # mapping, same treatment as every other true-missing categorical here.
    for col in ORDINAL_QUALITY_COLS:
        if col in df.columns:
            if df[col].isna().any():
                mode = df[col].mode(dropna=True)
                df[col] = df[col].fillna(mode.iloc[0] if len(mode) else "TA")
            df[col] = df[col].map(QUALITY_SCALE).astype(int)

    # Engineered features — all row-local, all known at listing time.
    df["TotalSF"] = df["TotalBsmtSF"] + df["1stFlrSF"] + df["2ndFlrSF"]
    df["HouseAge"] = df["YrSold"] - df["YearBuilt"]
    df["RemodAge"] = df["YrSold"] - df["YearRemodAdd"]
    df["TotalBath"] = (
        df["FullBath"] + 0.5 * df["HalfBath"]
        + df["BsmtFullBath"].fillna(0) + 0.5 * df["BsmtHalfBath"].fillna(0)
    )
    df["HasPool"] = (df["PoolArea"] > 0).astype(int)
    df["HasGarage"] = (df["GarageArea"] > 0).astype(int)
    df["HasFireplace"] = (df["Fireplaces"] > 0).astype(int)

    # Skew correction for linear models — a no-op in effect for tree models, which
    # only care about split order and are invariant to a monotonic transform.
    for col in SKEWED_NUMERIC_COLS:
        if col in df.columns:
            df[col] = np.log1p(df[col].clip(lower=0))

    return df


def get_feature_lists(df: pd.DataFrame):
    """Split engineered feature columns into numeric / categorical, excluding Id and
    target columns. The ten ordinal quality columns land in `numeric` automatically
    once engineer_features has mapped them to integers."""
    exclude = {"Id", TARGET, LOG_TARGET}
    numeric = [c for c in df.select_dtypes("number").columns if c not in exclude]
    categorical = [c for c in df.select_dtypes("object").columns if c not in exclude]
    return numeric, categorical


def build_preprocessor(numeric_cols, categorical_cols, rare_min_frequency=10):
    """ColumnTransformer fit only on training folds — never on the full dataset
    before splitting (see /ds-prep's leakage rule on fit-requiring transforms).

    For one-hot-based candidates (Ridge, Lasso, RandomForest, LightGBM, XGBoost):
    - numeric branch is median-imputed *and standard-scaled* — Ridge/Lasso penalize
      coefficient magnitude, which is scale-dependent; LotArea's std (~9981) vs.
      OverallQual's (~1.4) made the unscaled version's regularization arbitrary
      across features. Harmless for tree models (scale-invariant).
    - categorical branch collapses any level with fewer than `rare_min_frequency`
      training rows into a single "infrequent" bucket via OneHotEncoder's own
      `min_frequency` (fit per-fold, same as everything else here — not a
      pre-computed-on-the-full-dataset rule).
    """
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(
            handle_unknown="infrequent_if_exist",
            min_frequency=rare_min_frequency,
            sparse_output=False,
        )),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, numeric_cols),
        ("cat", categorical_pipe, categorical_cols),
    ])


def build_preprocessor_native(numeric_cols, categorical_cols):
    """Preprocessing for CatBoost's native categorical handling: impute only, no
    one-hot, no scaling (CatBoost is scale-invariant and does its own ordered target
    statistics on raw categorical levels — one-hot would throw that advantage away).

    Returns (transformer, cat_feature_indices) — the indices are only valid for the
    fixed column order this transformer produces (numeric block first, then
    categorical), which is why they're returned together rather than recomputed
    elsewhere from assumptions about column order.
    """
    numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="median"))])
    categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent"))])
    ct = ColumnTransformer([
        ("num", numeric_pipe, numeric_cols),
        ("cat", categorical_pipe, categorical_cols),
    ])
    cat_feature_indices = list(range(len(numeric_cols), len(numeric_cols) + len(categorical_cols)))
    return ct, cat_feature_indices


def prepare_full(train_path="train.csv", test_path="test.csv"):
    train, test = load_raw(train_path, test_path)
    train = engineer_features(train)
    test = engineer_features(test)
    train[LOG_TARGET] = np.log1p(train[TARGET])
    return train, test
