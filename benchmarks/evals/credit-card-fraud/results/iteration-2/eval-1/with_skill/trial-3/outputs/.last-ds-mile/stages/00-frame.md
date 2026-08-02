# 00 — Problem Framing

## Problem statement

Detect fraudulent credit card transactions in `creditcard.csv` — a well-known
anonymized dataset (284,807 transactions, Sept 2013, European cardholders,
two days of activity). Features `V1`-`V28` are PCA components of the original
transaction attributes (unrecoverable to their original meaning); `Time`
(seconds since first transaction) and `Amount` are the only two features in
their raw form. `Class` is the target (1 = fraud, 0 = genuine).

## Assumptions (no stakeholder available to confirm)

The user did not specify a deployment context, and none is recoverable from
the dataset itself (features are anonymized, no merchant/customer metadata).
I asked to clarify the decision this feeds and the false-positive/false-negative
cost tradeoff; no answer was available, so this is framed as an **exploratory
feasibility assessment**, not a production deployment:

- We report standard imbalanced-classification metrics rather than a
  business-cost-weighted single number.
- We still pick and justify an operating threshold for the confusion matrix,
  but flag it as illustrative, not a business-calibrated decision.
- **Non-goal**: this is not a ready-to-deploy scoring service. Before
  production use, someone needs to supply the actual cost of a missed fraud
  vs. the cost of a false alarm (analyst time or customer friction), which
  would change the threshold (and possibly the metric) chosen in `/ds-evaluate`.

## Unit of analysis

One row = one credit card transaction. Prediction is made per-transaction,
independently (no sequence/session modeling).

## Target definition

`Class == 1`: the transaction was confirmed/labeled fraudulent by the card
issuer's existing process (label provenance is external to this dataset).
`Class == 0`: genuine. Binary, no ambiguous class.

## Decision this feeds (assumed, since unconfirmed)

Illustrative decision: "flag transaction for manual fraud-analyst review"
(rather than "auto-block"), because that is the lower-risk assumption when
the false-positive cost is unknown — blocking real customers outright is a
much more expensive mistake to get wrong by default than adding a review
queue item.

## Do we need ML here?

Yes — fraud is defined by a subtle, non-linear combination of 30 features
with a ~0.17% base rate; no single-rule or simple threshold on `Amount` or
`Time` alone is expected to separate classes (confirmed in `/ds-explore`).

## Success metric

Primary: **PR-AUC (average precision)** — appropriate for severe class
imbalance where ROC-AUC is optimistic and can mask poor precision.
Secondary, reported for interpretability: recall at fixed precision levels,
and a confusion matrix at one illustrative operating threshold.
Non-goal metric: raw accuracy (meaningless at 0.17% fraud prevalence — a
model predicting "genuine" always scores 99.83% accuracy).

## Non-goals

- Not tuning for a specific deployment cost function (no cost data available).
- Not building a real-time scoring pipeline or latency-constrained model.
- Not attempting to de-anonymize or reverse-engineer the PCA features.
