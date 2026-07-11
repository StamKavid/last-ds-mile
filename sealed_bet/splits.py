"""Split a DataFrame into (dev, held) by random / group / time strategy."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def split(df: pd.DataFrame, strategy: str, seed: int, held_frac: float = 0.2,
          group_key: str | None = None, time_col: str | None = None):
    if strategy == "random":
        dev, held = train_test_split(df, test_size=held_frac, random_state=seed, shuffle=True)
        return dev.reset_index(drop=True), held.reset_index(drop=True)
    if strategy == "group":
        if not group_key:
            raise ValueError("group split requires group_key")
        gss = GroupShuffleSplit(n_splits=1, test_size=held_frac, random_state=seed)
        dev_idx, held_idx = next(gss.split(df, groups=df[group_key]))
        return df.iloc[dev_idx].reset_index(drop=True), df.iloc[held_idx].reset_index(drop=True)
    if strategy == "time":
        if not time_col:
            raise ValueError("time split requires time_col")
        ordered = df.sort_values(time_col).reset_index(drop=True)
        cut = int(len(ordered) * (1 - held_frac))
        return ordered.iloc[:cut].reset_index(drop=True), ordered.iloc[cut:].reset_index(drop=True)
    raise ValueError(f"unknown strategy: {strategy}")
