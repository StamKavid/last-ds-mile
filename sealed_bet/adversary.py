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

from sealed_bet.metrics import bootstrap_sigma, lift

CERTIFY_LIFT_THRESHOLD = 2.0  # same language as the ship invariant
LEAKAGE_AUC_THRESHOLD = 0.95
LEAKAGE_R2_THRESHOLD = 0.95


def _cv_folds(minority_count: int) -> int:
    return min(5, max(2, minority_count))


def split_adversary(dev_df: pd.DataFrame, held_features_df: pd.DataFrame,
                    feature_cols: list[str], seed: int = 0) -> dict:
    dev_X = dev_df[feature_cols].to_numpy()
    held_X = held_features_df[feature_cols].to_numpy()
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

    clf = RandomForestClassifier(n_estimators=100, random_state=seed)
    cv = _cv_folds(minority_count)
    proba = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]
    auc = float(roc_auc_score(y, proba))
    sigma = bootstrap_sigma(y, proba, "roc_auc", seed=seed)
    lift_val = lift(auc, 0.5, sigma, greater_is_better=True)
    certified = lift_val <= CERTIFY_LIFT_THRESHOLD
    return {"auc": auc, "sigma": sigma, "lift": lift_val, "certified": certified}


def leakage_adversary(dev_df: pd.DataFrame, target_col: str,
                      feature_cols: list[str], task: str, seed: int = 0) -> list[dict]:
    y = dev_df[target_col].to_numpy()
    if task == "classification":
        counts = np.bincount(y.astype(int))
        minority_count = int(counts[counts > 0].min())
        cv = _cv_folds(minority_count)
    else:
        cv = min(5, max(2, len(y) // 20))

    findings = []
    for col in feature_cols:
        X = dev_df[[col]].to_numpy()
        if task == "classification":
            model = LogisticRegression(max_iter=1000)
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
