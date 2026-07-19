# 02 — Exploratory Data Analysis

**Bivariate — target relationship (categorical drivers, churn rate by group):**

| Feature | Group | Churn rate |
|---|---|---|
| `Contract` | Month-to-month | **42.7%** |
| `Contract` | One year | 11.3% |
| `Contract` | Two year | 2.8% |
| `InternetService` | Fiber optic | **41.9%** |
| `InternetService` | DSL | 19.0% |
| `InternetService` | No internet | 7.4% |
| `tenure` (bucketed) | 0–12 months | **47.4%** |
| `tenure` (bucketed) | 48–72 months | 9.5% |

See `figures/02-churn-by-contract.png` and `figures/02-tenure-relationship.png` for the
`Contract` and `tenure` rows as charts — the two strongest, cleanest patterns here.

**Hypothesis log:**
- `Contract` is the single strongest categorical driver found — a 15x spread between
  month-to-month and two-year churn rates. Hypothesis: contract length is a direct proxy
  for switching cost/commitment, so this is a legitimate, expected business driver, not a
  leakage smell (unlike a feature that's *this* predictive with no plausible mechanism
  would be).
- `InternetService=Fiber optic` churning more than DSL is a real, slightly
  counter-intuitive finding worth flagging for the business (`09-report.md`) rather than
  just modeling around it — plausibly a price-sensitivity or service-quality-perception
  effect, not something resolvable from this data alone.
- `tenure` shows a clean, monotonic decay (newer customers churn much more) — the
  single most standard churn pattern, not surprising.

**Leakage-candidate check (`ds-method` Red Flag: "near-perfect separation"):** none of
these rates approach the "too good to be true" range (max spread is 42.7% vs 2.8%, both
still far from 0%/100% separation) — no feature here looks like it secretly encodes the
outcome itself.

**Collinearity flagged:** `MonthlyCharges` and `InternetService`/add-on service columns
(`OnlineSecurity`, `StreamingTV`, etc.) are clearly related (more services → higher
monthly charge) — not a leakage concern (all legitimately known at prediction time), but
noted for `/ds-explain` in case one dominates importance in a way that's hard to
disentangle from the others.
