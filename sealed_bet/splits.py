"""Split a DataFrame into (dev, held) by random / group / time strategy."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def split(df: pd.DataFrame, strategy: str, seed: int, held_frac: float = 0.2,
          group_key: str | None = None, time_col: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into (dev, held) using the given strategy.

    - random: i.i.d. shuffle split; no ordering or grouping guarantee.
    - group: dev and held never share a group_key value (no group straddles the
      split boundary).
    - time: held is always strictly chronologically later than dev — every row
      sharing a given time_col value ends up entirely in dev or entirely in
      held, never split across both. Because a tie found straddling the cut
      point is pushed entirely into held, the actual held fraction may end up
      somewhat larger than the requested held_frac when ties exist there.
    """
    if strategy == "random":
        dev, held = train_test_split(df, test_size=held_frac, random_state=seed, shuffle=True)
        return dev.reset_index(drop=True), held.reset_index(drop=True)
    if strategy == "group":
        if not group_key:
            raise ValueError("group split requires group_key")
        if group_key not in df.columns:
            raise ValueError(f"group_key {group_key!r} not found in df columns")
        gss = GroupShuffleSplit(n_splits=1, test_size=held_frac, random_state=seed)
        dev_idx, held_idx = next(gss.split(df, groups=df[group_key]))
        return df.iloc[dev_idx].reset_index(drop=True), df.iloc[held_idx].reset_index(drop=True)
    if strategy == "time":
        if not time_col:
            raise ValueError("time split requires time_col")
        if time_col not in df.columns:
            raise ValueError(f"time_col {time_col!r} not found in df columns")
        ordered = df.sort_values(time_col).reset_index(drop=True)
        n = len(ordered)
        cut = int(n * (1 - held_frac))
        if 0 < cut < n:
            boundary_value = ordered[time_col].iloc[cut - 1]
            while cut < n and ordered[time_col].iloc[cut] == boundary_value:
                cut += 1
            if cut == n:
                raise ValueError(
                    f"time split: every row from the requested cut point onward "
                    f"shares timestamp {boundary_value!r} with the last dev row, "
                    f"so no non-empty held split preserving strict chronological "
                    f"ordering exists"
                )
        return ordered.iloc[:cut].reset_index(drop=True), ordered.iloc[cut:].reset_index(drop=True)
    raise ValueError(f"unknown strategy: {strategy}")
