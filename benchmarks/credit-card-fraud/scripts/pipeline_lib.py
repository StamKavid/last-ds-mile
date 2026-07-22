"""Shared feature engineering + preprocessing for the credit-card-fraud benchmark.

Dataset (raw): 284,807 European card transactions over 2 days (Sept 2013), 492
fraud (0.173%) — anonymized via PCA into V1-V28, plus Time (seconds since first
transaction) and Amount. No missing values. 1081 exact duplicate rows found in
/ds-data (19 of the "extra" copies are fraud-labeled) — deduped here, before any
split, per target-leakage-detection's train/test-contamination check: an undeduped
dataset risks the same transaction landing in both a training and a validation
fold. Every script downstream of `prepare_full()` therefore works with the
post-dedup counts, not the raw ones above: 283,726 rows, 473 fraud (0.167%) — the
figures reported everywhere else in this benchmark's stage docs.
"""
import numpy as np
import pandas as pd

TARGET = "Class"


def load_raw(path="creditcard.csv"):
    return pd.read_csv(path)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates().reset_index(drop=True)

    # Amount is heavily right-skewed (skew ~17) — log1p for scale-sensitive models
    # (LogisticRegression); harmless for tree models (monotonic transform).
    df["LogAmount"] = np.log1p(df["Amount"])

    # hour_of_day: /ds-explore found fraud rate spikes to ~10x baseline in the
    # 2am-5am window (low-traffic hours) — a real, usable signal, not just noise.
    df["hour_of_day"] = (df["Time"] % 86400) // 3600

    # day: mild fraud-rate drift between day 0 (0.194%) and day 1 (0.151%) found in
    # /ds-explore — kept as a feature and also used for the one-time temporal holdout
    # in /ds-validate; not itself expected to be a top driver.
    df["day"] = (df["Time"] // 86400).astype(int)

    return df


def get_feature_lists(df: pd.DataFrame):
    exclude = {TARGET}
    numeric = [c for c in df.select_dtypes("number").columns if c not in exclude]
    return numeric, []  # no categorical columns in this dataset


def prepare_full(path="creditcard.csv"):
    df = load_raw(path)
    df = engineer_features(df)
    return df
