import pandas as pd

from sealed_bet.splits import split


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
