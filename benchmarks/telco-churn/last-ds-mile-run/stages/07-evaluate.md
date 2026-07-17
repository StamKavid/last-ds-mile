# 07 — Evaluation & Error Analysis

**Metric confirmed:** ROC-AUC, as chosen in `00-frame.md`. Overall sealed AUC (from
`/ds-open`, `LEDGER.md`): **0.8268**.

**Calibration — genuinely good, worth reporting positively:** predicted-probability
deciles track actual churn rate closely across the full range (e.g. top decile:
mean predicted 0.748 vs. actual 0.716; bottom decile: 0.009 vs. 0.007). A retention team
can read this model's output as an approximate real probability, not just a ranking.

**Slice performance — by `Contract` type (the real finding of this stage):**

| Contract | n | AUC (within-slice) | Churn rate |
|---|---|---|---|
| Month-to-month | 762 | 0.742 | 41.2% |
| Two year | 359 | 0.760 | 2.8% |
| One year | 288 | 0.681 | 15.3% |

Within-slice AUC (0.68–0.76) is notably lower than the overall 0.8268. This is not a
sign the model is broken per-slice — it's the expected consequence of `Contract` itself
being one of the two strongest overall drivers (`02-explore.md`, `08-explain.md`): a
large share of the overall AUC comes from correctly separating month-to-month customers
(who churn a lot) from two-year customers (who almost never do). Once you're already
inside one contract-type slice, that easy signal is gone, and the model's remaining
discriminative power is real but more modest. **Reporting only the overall 0.8268
without this breakdown would overstate how well the model discriminates among otherwise-
similar customers** — exactly the failure mode this stage exists to catch.

**Error analysis:** the hardest slice to separate is `One year` contracts (AUC 0.681,
churn rate 15.3%) — plausibly because one-year customers are a genuine middle ground
(neither the clearly-loyal two-year cohort nor the clearly-flighty month-to-month one),
so the remaining features have to do more work with less clean signal.
