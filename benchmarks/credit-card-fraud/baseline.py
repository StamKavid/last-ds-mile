"""A real, non-ML rival for the credit-card-fraud benchmark.

/ds-baseline's discipline: the baseline must be the thing you would actually do
without ML, scored -- not a constant, and not a paragraph of prose that never
gets measured. For this dataset the honest incumbent is a rules engine: a fraud
team with no model flags transactions that look statistically unlike normal
traffic.

V1..V28 are PCA components of the original (undisclosed) features, computed over
predominantly legitimate traffic, so genuine fraud shows up as a multivariate
outlier -- far from the origin in component space. This baseline scores each
held row by its squared Mahalanobis-style distance from the dev set's centre,
using per-component means and standard deviations estimated on DEV ONLY.

Deliberately label-free. It never looks at `Class`, so it is not a weak
supervised model wearing a heuristic's clothes -- it is the unsupervised
anomaly rule a team would ship before anyone trained anything. That also means
it is fit on dev and applied to held with no leakage in either direction.

Expected to land far above AUPRC's constant floor (the positive-class
prevalence, ~0.0017 here) while remaining well below a trained model -- i.e. a
rival worth beating rather than a coin flip.
"""
from __future__ import annotations

import numpy as np

PCA_COLS = [f"V{i}" for i in range(1, 29)]


def anomaly_distance(dev_df, held_features_df):
    """Score held rows by distance from dev's centre in PCA-component space.

    Returns one score per held row, higher = more anomalous = more
    fraud-suspicious. Uses only columns present in both frames, so it keeps
    working when `Time` is excluded from the feature set.
    """
    cols = [c for c in PCA_COLS if c in dev_df.columns and c in held_features_df.columns]
    if not cols:
        raise ValueError(
            "no V1..V28 PCA components found in the dev/held frames — this "
            "baseline is specific to the creditcard.csv schema"
        )

    mu = dev_df[cols].mean()
    sigma = dev_df[cols].std().replace(0.0, 1.0)  # a constant column contributes nothing

    z = (held_features_df[cols] - mu) / sigma
    scores = (z**2).sum(axis=1).to_numpy(dtype=float)

    # seal() rejects non-finite baseline predictions outright, and it is right
    # to: a baseline that cannot produce a real number for some rows has not
    # decided what to do about them. Fall back to the dev-centre distance
    # (i.e. "no evidence of anomaly") rather than silently emitting NaN.
    if not np.all(np.isfinite(scores)):
        scores = np.nan_to_num(scores, nan=0.0, posinf=np.nanmax(scores[np.isfinite(scores)]))
    return scores
