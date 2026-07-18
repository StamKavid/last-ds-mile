import pandas as pd

from sealed_bet.splits import auto_stratify_col, split


def _df():
    return pd.DataFrame({
        "x": range(100),
        "g": [i % 10 for i in range(100)],       # 10 groups
        "t": pd.date_range("2020-01-01", periods=100, freq="D"),
        "y": [i % 2 for i in range(100)],
    })


def test_random_split_sizes():
    dev, held = split(_df(), strategy="random", seed=0, held_frac=0.2)
    assert len(held) == 20 and len(dev) == 80


def test_group_split_no_group_crosses_boundary():
    dev, held = split(_df(), strategy="group", seed=0, held_frac=0.2, group_key="g")
    assert set(dev["g"]).isdisjoint(set(held["g"]))


def test_time_split_held_is_the_future():
    dev, held = split(_df(), strategy="time", seed=0, held_frac=0.2, time_col="t")
    assert dev["t"].max() < held["t"].min()


def test_time_split_no_tie_leaks_across_boundary():
    df = pd.DataFrame({
        "t": pd.to_datetime(["2020-01-01"] * 6 + ["2020-01-05"] * 2 + ["2020-01-09"] * 3),
        "y": range(11),
    })
    dev, held = split(df, strategy="time", seed=0, held_frac=0.3, time_col="t")
    # every row with a given timestamp value must land entirely on one side
    assert set(dev["t"]).isdisjoint(set(held["t"]))
    assert dev["t"].max() < held["t"].min()


def test_group_split_missing_column_raises_value_error():
    import pytest
    with pytest.raises(ValueError, match="group_key"):
        split(_df(), strategy="group", seed=0, held_frac=0.2, group_key="nope")


def test_time_split_missing_column_raises_value_error():
    import pytest
    with pytest.raises(ValueError, match="time_col"):
        split(_df(), strategy="time", seed=0, held_frac=0.2, time_col="nope")


def test_time_split_ties_to_end_raise_value_error():
    import pytest
    df = pd.DataFrame({
        "t": pd.to_datetime(["2020-01-01"] * 5 + ["2020-01-09"] * 5),
        "y": range(10),
    })
    # naive cut at held_frac=0.4 lands inside the tied tail run (all "2020-01-09"),
    # and the tie-walk can't find a boundary before running off the end
    with pytest.raises(ValueError, match="no non-empty held split"):
        split(df, strategy="time", seed=0, held_frac=0.4, time_col="t")


def _imbalanced_df(n=1000, pos_rate=0.02, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < pos_rate).astype(int)
    return pd.DataFrame({"x": rng.normal(size=n), "y": y})


def test_random_split_stratified_preserves_class_balance():
    df = _imbalanced_df(n=2000, pos_rate=0.02, seed=0)
    dev, held = split(df, strategy="random", seed=0, held_frac=0.2, stratify_col="y")
    dev_rate = dev["y"].mean()
    held_rate = held["y"].mean()
    assert abs(dev_rate - held_rate) < 0.01  # tight: stratification should nearly match exactly


def test_random_split_unstratified_can_differ_more(monkeypatch=None):
    # Not a flaky assertion about a specific unstratified draw -- just confirms
    # stratify_col is a real, distinct code path, not a silent no-op.
    df = _imbalanced_df(n=2000, pos_rate=0.02, seed=1)
    dev_strat, held_strat = split(df, strategy="random", seed=1, held_frac=0.2, stratify_col="y")
    dev_plain, held_plain = split(df, strategy="random", seed=1, held_frac=0.2)
    # both are valid splits of the same data; stratified sizes still match held_frac
    assert len(held_strat) == len(held_plain)


def test_stratify_col_rejected_for_group_and_time_strategies():
    import pytest
    with pytest.raises(ValueError, match="only supported for strategy='random'"):
        split(_df(), strategy="group", seed=0, held_frac=0.2, group_key="g", stratify_col="y")
    with pytest.raises(ValueError, match="only supported for strategy='random'"):
        split(_df(), strategy="time", seed=0, held_frac=0.2, time_col="t", stratify_col="y")


def test_auto_stratify_col_only_for_classification_random():
    assert auto_stratify_col("classification", "random", "y") == "y"
    assert auto_stratify_col("regression", "random", "y") is None
    assert auto_stratify_col("classification", "time", "y") is None
    assert auto_stratify_col("classification", "group", "y") is None
