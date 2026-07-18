def test_package_imports():
    import sealed_bet

    assert sealed_bet.__version__ == "0.1.0"


import numpy as np
import pytest

from sealed_bet.metrics import (
    METRICS,
    baseline_predict,
    baseline_score,
    bootstrap_sigma,
    lift,
    paired_bootstrap_sigma,
)


def test_registry_has_rmse_and_roc_auc():
    assert set(["rmse", "roc_auc"]).issubset(METRICS)
    assert METRICS["rmse"].greater_is_better is False
    assert METRICS["roc_auc"].greater_is_better is True


def test_registry_has_auprc():
    assert "auprc" in METRICS
    assert METRICS["auprc"].greater_is_better is True
    assert METRICS["auprc"].baseline_kind == "mean"


def test_auprc_constant_baseline_converges_to_prevalence_not_a_universal_number():
    # Unlike roc_auc's constant baseline (always exactly 0.5), AUPRC's constant
    # baseline is dataset-specific: it converges to the positive-class
    # prevalence. Proving this matters because it means AUPRC's baseline is a
    # real, non-trivial floor even without a heuristic baseline_fn.
    rng = np.random.default_rng(0)
    for pos_rate in (0.02, 0.1, 0.5):
        y_train = (rng.random(3000) < pos_rate).astype(int)
        y_eval = (rng.random(1000) < pos_rate).astype(int)
        base = baseline_score(y_train, y_eval, "auprc")
        assert base == pytest.approx(y_eval.mean(), abs=0.05)


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


def test_bootstrap_sigma_skips_nan_resamples_not_just_valueerror():
    # A tiny minority class makes some bootstrap resamples draw ZERO
    # minority-class rows purely by chance -- roc_auc_score on that resample
    # returns NaN (warns, doesn't raise) rather than raising ValueError.
    # bootstrap_sigma must skip these, not let a single NaN poison the whole
    # sigma estimate.
    rng = np.random.default_rng(0)
    y = np.concatenate([np.zeros(196), np.ones(4)])  # 196/4 split, matches
                                                       # the real bug report
    p = rng.random(200)
    sigma = bootstrap_sigma(y, p, "roc_auc", n=1000, seed=0)
    assert sigma == sigma  # not NaN (NaN != NaN, so this fails if sigma is NaN)
    assert sigma >= 0.0


def test_lift_sign_follows_direction():
    # greater-is-better: model above baseline -> positive lift
    assert lift(0.80, 0.50, 0.10, greater_is_better=True) == pytest.approx(3.0)
    # lower-is-better: model below baseline -> positive lift
    assert lift(0.40, 1.00, 0.20, greater_is_better=False) == pytest.approx(3.0)


def test_baseline_predict_returns_one_value_per_eval_row():
    y_train = np.array([1.0, 2.0, 3.0, 100.0])
    preds = baseline_predict(y_train, n_eval=5, metric_name="rmse")
    assert len(preds) == 5
    assert np.all(preds == 2.5)  # median


def test_roc_auc_constant_baseline_is_always_half_regardless_of_class_balance():
    # The whole reason a real heuristic baseline (seal's baseline_fn) matters:
    # a constant-probability prediction has no ranking power, so its ROC-AUC
    # is exactly 0.5 by construction -- it never actually looks at the data.
    # A "27sigma lift over baseline" for roc_auc is a lift over this floor,
    # not over anything informative.
    rng = np.random.default_rng(0)
    for pos_rate in (0.01, 0.1, 0.265, 0.5, 0.9):
        y_train = (rng.random(2000) < pos_rate).astype(int)
        y_eval = (rng.random(500) < pos_rate).astype(int)
        assert baseline_score(y_train, y_eval, "roc_auc") == pytest.approx(0.5)


def test_paired_bootstrap_sigma_is_tighter_than_unpaired_when_errors_are_shared():
    # When the model and baseline both do worse on the same intrinsically-hard
    # rows, that shared difficulty should cancel out of the paired delta's
    # variance instead of inflating it the way two independent sigmas would.
    rng = np.random.default_rng(0)
    n = 300
    y = rng.normal(size=n)
    hard = rng.random(n) < 0.2  # a subset that's hard for everyone
    noise = np.where(hard, rng.normal(scale=3.0, size=n), rng.normal(scale=0.1, size=n))
    y_pred = y + noise * 0.5  # model: partially tracks the shared hardness
    y_base = y + noise  # baseline: fully tracks the shared hardness

    paired = paired_bootstrap_sigma(y, y_pred, y_base, "rmse", n=500, seed=0)
    model_only = bootstrap_sigma(y, y_pred, "rmse", n=500, seed=0)
    base_only = bootstrap_sigma(y, y_base, "rmse", n=500, seed=0)
    assert paired < model_only + base_only


def test_paired_bootstrap_sigma_rejects_misaligned_lengths():
    with pytest.raises(ValueError, match="aligned"):
        paired_bootstrap_sigma([1, 2, 3], [1, 2, 3], [1, 2], "rmse")


def test_paired_bootstrap_sigma_zero_when_model_equals_baseline():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, size=200)
    p = rng.random(200)
    sigma = paired_bootstrap_sigma(y, p, p, "roc_auc", n=200, seed=0)
    assert sigma == pytest.approx(0.0)
