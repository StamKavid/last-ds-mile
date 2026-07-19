# 03 — Cleaning & Feature Engineering

**`TotalCharges` fix** (per `01-data.md`'s integrity finding): the 11 `tenure == 0` rows
with a literal `' '` string are recoded to `0.0` — a real domain fact (no billing history
yet), not an imputed guess — then the column is cast to numeric. This is fit
independently of any train/val split (it's a fixed, deterministic string→number recode
using the value's own row, not a statistic computed across rows), so there's no
leakage risk in applying it before the split.

**Known-at-prediction-time check:** every remaining column describes the customer's
account/service profile at the snapshot, not an outcome of churning — there is no
"how the customer left" equivalent to House Prices' `SaleCondition` finding here. All 19
features pass the check.

**Target encoding:** `Churn` recoded `Yes → 1`, `No → 0` (required — `sealed_bet`'s
`roc_auc` metric expects a numeric 0/1 target, not a string label).

**`SeniorCitizen`:** already 0/1 int, left as-is (the one feature not stored as a
Yes/No string, unlike every other boolean column — noted so a future pass doesn't
double-encode it).

**Final feature set:** all 19 original feature columns (with `TotalCharges` cleaned to
numeric). No columns dropped — this is a much smaller, cleaner feature space than House
Prices (19 vs. 76), and every one has a plausible, checked reason to stay in.
