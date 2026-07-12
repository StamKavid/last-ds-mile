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
    assert not (result["sigma"] != result["sigma"])  # not NaN
    assert not (result["lift"] != result["lift"])  # not NaN


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


def test_leakage_adversary_handles_imbalanced_classification_target():
    # Regression test for the exact bug class Task 1 fixed: an imbalanced
    # binary target must size CV folds from the MINORITY class count, not
    # total row count, or this degenerates into NaN scores on real sklearn
    # versions (they warn-and-return-NaN rather than raise for single-class
    # folds).
    rng = np.random.default_rng(2)
    n = 200
    y = np.concatenate([np.zeros(190), np.ones(10)]).astype(int)
    rng.shuffle(y)
    df = pd.DataFrame({"noise": rng.normal(size=n), "y": y})
    findings = leakage_adversary(df, target_col="y", feature_cols=["noise"],
                                 task="classification", seed=2)
    score = findings[0]["solo_score"]
    assert score == score  # not NaN
