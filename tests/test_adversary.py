import math

import numpy as np
import pandas as pd
import pytest

from sealed_bet.adversary import split_adversary


def _iid_frames(n_dev=160, n_held=40, seed=0):
    rng = np.random.default_rng(seed)
    dev = pd.DataFrame({
        "a": rng.normal(size=n_dev),
        "b": rng.normal(size=n_dev),
    })
    held = pd.DataFrame({
        "a": rng.normal(size=n_held),
        "b": rng.normal(size=n_held),
    })
    return dev, held


def test_split_adversary_returns_expected_keys():
    dev, held = _iid_frames()
    result = split_adversary(dev, held, feature_cols=["a", "b"], seed=0)
    assert set(["auc", "sigma", "lift", "certified"]).issubset(result)
    assert isinstance(result["certified"], bool)


def test_split_adversary_certifies_honest_iid_split():
    dev, held = _iid_frames(seed=1)
    result = split_adversary(dev, held, feature_cols=["a", "b"], seed=1)
    assert result["certified"] is True
    assert result["auc"] < 0.75  # a genuinely indistinguishable split shouldn't score high


def test_split_adversary_handles_small_held_set_without_nan(tmp_path=None):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(0)
    dev = pd.DataFrame({"a": rng.normal(size=196), "b": rng.normal(size=196)})
    held = pd.DataFrame({"a": rng.normal(size=4), "b": rng.normal(size=4)})
    result = split_adversary(dev, held, feature_cols=["a", "b"], seed=0)
    assert not math.isnan(result["sigma"])
    assert not math.isnan(result["lift"])


def test_split_adversary_raises_on_too_small_held_set():
    rng = np.random.default_rng(0)
    dev = pd.DataFrame({"a": rng.normal(size=50), "b": rng.normal(size=50)})
    held = pd.DataFrame({"a": rng.normal(size=1), "b": rng.normal(size=1)})
    with pytest.raises(ValueError):
        split_adversary(dev, held, feature_cols=["a", "b"], seed=0)


def test_split_adversary_raises_on_too_small_dev_set():
    rng = np.random.default_rng(0)
    dev = pd.DataFrame({"a": rng.normal(size=1), "b": rng.normal(size=1)})
    held = pd.DataFrame({"a": rng.normal(size=100), "b": rng.normal(size=100)})
    with pytest.raises(ValueError, match="dev set has only"):
        split_adversary(dev, held, feature_cols=["a", "b"], seed=0)


from sealed_bet.adversary import leakage_adversary


def test_leakage_adversary_flags_target_derived_feature():
    rng = np.random.default_rng(0)
    n = 200
    y = rng.integers(0, 2, size=n)
    df = pd.DataFrame({
        "noise": rng.normal(size=n),
        "leaky": y.astype(float) + rng.normal(scale=0.01, size=n),  # near-copy of target
        "y": y,
    })
    findings = leakage_adversary(df, target_col="y", feature_cols=["noise", "leaky"],
                                 task="classification", seed=0)
    by_feature = {f["feature"]: f for f in findings}
    assert by_feature["leaky"]["flagged"] is True
    assert by_feature["noise"]["flagged"] is False


def test_leakage_adversary_regression_task():
    rng = np.random.default_rng(1)
    n = 200
    y = rng.normal(size=n)
    df = pd.DataFrame({
        "noise": rng.normal(size=n),
        "leaky": y * 2.0 + rng.normal(scale=0.01, size=n),
        "y": y,
    })
    findings = leakage_adversary(df, target_col="y", feature_cols=["noise", "leaky"],
                                 task="regression", seed=1)
    by_feature = {f["feature"]: f for f in findings}
    assert by_feature["leaky"]["flagged"] is True
    assert by_feature["noise"]["flagged"] is False


def test_leakage_adversary_sizes_cv_by_minority_class_not_total_rows(monkeypatch):
    # Regression test for the exact bug class Task 1 fixed elsewhere in this
    # file: CV folds must be sized from the MINORITY class count, not total
    # row count, or a degenerate fold can silently corrupt results on some
    # sklearn versions. leakage_adversary's aggregate roc_auc_score call
    # doesn't itself go NaN when this is wrong (verified empirically), so we
    # test the mechanism directly -- the actual cv value passed downstream --
    # rather than an indirect symptom that doesn't manifest here.
    import sealed_bet.adversary as adversary_module

    captured_cv = {}
    real_cross_val_predict = adversary_module.cross_val_predict

    def _spy(estimator, X, y, cv=None, **kwargs):
        captured_cv["cv"] = cv
        return real_cross_val_predict(estimator, X, y, cv=cv, **kwargs)

    monkeypatch.setattr(adversary_module, "cross_val_predict", _spy)

    rng = np.random.default_rng(2)
    n = 200
    y = np.concatenate([np.zeros(197), np.ones(3)]).astype(int)
    rng.shuffle(y)
    df = pd.DataFrame({"noise": rng.normal(size=n), "y": y})
    leakage_adversary(df, target_col="y", feature_cols=["noise"],
                      task="classification", seed=2)

    # minority class has 3 members -> _cv_folds(3) == 3, NOT _cv_folds(200) == 5
    assert captured_cv["cv"] == 3


def test_leakage_adversary_raises_on_minority_class_below_two():
    rng = np.random.default_rng(0)
    n = 200
    y = np.zeros(n, dtype=int)
    y[0] = 1  # exactly 1 positive -- the ordinary "rare fraud" scenario
    df = pd.DataFrame({"noise": rng.normal(size=n), "y": y})
    with pytest.raises(ValueError, match="minority class"):
        leakage_adversary(df, target_col="y", feature_cols=["noise"],
                          task="classification", seed=0)


def test_leakage_adversary_raises_on_negative_encoded_labels():
    rng = np.random.default_rng(0)
    n = 200
    y = rng.choice([-1, 1], size=n)
    df = pd.DataFrame({"noise": rng.normal(size=n), "y": y})
    with pytest.raises(ValueError, match="non-negative"):
        leakage_adversary(df, target_col="y", feature_cols=["noise"],
                          task="classification", seed=0)


# --- Regression coverage: both probes used to crash on the first categorical
# column or the first NaN ("could not convert string to float: 'Male'") on
# any realistic tabular dataset -- every real benchmark run in this repo hit
# it. These tests prove the fix on the exact shape of data that broke it,
# not just on the all-numeric, no-missing-values frames above. ---

def _mixed_dtype_frame(n=200, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "num": rng.normal(size=n),
        "num_with_gaps": rng.normal(size=n),
        "cat": rng.choice(["Male", "Female"], size=n),
        "cat_with_gaps": rng.choice(["A", "B", "C"], size=n),
    })
    df.loc[rng.choice(n, size=n // 10, replace=False), "num_with_gaps"] = np.nan
    df.loc[rng.choice(n, size=n // 10, replace=False), "cat_with_gaps"] = np.nan
    return df


def test_split_adversary_handles_categorical_and_missing_columns():
    dev = _mixed_dtype_frame(n=160, seed=0)
    held = _mixed_dtype_frame(n=40, seed=1)
    result = split_adversary(dev, held, feature_cols=list(dev.columns), seed=0)
    assert 0.0 <= result["auc"] <= 1.0


def test_leakage_adversary_handles_categorical_and_missing_columns():
    rng = np.random.default_rng(0)
    n = 200
    y = rng.integers(0, 2, size=n)
    df = _mixed_dtype_frame(n=n, seed=0)
    df["y"] = y
    findings = leakage_adversary(df, target_col="y", feature_cols=list(df.columns[:-1]),
                                 task="classification", seed=0)
    assert len(findings) == 4
    assert all(0.0 <= f["solo_score"] <= 1.0 for f in findings)


def test_leakage_adversary_catches_a_categorical_bijection_a_linear_probe_would_miss():
    # A nominal category that alternates non-monotonically with the target is
    # a real leak (e.g. a status code that happens to be a proxy for the
    # outcome) but its arbitrary ordinal code is not linearly/monotonically
    # related to the target -- this is exactly why categorical columns get a
    # DecisionTree probe instead of Logistic/Linear (see adversary.py).
    n = 400
    codes = np.tile(np.arange(8), n // 8)
    y = (codes % 2)  # alternates 0,1,0,1,... across increasing codes
    df = pd.DataFrame({"leaky_cat": [f"code_{c}" for c in codes], "y": y})
    findings = leakage_adversary(df, target_col="y", feature_cols=["leaky_cat"],
                                 task="classification", seed=0)
    assert findings[0]["flagged"] is True
