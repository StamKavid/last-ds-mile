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
