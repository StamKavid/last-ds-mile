# Stage 2 — EDA

## Univariate

- `Churn`: 26.5% positive.
- `tenure`: roughly uniform 0–72, not concentrated at either end.
- `TotalCharges`: skewed (long tail toward long-tenure, high-spend accounts).

## Bivariate — target relationship

**Hypothesis: contract type is associated with churn.** Confirmed as an association,
*not* a causal claim: churn rate is **42.7%** for month-to-month, **11.3%** for
one-year, **2.8%** for two-year — a monotonic, large gap, and the reason `Contract`
is ordinal-encoded rather than one-hot in `/ds-prep` (the effect size itself is
monotonic in commitment length, so the encoding should preserve that order).

**Correction (caught on review): the original framing here said "contract
commitment *reduces* churn... confirmed."** That's a causal claim this correlational
comparison cannot confirm. The obvious confound is self-selection: customers who
choose a two-year contract are plausibly already more stable, satisfied, or
price-committed *before* signing — the contract could be a symptom of low churn
propensity, not its cause. This dataset offers no random assignment, natural
experiment, or instrument that would let a causal claim be made here; correctly
stated, this is "predictive of churn," not "a lever that reduces it." If a retention
team acted on the causal misreading by pushing reluctant customers onto longer
contracts, the real effect on their individual churn probability could be far
smaller than this group gap, or zero. See
`lessons/the-contract-that-wasnt-the-cause.md`.

**Hypothesis: internet service type affects churn.** Confirmed: fiber-optic
customers churn at **41.9%** vs. **19.0%** (DSL) and **7.4%** (no internet) — a real,
large gap. Not obviously a leakage-shaped signal (no single feature near-perfectly
separates the target; the strongest single categorical effect, `Contract`, tops out
at 42.7% vs. 2.8%, nowhere near the near-total-separation pattern `ds-method`'s Red
Flags warn about).

**Hypothesis: tenure and monthly charges both matter.** `tenure` correlates at
**−0.35** with churn (longer-tenured customers churn less, the expected direction);
`MonthlyCharges` at **+0.19** (pricier plans churn somewhat more). Both moderate,
neither leakage-shaped.

## Leakage candidates flagged for `/ds-prep`

None found. Every feature is a service/account attribute recorded at (or before) the
snapshot date — none is a downstream consequence of the churn event itself (e.g.
there is no "cancellation_reason" or "days_since_cancellation" column that would only
be populated *after* a customer already churned).
