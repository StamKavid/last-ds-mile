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
