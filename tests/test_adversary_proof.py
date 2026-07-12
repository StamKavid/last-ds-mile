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
    # Honest scope: this proves split_adversary isn't a rubber stamp against a
    # gross, easily-separable dev/held difference -- it does not by itself
    # demonstrate sensitivity to subtler structural leaks like a forgotten
    # group/time key (that's a separate, harder claim not tested here).
    assert result["certified"] is False
    assert result["auc"] > 0.9


def test_split_adversary_clears_a_genuinely_honest_split():
    # A single honest split can, by chance, land above the certify threshold
    # ~5% of the time -- that's the inherent floor of a fixed 2-sigma test on
    # a noisy AUC estimate, not a bug (see sealed_bet/adversary.py's
    # CERTIFY_LIFT_THRESHOLD). Verified via seed sweep: a lone trial isn't
    # valid proof of reliability, only the aggregate behavior is. Assert the
    # mechanism clears the honest case in a strong majority of trials.
    n_trials = 30
    certified_count = 0
    for seed in range(n_trials):
        rng = np.random.default_rng(seed)
        dev = pd.DataFrame({
            "a": rng.normal(size=160),
            "b": rng.normal(size=160),
        })
        held = pd.DataFrame({
            "a": rng.normal(size=40),
            "b": rng.normal(size=40),
        })
        result = split_adversary(dev, held, feature_cols=["a", "b"], seed=seed)
        if result["certified"]:
            certified_count += 1
    # ~5% observed false-positive rate on honest splits -> expect roughly
    # 28-30 of 30 trials to certify; require a strong majority, not perfection.
    assert certified_count >= n_trials * 0.85


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
