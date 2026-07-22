# Stage 3 — Cleaning & Feature Engineering

## Cleaning log

| Change | Why | Alternative considered |
|---|---|---|
| `TotalCharges` blank → 0 for the 11 `tenure==0` rows | Domain fact (0 months × charge = $0), not an unknown — see `01-data.md` | Median imputation — rejected, would fabricate a plausible-looking but wrong value for a case where the true value is known |
| `Contract` ordinal-encoded (`Month-to-month`=0, `One year`=1, `Two year`=2) | `/ds-explore` found a monotonic churn-rate effect by commitment length — one-hot would discard that order | One-hot — rejected for the same reason as house-prices' quality columns: throws away real ordering signal, especially costly for the linear candidate |
| `customerID` dropped | Identifier, not a feature; confirmed unique, carries no signal | None |
| `Churn` mapped Yes/No → 1/0 | Needed as a numeric target for every library used here | None |

## Known-at-prediction-time check

Every remaining feature is a service/account/billing attribute recorded as of the
snapshot date — none is a consequence of the churn event itself (confirmed in
`/ds-explore`, no post-outcome column exists in this dataset).

## Pipeline definition

All fit-requiring transforms (`StandardScaler` for numeric, `OneHotEncoder` for the
remaining un-ordered categoricals) live inside `pipeline_lib.build_preprocessor`,
fit per-fold inside the CV loop in `/ds-model` — never on the full dataset before
splitting.
