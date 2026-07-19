"""Adversaries: statistical primitives that try to prove a claim is a lie.

split_adversary() certifies (or refutes) that dev and held rows are drawn from
an indistinguishable distribution -- the split-adversary from the design (a
train-vs-holdout discriminator; Kaggle's "adversarial validation"). A high AUC
means the split-adversary can tell dev and held apart, which usually means the
split leaked a forgotten group/time structure, or the "random" split wasn't
actually random. This never reads target values -- callers must pass only
feature columns.

leakage_adversary() flags features whose solo predictive power is implausibly
high, a signature of target leakage. It only ever touches dev data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from sealed_bet.metrics import bootstrap_sigma, lift

CERTIFY_LIFT_THRESHOLD = 2.0  # same language as the ship invariant
LEAKAGE_AUC_THRESHOLD = 0.95
LEAKAGE_R2_THRESHOLD = 0.95

# Both adversaries are warn-only diagnostics, so their cost must stay well under
# the cost of the model they exist to protect. Before this cap they did not:
# on the 284,807-row credit-card-fraud benchmark, split_adversary ran 5-fold
# cross-validation of a 100-tree RandomForest over every row, then bootstrapped
# roc_auc 1000x over all of them -- 27m38s, against a 2m47s AutoGluon fit. A
# user on a few-hundred-thousand-row dataset would reasonably conclude /ds-seal
# had hung, with no output and no way to skip.
#
# Subsampling is not a compromise here: both probes answer a question about a
# DISTRIBUTION (can dev and held be told apart? does this feature solo-predict
# the target?), and those are answerable to far more precision than the ship
# gate needs from tens of thousands of rows. The cap is recorded in the Ledger
# so a reader always knows how many rows the verdict rests on, rather than the
# subsampling being invisible.
PROBE_MAX_ROWS = 50_000


def _cv_folds(minority_count: int) -> int:
    return min(5, max(2, minority_count))


def _is_categorical(series: pd.Series) -> bool:
    return series.dtype == object or isinstance(series.dtype, pd.CategoricalDtype)


def _encode_numeric(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """Make an arbitrary feature frame safe for a diagnostic sklearn model.

    Both adversaries are throwaway probes, not the model that ships, so a
    simple ordinal-encode + median/mode-impute here isn't a leakage concern
    the way it would be in /ds-prep -- it never touches the target and never
    leaves this function. Real tabular data (Ames' LotFrontage/GarageYrBlt,
    Telco's every categorical column) is almost always a mix of dtypes and
    has real missing values; without this, both probes raise on the first
    string column or first NaN, which is exactly the failure mode this
    exists to fix -- a leakage check that has never once run on a realistic
    dataset isn't a leakage check.

    Ordinal codes are fine for split_adversary's RandomForest (many features,
    many trees, splitting jointly) but NOT for leakage_adversary's per-feature
    linear/logistic probe -- see _onehot_single_column for why that needs a
    different encoding.
    """
    sub = df[cols].copy()
    obj_cols = [c for c in cols if _is_categorical(sub[c])]
    if obj_cols:
        sub[obj_cols] = sub[obj_cols].astype(str)
        enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        sub[obj_cols] = enc.fit_transform(sub[obj_cols])
    sub = sub.apply(lambda s: pd.to_numeric(s, errors="coerce"))
    sub = sub.fillna(sub.median(numeric_only=True))
    return sub.fillna(0.0).to_numpy(dtype=float)


def _onehot_single_column(df: pd.DataFrame, col: str) -> np.ndarray:
    """One-hot encode one categorical column for leakage_adversary's per-feature probe.

    An ordinal code forces an arbitrary total order onto a nominal column, and
    a linear/logistic model can then only see a monotonic relationship along
    that order -- it misses a real leak whose category-to-target mapping
    doesn't happen to sort that way (e.g. a status code that alternates with
    the target). One-hot gives the linear model one coefficient per category,
    i.e. an arbitrary lookup table, so it can represent ANY category-to-target
    mapping regardless of ordering -- proven by
    test_leakage_adversary_catches_a_categorical_bijection_a_linear_probe_would_miss.
    """
    sub = df[[col]].astype(str)
    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return enc.fit_transform(sub)


def _subsample_stratified(X: np.ndarray, y: np.ndarray, max_rows: int,
                          seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Cap rows while preserving each class's share, deterministically.

    Stratified rather than uniform because the dev/held ratio is the thing
    split_adversary is measuring: a uniform sample of a 4:1 split would still
    be roughly 4:1, but a stratified one is exactly 4:1, which keeps the AUC
    comparable across runs with different cap behaviour.
    """
    if len(y) <= max_rows:
        return X, y
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for cls in np.unique(y):
        idx = np.flatnonzero(y == cls)
        # At least 2 per class so cross-validation still has something to fold.
        n = max(2, round(max_rows * len(idx) / len(y)))
        n = min(n, len(idx))
        keep.append(rng.choice(idx, size=n, replace=False))
    sel = np.sort(np.concatenate(keep))
    return X[sel], y[sel]


def split_adversary(dev_df: pd.DataFrame, held_features_df: pd.DataFrame,
                    feature_cols: list[str], seed: int = 0,
                    max_rows: int = PROBE_MAX_ROWS) -> dict:
    combined = _encode_numeric(pd.concat(
        [dev_df[feature_cols], held_features_df[feature_cols]], ignore_index=True
    ), feature_cols)
    dev_X = combined[: len(dev_df)]
    held_X = combined[len(dev_df):]
    minority_count = min(len(dev_X), len(held_X))
    if minority_count < 2:
        offending = "dev" if len(dev_X) < len(held_X) else "held"
        raise ValueError(
            f"split_adversary: {offending} set has only {minority_count} row(s) "
            f"(dev has {len(dev_X)}, held has {len(held_X)}); need at least 2 "
            f"rows in both dev and held to run a stratified cross-validated "
            f"split-adversary"
        )
    X = np.vstack([dev_X, held_X])
    y = np.concatenate([np.zeros(len(dev_X)), np.ones(len(held_X))])
    n_total = len(y)
    X, y = _subsample_stratified(X, y, max_rows, seed)
    # Re-derive after subsampling: the fold count must reflect the rows actually
    # being cross-validated, not the pre-cap population.
    minority_count = int(min(np.sum(y == 0), np.sum(y == 1)))

    clf = RandomForestClassifier(n_estimators=100, random_state=seed)
    cv = _cv_folds(minority_count)
    proba = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]
    auc = float(roc_auc_score(y, proba))
    sigma = bootstrap_sigma(y, proba, "roc_auc", seed=seed)
    lift_val = lift(auc, 0.5, sigma, greater_is_better=True)
    certified = lift_val <= CERTIFY_LIFT_THRESHOLD
    return {"auc": auc, "sigma": sigma, "lift": lift_val, "certified": certified,
            "n_rows": len(y), "n_rows_total": n_total}


def leakage_adversary(dev_df: pd.DataFrame, target_col: str,
                      feature_cols: list[str], task: str, seed: int = 0) -> list[dict]:
    y = dev_df[target_col].to_numpy()
    if task == "classification":
        if np.any(y.astype(int) < 0):
            raise ValueError(
                "leakage_adversary: classification target must be encoded "
                "as non-negative integers (e.g. 0/1), not negative values "
                "like -1/1"
            )
        counts = np.bincount(y.astype(int))
        minority_count = int(counts[counts > 0].min())
        if minority_count < 2:
            raise ValueError(
                f"leakage_adversary: the minority class has only "
                f"{minority_count} row(s); need at least 2 to run a "
                f"stratified cross-validated leakage probe"
            )
        cv = _cv_folds(minority_count)
    else:
        cv = min(5, max(2, len(y) // 20))

    findings = []
    for col in feature_cols:
        X = (_onehot_single_column(dev_df, col) if _is_categorical(dev_df[col])
             else _encode_numeric(dev_df, [col]))
        if task == "classification":
            model = LogisticRegression(max_iter=1000, random_state=seed)
            proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
            score = float(roc_auc_score(y, proba))
            flagged = score > LEAKAGE_AUC_THRESHOLD
        else:
            model = LinearRegression()
            pred = cross_val_predict(model, X, y, cv=cv)
            score = float(r2_score(y, pred))
            flagged = score > LEAKAGE_R2_THRESHOLD
        findings.append({"feature": col, "solo_score": score, "flagged": flagged})
    return findings
