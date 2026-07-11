def test_package_imports():
    import sealed_bet

    assert sealed_bet.__version__ == "0.1.0"


import numpy as np
import pytest

from sealed_bet.metrics import METRICS, baseline_score, bootstrap_sigma, lift


def test_registry_has_rmse_and_roc_auc():
    assert set(["rmse", "roc_auc"]).issubset(METRICS)
    assert METRICS["rmse"].greater_is_better is False
    assert METRICS["roc_auc"].greater_is_better is True


def test_baseline_regression_uses_median():
    y_train = np.array([1.0, 2.0, 3.0, 100.0])  # median 2.5
    y_eval = np.array([2.0, 3.0])
    # rmse of constant 2.5 vs [2,3] = sqrt(mean([0.25,0.25])) = 0.5
    assert baseline_score(y_train, y_eval, "rmse") == pytest.approx(0.5)


def test_baseline_classification_is_half_auc():
    y_train = np.array([0, 1, 1, 0])
    y_eval = np.array([0, 1, 0, 1])
    # constant probability -> ROC-AUC is exactly 0.5
    assert baseline_score(y_train, y_eval, "roc_auc") == pytest.approx(0.5)


def test_bootstrap_sigma_positive_for_varied_preds():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, size=200)
    p = rng.random(200)
    s = bootstrap_sigma(y, p, "roc_auc", n=200, seed=1)
    assert s > 0.0


def test_lift_sign_follows_direction():
    # greater-is-better: model above baseline -> positive lift
    assert lift(0.80, 0.50, 0.10, greater_is_better=True) == pytest.approx(3.0)
    # lower-is-better: model below baseline -> positive lift
    assert lift(0.40, 1.00, 0.20, greater_is_better=False) == pytest.approx(3.0)
