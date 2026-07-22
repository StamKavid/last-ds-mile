# Stage 1 — Data Understanding

## Sanitization gate

`WA_Fn-UseC_-Telco-Customer-Churn.csv` is a well-known public IBM/Kaggle sample
dataset — provenance documented, no untrusted pickle/joblib loaded. Text columns are
all short, fixed-vocabulary categoricals (`Yes`/`No`/service-tier strings) — scanned
for hidden unicode or injected instructions; none found (unsurprising given the
column-level `unique()` check below shows a small, closed vocabulary per column).

## Data dictionary

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `customerID` | string | Account identifier | Dropped — not a feature, and confirmed unique (0 duplicate IDs) |
| `gender`, `SeniorCitizen`, `Partner`, `Dependents` | categorical/binary | Demographics | `SeniorCitizen` already 0/1 |
| `tenure` | numeric | Months as a customer | 0–72 |
| `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` | categorical | Subscribed services | Several use `"No <service> service"` as a third level, not true missingness |
| `Contract` | categorical, naturally ordinal | `Month-to-month` / `One year` / `Two year` | Ordinal-encoded in `/ds-prep` (see below) |
| `PaperlessBilling`, `PaymentMethod` | categorical | Billing | |
| `MonthlyCharges`, `TotalCharges` | numeric | Billing amounts | `TotalCharges` loaded as `object` — see integrity finding below |
| `Churn` | binary (Yes/No) | Target | |

## Integrity findings

- **`TotalCharges` is stored as a string column, and 11 rows have a blank value**
  (`" "`, not `NaN` — a formatting artifact, not a proper null). All 11 have
  **`tenure == 0`** — brand-new customers who haven't been billed yet. The correct
  value is **0**, a domain fact (`tenure × MonthlyCharges = 0`), not an unknown to
  impute by median. Fixed explicitly in `/ds-prep` rather than silently coerced.
- **No other missing values** anywhere else in the dataset.
- **22 duplicate rows** (identical on every column except `customerID`). With 20
  categorical/binary columns and only 7043 rows, some coincidental duplication is
  expected by chance in a dataset this categorical-heavy — checked and **not
  dropped**, a different call than credit-card-fraud's duplicates (which had a
  structural explanation — PCA-anonymization collision risk on continuous features —
  that doesn't apply here). Stated explicitly so this isn't read as an inconsistency
  with the other benchmark's decision.
- **No implausible values**: `tenure` 0–72 months (plausible), `MonthlyCharges`
  $18.25–$118.75 (plausible), no ages/dates out of range.
- **No secret-looking values.**

## Open questions for the stakeholder

- Over what window was `Churn` measured (a fixed lookback, or "as of dataset
  export")? Not documented in the source; affects how directly this snapshot maps to
  a recurring per-cycle scoring job — noted as an assumption, not resolved here.
