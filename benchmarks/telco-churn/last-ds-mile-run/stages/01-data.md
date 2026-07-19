# 01 — Data Understanding

**Sanitization gate:** plain CSV via `sklearn.datasets.fetch_openml`, a trusted
first-party fetch mechanism, not an arbitrary download link. No pickled objects. No
hidden-unicode/injected-instruction patterns found in text columns.

**Shape:** 7,043 rows × 20 columns (19 features + `Churn` target). No `customerID`/row
identifier in this OpenML mirror.

**dtypes:** 17 object (categorical), 2 int64 (`SeniorCitizen`, `tenure`), 1 float64
(`MonthlyCharges`) — plus `TotalCharges`, which is `object` dtype despite looking
numeric (see integrity finding below).

**Integrity finding — `TotalCharges` (the real finding of this stage):** stored as a
string column, not numeric. 11 rows contain a literal `' '` (single space) instead of a
number — every one of them has `tenure == 0` (a brand-new customer who hasn't been
billed yet). This isn't missing data to impute; it's a real domain fact (`$0` total
charges for a customer with zero months of tenure), and `/ds-prep` recodes it as such
rather than dropping the rows or imputing a mean.

**Duplicate rows:** 22 fully-identical rows across all 19 feature columns. Checked
before assuming this is a data-quality bug: there is no `customerID` in this dataset
mirror to distinguish otherwise-identical accounts, and with 7,043 rows over
low-cardinality categorical features + coarse-grained `tenure`/charges, some genuine
distinct customers sharing an identical profile is expected, not necessarily a
duplication error. Not dropped — no evidence they're erroneous copies rather than
distinct accounts.

**Class balance:** `Churn` = 26.5% Yes / 73.5% No — real, moderate imbalance (not
extreme), flagged for `/ds-validate` (stratified split) and `/ds-baseline`
(majority-class baseline, not a 50/50 assumption).

**Sanity checks:** `SeniorCitizen` is 0/1 (not a text Yes/No like the other booleans —
noted for `/ds-prep`); `MonthlyCharges` range and `tenure` (0–72 months) are both
domain-plausible for a telecom subscription business.
