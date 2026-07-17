# 08 — Interpretation

**Feature importance (permutation, on the held set, refit predictor):**

| Feature | Importance |
|---|---|
| `tenure` | 0.021 |
| `Contract` | 0.019 |
| `InternetService` | 0.014 |
| `OnlineSecurity` | 0.003 |
| `PaperlessBilling` | 0.002 |

**Sanity check against domain expectations:** the top two drivers — how long someone's
been a customer, and what contract they're locked into — are exactly the two strongest
individual patterns already found in `02-explore.md`'s EDA (the tenure-decay curve and
the 15x churn-rate spread across contract types). This consistency between an
independent correlation check (Explore) and a model-internal importance measure
(Explain) is itself a good sign: the model learned the same story a human analyst would
tell, not something opaque.

**No leakage re-check needed:** nothing here approaches the "single feature has
near-perfect importance" Red Flag — the top feature (`tenure`, 0.021) is a modest
fraction of total importance, consistent with a model using many weak-to-moderate
signals together rather than one dominant (and therefore suspicious) one.
