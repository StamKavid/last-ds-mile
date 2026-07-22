# Stage 0 — Problem Framing

## Problem statement

European cardholder transactions over two days in September 2013 (the Kaggle
"Credit Card Fraud Detection" dataset). A transaction-screening tool for a card
issuer: given a transaction's attributes, flag it for additional review before (or
immediately after) authorization.

## Decision this feeds

A fraud-ops screening system uses the model's score to decide whether a transaction
gets held for manual review or a step-up authentication challenge. Today, without
this tool, screening relies on fixed rules (e.g. amount thresholds, velocity checks)
that miss fraud patterns a rule author didn't anticipate. This is a real-time
decision with an asymmetric cost: a missed fraud case (false negative) costs the
average fraud amount plus chargeback/ops overhead; a false alarm (false positive)
costs customer friction and support load, individually far cheaper but far more
frequent if the threshold is set carelessly.

## Unit of analysis and target

One row = one card transaction. Target: `Class` (1 = confirmed fraud, 0 = genuine).
This is a directly-recorded label (confirmed via chargeback, per the dataset's
documentation), not a derived definition — two people given the same raw row would
agree on it identically.

## Do we even need ML?

A fixed-threshold rule on `Amount` alone was checked as the "do we even need ML" test:
fraud transactions have a *lower* median amount ($9.25) than genuine ones ($22.00) in
this data — the opposite of what an amount-threshold rule would assume — so a simple
rule would perform worse than chance on the dimension it relies on. Features `V1-V28`
are already PCA-anonymized (no interpretable raw attribute to hand-write a rule from
even if one wanted to), so a model that can combine 28+ dimensions is justified, not
a default reach for complexity.

## Success metric

**PR-AUC (average precision)** as the primary ranking metric — per
`metric-selection`'s imbalanced-classification row, ROC-AUC stays misleadingly high
under 0.17% fraud because it's dominated by the easy majority-class true-negative
rate; PR-AUC is sensitive to exactly the minority-class performance the decision
actually depends on. ROC-AUC is still reported, but never as the metric used to rank
candidates.

**Business framing:** the real deployment decision is not "rank all transactions,"
it's "pick an operating threshold." `/ds-model` freezes a threshold chosen to
maximize **F2** (recall weighted 2x precision) on validation predictions only —
because missing a fraud case is assumed costlier than one extra false alarm, matching
`metric-selection`'s asymmetric-cost row. The frozen threshold's precision/recall and
resulting count of caught-fraud vs. false-alarms is the number that actually maps to
ops cost, not the threshold-free PR-AUC alone.

## Non-goals

- Not a real-time system architecture (latency, streaming infra) — this benchmark
  covers the modeling decision only.
- Not fraud patterns from outside this 2013, European-cardholder window; a real
  deployment would need continuous retraining as fraud patterns shift.
- Not multi-card-network or non-card payment fraud.
