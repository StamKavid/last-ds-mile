"""Split a DataFrame into (dev, held) by random / group / time strategy."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def auto_stratify_col(task: str, strategy: str, target: str) -> str | None:
    """The one place that decides whether a split should be stratified.

    Only a random split on a classification target is a candidate: group and
    time splits are ordered/entity-partitioned by design, so stratifying them
    would fight the strategy's own point. Centralized here so seal() and
    run_iteration()'s internal outer split apply the same policy instead of
    each guessing independently -- the exact kind of inconsistency that grew
    into the .last-ds-mile/ vs last-ds-mile-run/ split-path problem elsewhere
    in this project.
    """
    return target if (task == "classification" and strategy == "random") else None


def split(df: pd.DataFrame, strategy: str, seed: int, held_frac: float = 0.2,
          group_key: str | None = None, time_col: str | None = None,
          stratify_col: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into (dev, held) using the given strategy.

    - random: i.i.d. shuffle split; no ordering or grouping guarantee. If
      stratify_col is given, dev/held preserve that column's class
      proportions (see auto_stratify_col) -- without this, a random split on
      an imbalanced classification target can by chance produce a held set
      whose positive rate differs enough from dev's to make the sealed score
      noisier than it needs to be, or (at severe imbalance, e.g. <1% positive)
      leave too few positives in held to score at all.
    - group: dev and held never share a group_key value (no group straddles the
      split boundary).
    - time: held is always strictly chronologically later than dev — every row
      sharing a given time_col value ends up entirely in dev or entirely in
      held, never split across both. Because a tie found straddling the cut
      point is pushed entirely into dev, the actual held fraction may end up
      somewhat smaller than the requested held_frac when ties exist there.
    """
    if stratify_col and strategy != "random":
        raise ValueError(
            f"stratify_col is only supported for strategy='random', not {strategy!r} "
            f"-- group/time splits are already partitioned by entity/chronology, and "
            f"stratifying them would fight that partitioning"
        )
    if strategy == "random":
        stratify = df[stratify_col] if stratify_col else None
        dev, held = train_test_split(df, test_size=held_frac, random_state=seed,
                                     shuffle=True, stratify=stratify)
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
