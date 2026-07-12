import numpy as np
import pandas as pd

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
