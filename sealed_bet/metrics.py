"""Metric registry, honest baselines, bootstrap noise (σ), and the lift invariant."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from sklearn.metrics import mean_squared_error, roc_auc_score


@dataclass(frozen=True)
class Metric:
    name: str
    fn: Callable[[np.ndarray, np.ndarray], float]
    greater_is_better: bool
    baseline_kind: str  # "median" (regression) | "mean" (classification)


def _rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


METRICS: dict[str, Metric] = {
    "rmse": Metric("rmse", _rmse, greater_is_better=False, baseline_kind="median"),
    "roc_auc": Metric(
        "roc_auc", lambda yt, yp: float(roc_auc_score(yt, yp)),
        greater_is_better=True, baseline_kind="mean",
    ),
}


def _baseline_constant(y_train: np.ndarray, kind: str) -> float:
    return float(np.median(y_train)) if kind == "median" else float(np.mean(y_train))


def baseline_score(y_train: np.ndarray, y_eval: np.ndarray, metric_name: str) -> float:
    m = METRICS[metric_name]
    const = _baseline_constant(np.asarray(y_train), m.baseline_kind)
    preds = np.full(len(y_eval), const)
    return float(m.fn(np.asarray(y_eval), preds))


def bootstrap_sigma(y_true, y_pred, metric_name: str, n: int = 1000, seed: int = 0) -> float:
    m = METRICS[metric_name]
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rng = np.random.default_rng(seed)
    scores = []
    idx = np.arange(len(y_true))
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        try:
            score = m.fn(y_true[s], y_pred[s])
        except ValueError:
            continue  # e.g. a resample with one class for roc_auc; skip
        if score != score:  # NaN check without importing math; NaN != NaN is always True
            continue  # some sklearn versions warn-and-return-NaN instead of raising; skip
        scores.append(score)
    return float(np.std(scores)) if scores else 0.0


def lift(model_score: float, baseline: float, sigma: float, greater_is_better: bool) -> float:
    if sigma == 0.0:
        return 0.0
    delta = (model_score - baseline) if greater_is_better else (baseline - model_score)
    return float(delta / sigma)
