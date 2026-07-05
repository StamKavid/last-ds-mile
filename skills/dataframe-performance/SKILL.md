---
name: dataframe-performance
description: Decides when pandas is fine and when to reach for Polars, plus core vectorization/dtype/memory techniques either way. Use when a pandas operation is slow, when a dataset is large enough that load/profile/transform time is becoming a bottleneck, or when asked about Polars, vectorization, or memory usage.
---

# dataframe-performance

## Overview

pandas and Polars are not a strict upgrade path — this skill gives a concrete decision
rule for which one fits, plus the vectorization/dtype techniques that matter in
either.

## When to Use

- A pandas operation (load, groupby, join, apply) is noticeably slow, or a dataset no
  longer fits comfortably in memory/time budget.
- Deciding at project start whether to reach for Polars instead of pandas.
- NOT for: choosing a validation strategy or model (see `validation-strategy`,
  `metric-selection`) — this skill is purely about dataframe engine and performance,
  not modeling decisions.

## Core Process

1. Before optimizing, profile: is the bottleneck actually the dataframe library, or
   something else (network I/O, model training, a for-loop in Python)? Don't guess.
2. If it is the dataframe layer, check the decision table below for whether Polars is
   worth the switch, or whether pandas can be fixed in place with vectorization.
3. If switching to Polars, confirm downstream tools accept it directly (scikit-learn,
   XGBoost/LightGBM, Plotly, Altair all do as of 2026 — see Techniques/Patterns) —
   don't assume a conversion-back-to-pandas tax is required.
4. If staying on pandas, apply the vectorization/dtype fixes below before reaching
   for a different tool.

## Techniques/Patterns

### When to reach for Polars vs stay on pandas

| Situation | Recommendation | Why |
|---|---|---|
| Small-to-medium dataset (fits comfortably in memory, loads in seconds), heavy interactive/exploratory use | Stay on pandas | Larger ecosystem familiarity, most tutorials/Stack Overflow answers assume it, no benefit from switching at this scale |
| Large CSV/Parquet loads, big group-bys or joins, a nightly/scheduled pipeline | Switch to Polars | Multi-threaded by default with a lazy-evaluation query optimizer; commonly 3-10x faster on exactly these operations, sometimes more at scale |
| Feature engineering pipeline that's become the bottleneck in `/ds-prep` | Consider Polars for that step specifically | You don't have to convert the whole project — profile, load, and heavy transforms can run in Polars, then hand off a materialized result |
| Fitting a `/ds-model` scikit-learn `Pipeline`/`ColumnTransformer` | Either is fine | scikit-learn accepts Polars input but converts internally to NumPy/SciPy for computation — no native speed win inside sklearn itself, so don't switch dataframe libraries hoping for a training-time speedup |
| Fitting XGBoost or LightGBM directly | Polars works natively | Both accept Polars `DataFrame`/`LazyFrame` directly, no conversion needed |
| Plotting with Plotly or Altair | Either is fine | Both support Polars natively via the Narwhals compatibility layer — no forced conversion to pandas for visualization |

### Vectorization and dtype fixes (apply regardless of library)

| Anti-pattern | Fix |
|---|---|
| `df.apply(lambda row: ..., axis=1)` for a row-wise calculation | Rewrite as a vectorized expression on the columns directly (`df['a'] + df['b']`, `np.where(...)`, or the library's native expression API) |
| Python `for` loop appending to a list, then building a dataframe | Vectorize, or at minimum build the list first and construct the dataframe once — never grow a dataframe row-by-row in a loop |
| Default `object`/generic string dtype for a low-cardinality categorical column | Use `pandas.Categorical` / Polars `Categorical` — cuts memory and speeds up group-bys and joins |
| Loading a `float64` column that only ever holds small integers or a narrow range | Downcast dtype (`int32`, `float32`) after confirming no precision loss — meaningfully reduces memory on large datasets |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Polars is faster, I should just always use it" | Speed isn't the only cost — team familiarity, tutorial availability, and the "Applied DS/Analyst" workflow this plugin targets often favor pandas until a real bottleneck appears. Optimize when it's actually slow, not by default. |
| "I'll optimize by switching libraries before I've even profiled what's slow" | The bottleneck is often not the dataframe library at all (a Python loop, network I/O, an unindexed join) — profile first, per Core Process step 1. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A `/ds-data` or `/ds-prep` step takes minutes on a dataset well under a gigabyte | Usually a vectorization anti-pattern (a Python loop or row-wise `.apply`), not something that needs a different dataframe library at all |

See `ds-method`'s shared Red Flags for the broader discipline this skill supports.

## Verification

- [ ] The actual bottleneck was profiled/identified before choosing a fix, not
      assumed.
- [ ] If Polars was adopted for a step, downstream tools (sklearn/XGBoost/LightGBM/
      Plotly/Altair) were confirmed to accept it directly rather than assuming a
      pandas conversion is required.
- [ ] Any vectorization fix was verified to still produce the same result as the
      original slow version, not just declared faster.
