# Stage 3 — Cleaning & Feature Engineering

## Cleaning log

| Change | Why | Alternative considered |
|---|---|---|
| Dropped 1081 exact duplicate rows | Train/test-contamination risk (`target-leakage-detection`) — see `01-data.md` | Keep and rely on the split to rarely separate a duplicate pair by chance — rejected, "rarely" isn't a leakage control |
| Added `LogAmount = log1p(Amount)` | `Amount` skew 16.98 — helps the linear candidate (`LogReg`); a no-op for tree models (monotonic transform) | Leave `Amount` raw for every model — rejected only for the linear candidate's sake, kept `Amount` itself too since trees can still split on the raw scale |
| Added `hour_of_day = (Time % 86400) // 3600` | `/ds-explore` found a real ~10x fraud-rate spike at hour 2 — a genuine signal, not noise | None — this is a fixed, deterministic function of `Time`, not a fit-requiring statistic, so computing it before any split is not a leakage risk |
| Added `day = Time // 86400` | Used for the one-time temporal holdout in `/ds-validate`; also a feature (mild day-to-day drift) | None |

## Known-at-prediction-time check

Every feature (`V1-V28`, `Time`, `Amount`, `LogAmount`, `hour_of_day`, `day`) is
computable from the transaction itself at authorization time — none reaches into the
target or into another row. `hour_of_day` and `day` are both fixed, deterministic
functions of `Time`, not full-dataset aggregates, so they carry no leakage risk
despite being "derived" rather than raw columns.

## Pipeline definition

All fit-requiring transforms (`StandardScaler` for `LogReg`; `OneHotEncoder` — unused
here, no categorical columns exist in this dataset) live inside
`pipeline_lib.build_preprocessor`, fit per-fold inside the CV loop in `/ds-model`,
never on the full dataset before splitting. Deduplication itself is *not* a
fit-requiring statistic (it doesn't compute anything from the data that could vary
by which rows are in a fold) and is safe to do once, globally, in
`engineer_features`.
