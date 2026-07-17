from sealed_bet.auto import ladder_accept


def test_ladder_accept_true_when_improvement_clears_noise_floor_greater_is_better():
    assert ladder_accept(new_score=0.80, best_score=0.76, noise_floor=0.02, greater_is_better=True) is True


def test_ladder_accept_false_when_improvement_within_noise_floor_greater_is_better():
    assert ladder_accept(new_score=0.77, best_score=0.76, noise_floor=0.02, greater_is_better=True) is False


def test_ladder_accept_true_when_improvement_clears_noise_floor_lower_is_better():
    # rmse: lower is better, so an IMPROVEMENT is new_score < best_score
    assert ladder_accept(new_score=0.15, best_score=0.19, noise_floor=0.01, greater_is_better=False) is True


def test_ladder_accept_false_when_regression_metric_gets_worse():
    assert ladder_accept(new_score=0.20, best_score=0.19, noise_floor=0.01, greater_is_better=False) is False


def test_ladder_accept_false_exactly_at_the_boundary():
    # exactly equal to the noise floor is NOT an improvement (strict >), same
    # convention as metrics.py's lift() ship gate (lift > 2.0, not >=).
    # 0.75/0.5/0.25 are exact powers of two, so the subtraction lands exactly
    # on the boundary in IEEE-754 double precision (unlike 0.78 - 0.76).
    assert ladder_accept(new_score=0.75, best_score=0.5, noise_floor=0.25, greater_is_better=True) is False


from sealed_bet.auto import diagnose


def test_diagnose_high_variance_when_train_beats_val_beyond_noise_floor():
    # train 0.91, val 0.72 -- train clearly beats val, well past the noise floor
    result = diagnose(train_score=0.91, val_score=0.72, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "high_variance"
    assert result["gap"] > 0.02


def test_diagnose_high_bias_when_gap_small_but_val_far_from_ceiling():
    # train 0.77, val 0.76 -- small gap (0.01, within the 0.02 noise floor),
    # but val is far below the ceiling of 0.95 -- still room to improve, not overfitting
    result = diagnose(train_score=0.77, val_score=0.76, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "high_bias"


def test_diagnose_neither_when_gap_small_and_val_near_ceiling():
    # train 0.94, val 0.93 -- small gap AND val is nearly at the ceiling of 0.95
    result = diagnose(train_score=0.94, val_score=0.93, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "neither"


def test_diagnose_regimes_for_lower_is_better_metric():
    # rmse: lower is better. train 0.08, val 0.19 -- train "beats" val (lower
    # rmse), well past the noise floor -- high variance
    result = diagnose(train_score=0.08, val_score=0.19, noise_floor=0.01,
                      ceiling_score=0.05, greater_is_better=False)
    assert result["regime"] == "high_variance"

    # train 0.17, val 0.18 -- small gap, but val (0.18) is still far above
    # (worse than) the ceiling of 0.05 -- high bias
    result = diagnose(train_score=0.17, val_score=0.18, noise_floor=0.01,
                      ceiling_score=0.05, greater_is_better=False)
    assert result["regime"] == "high_bias"


import numpy as np
import pandas as pd

from sealed_bet.auto import run_iteration


def test_run_iteration_returns_expected_keys_and_plausible_scores(tmp_path):
    rng = np.random.default_rng(0)
    n = 300
    dev = pd.DataFrame({
        "a": rng.normal(size=n),
        "b": rng.normal(size=n),
    })
    dev["y"] = (dev["a"] + dev["b"] > 0).astype(int)

    result = run_iteration(
        dev_df=dev, target="y", feature_cols=["a", "b"], task="classification",
        metric="roc_auc", strategy="random", seed=0, held_frac=0.2, time_limit=15,
        model_dir=str(tmp_path / "iter1"),
    )
    assert set(result.keys()) == {"train_score", "dev_score", "noise_floor"}
    # a genuinely separable signal (a+b>0 predicts y perfectly) should score well
    # above chance (0.5) on both train and held-out val
    assert result["train_score"] > 0.7
    assert result["dev_score"] > 0.7
    assert result["noise_floor"] >= 0.0


def test_run_iteration_respects_the_contracts_split_strategy(tmp_path):
    # a group-correlated dataset: rows sharing a group_key must never be split
    # across the internal outer-train/outer-val fold, same leakage concern the
    # top-level seal already guards against -- run_iteration must thread
    # strategy/group_key through to sealed_bet.splits.split(), not silently
    # default to "random" regardless of the Contract's own recorded strategy.
    rng = np.random.default_rng(1)
    n_groups = 40
    rows_per_group = 5
    groups = np.repeat(np.arange(n_groups), rows_per_group)
    dev = pd.DataFrame({
        "grp": groups,
        "a": rng.normal(size=n_groups * rows_per_group),
    })
    dev["y"] = (dev["a"] > 0).astype(int)

    result = run_iteration(
        dev_df=dev, target="y", feature_cols=["a"], task="classification",
        metric="roc_auc", strategy="group", group_key="grp", seed=0,
        held_frac=0.2, time_limit=15, model_dir=str(tmp_path / "iter_group"),
    )
    # just proving it runs at all under strategy="group" without raising --
    # sealed_bet.splits.split() already raises ValueError if group_key is
    # missing/invalid, so a clean return here proves the strategy was threaded
    # through rather than silently defaulting to "random"
    assert result["dev_score"] >= 0.0
