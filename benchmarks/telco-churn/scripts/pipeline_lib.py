"""Shared feature engineering + preprocessing for the telco-churn benchmark.

Dataset: 7043 customers, 21 columns, 26.5% churn. Found in /ds-data: 11 rows have a
blank `TotalCharges` string, all with `tenure=0` — brand-new customers who haven't
been billed yet. The true value is 0 (tenure x MonthlyCharges = 0), not an unknown to
impute by median — filled as a domain fact, not a missing-data guess. 22 duplicate
rows (excluding customerID) exist but with 21 mostly-categorical columns and only
7043 rows, coincidental duplication is expected by chance — not dropped, unlike
credit-card-fraud's duplicates, which had a different, structural explanation
(PCA-anonymization collision risk). Different data, different judgment call, both
stated explicitly rather than pattern-matching the same fix everywhere.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "Churn"

# Contract has a natural order by commitment length — ordinal-encoded rather than
# one-hot, same reasoning as house-prices' quality-scale columns.
CONTRACT_SCALE = {"Month-to-month": 0, "One year": 1, "Two year": 2}


def load_raw(path="WA_Fn-UseC_-Telco-Customer-Churn.csv"):
    return pd.read_csv(path)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    zero_tenure_mask = df["tenure"] == 0
    df.loc[zero_tenure_mask & df["TotalCharges"].isna(), "TotalCharges"] = 0.0
    # Any other genuinely-unknown TotalCharges (none found in this dataset, but
    # don't assume that holds for a re-run on updated data) gets a median fallback.
    df["TotalCharges"] = df["TotalCharges"].fillna(df["TotalCharges"].median())

    df["Contract"] = df["Contract"].map(CONTRACT_SCALE).astype(int)

    df[TARGET] = (df[TARGET] == "Yes").astype(int)

    df = df.drop(columns=["customerID"])

    return df


def get_feature_lists(df: pd.DataFrame):
    exclude = {TARGET}
    numeric = [c for c in df.select_dtypes("number").columns if c not in exclude]
    categorical = [c for c in df.select_dtypes("object").columns if c not in exclude]
    return numeric, categorical


def build_preprocessor(numeric_cols, categorical_cols, rare_min_frequency=10):
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(
            handle_unknown="infrequent_if_exist", min_frequency=rare_min_frequency, sparse_output=False,
        )),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, numeric_cols),
        ("cat", categorical_pipe, categorical_cols),
    ])


def build_preprocessor_native(numeric_cols, categorical_cols):
    """CatBoost's native categorical path — no one-hot, matching house-prices."""
    numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="median"))])
    categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent"))])
    ct = ColumnTransformer([
        ("num", numeric_pipe, numeric_cols),
        ("cat", categorical_pipe, categorical_cols),
    ])
    cat_feature_indices = list(range(len(numeric_cols), len(numeric_cols) + len(categorical_cols)))
    return ct, cat_feature_indices


def prepare_full(path="WA_Fn-UseC_-Telco-Customer-Churn.csv"):
    df = load_raw(path)
    df = engineer_features(df)
    return df
