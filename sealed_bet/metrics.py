"""Metric registry, honest baselines, bootstrap noise (σ), and the lift invariant."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import average_precision_score, mean_squared_error, roc_auc_score


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
    "auprc": Metric(
        # Unlike roc_auc, a constant-probability prediction's AUPRC does NOT
        # collapse to a single universal number -- it converges to the
        # positive-class prevalence (a degenerate precision-recall curve at
        # precision=prevalence for all recall), which is itself a real,
        # dataset-specific floor. That makes AUPRC a materially better fit
        # than roc_auc for an imbalanced classification decision (e.g.
        # targeting a rare-positive population), per BENCHMARKS.md's telco
        # finding: the retention team cares about how many of the accounts it
        # spends outreach budget on are genuine churners, which
        # precision-recall captures more directly than ROC-AUC does.
        "auprc", lambda yt, yp: float(average_precision_score(yt, yp)),
        greater_is_better=True, baseline_kind="mean",
    ),
}


def _baseline_constant(y_train: np.ndarray, kind: str) -> float:
    return float(np.median(y_train)) if kind == "median" else float(np.mean(y_train))


def baseline_predict(y_train: np.ndarray, n_eval: int, metric_name: str) -> np.ndarray:
    """The constant-prediction baseline's per-row predictions.

    Callers need the prediction *vector*, not just its score, because
    paired_bootstrap_sigma has to re-score the baseline on each resample
    alongside the model. Note what this means for a ranking metric like
    roc_auc: a constant vector has no ranking, so its AUC is exactly 0.5 on
    every dataset ever. That is a floor worth clearing, but it is not a
    *rival* -- see seal(baseline_fn=...) for scoring the real non-ML
    heuristic a stakeholder would actually use instead of the model.
    """
    m = METRICS[metric_name]
    const = _baseline_constant(np.asarray(y_train), m.baseline_kind)
    return np.full(n_eval, const)


def baseline_score(y_train: np.ndarray, y_eval: np.ndarray, metric_name: str) -> float:
    m = METRICS[metric_name]
    preds = baseline_predict(y_train, len(y_eval), metric_name)
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


def paired_bootstrap_sigma(y_true, y_pred, y_base, metric_name: str,
                           n: int = 1000, seed: int = 0) -> float:
    """σ of the model-minus-baseline *difference*, both re-scored on the same resample.

    This is the denominator the ship gate needs, and it is not the same number
    as bootstrap_sigma(y_true, y_pred, ...). That one is the standard error of
    the model's own score -- the uncertainty in "how good is my model?", which
    answers a question nobody is asking at the gate. The gate asks "is the model
    better than the baseline, or did I get lucky?", and that is a question about
    a *difference between two things measured on the same rows*.

    Scoring both predictors on each shared resample is what makes it paired: when
    the model and the baseline both miss on the same intrinsically-hard rows,
    that shared difficulty cancels out of the delta instead of inflating σ. An
    unpaired σ silently treats the two as independent and gets the width wrong.
    """
    m = METRICS[metric_name]
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    y_base = np.asarray(y_base)
    if not (len(y_true) == len(y_pred) == len(y_base)):
        raise ValueError(
            f"paired_bootstrap_sigma needs aligned arrays, got y_true={len(y_true)}, "
            f"y_pred={len(y_pred)}, y_base={len(y_base)}"
        )
    rng = np.random.default_rng(seed)
    deltas = []
    idx = np.arange(len(y_true))
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        try:
            model_score = m.fn(y_true[s], y_pred[s])
            base_score = m.fn(y_true[s], y_base[s])
        except ValueError:
            continue  # e.g. a resample that drew one class only; skip (as bootstrap_sigma does)
        if model_score != model_score or base_score != base_score:  # NaN check
            continue
        deltas.append(
            (model_score - base_score) if m.greater_is_better else (base_score - model_score)
        )
    return float(np.std(deltas)) if deltas else 0.0


def lift(model_score: float, baseline: float, sigma: float, greater_is_better: bool) -> float:
    if sigma == 0.0:
        return 0.0
    delta = (model_score - baseline) if greater_is_better else (baseline - model_score)
    return float(delta / sigma)
