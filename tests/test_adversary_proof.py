import numpy as np
import pandas as pd

from sealed_bet.adversary import leakage_adversary, split_adversary


def test_split_adversary_catches_an_obviously_distinguishable_held_set():
    # Honeypot: inject a large, deterministic offset into ONE feature, held-only.
    # A Breaker that can't catch THIS is rubber-stamping, not adjudicating.
    rng = np.random.default_rng(0)
    dev = pd.DataFrame({
        "a": rng.normal(size=160),
        "b": rng.normal(size=160),
    })
    held = pd.DataFrame({
        "a": rng.normal(size=40) + 10.0,  # trivially separable offset
        "b": rng.normal(size=40),
    })
    result = split_adversary(dev, held, feature_cols=["a", "b"], seed=0)
    assert result["certified"] is False
    assert result["auc"] > 0.9


def test_split_adversary_clears_a_genuinely_honest_split():
    rng = np.random.default_rng(1)
    dev = pd.DataFrame({
        "a": rng.normal(size=160),
        "b": rng.normal(size=160),
    })
    held = pd.DataFrame({
        "a": rng.normal(size=40),
        "b": rng.normal(size=40),
    })
    result = split_adversary(dev, held, feature_cols=["a", "b"], seed=1)
    assert result["certified"] is True


def test_leakage_adversary_catches_a_direct_target_copy():
    rng = np.random.default_rng(2)
    n = 200
    y = rng.integers(0, 2, size=n)
    df = pd.DataFrame({"copy_of_target": y.astype(float), "y": y})
    findings = leakage_adversary(df, target_col="y", feature_cols=["copy_of_target"],
                                 task="classification", seed=2)
    assert findings[0]["flagged"] is True
    assert findings[0]["solo_score"] > 0.99


def test_leakage_adversary_clears_pure_noise():
    rng = np.random.default_rng(3)
    n = 200
    y = rng.integers(0, 2, size=n)
    df = pd.DataFrame({"pure_noise": rng.normal(size=n), "y": y})
    findings = leakage_adversary(df, target_col="y", feature_cols=["pure_noise"],
                                 task="classification", seed=3)
    assert findings[0]["flagged"] is False
