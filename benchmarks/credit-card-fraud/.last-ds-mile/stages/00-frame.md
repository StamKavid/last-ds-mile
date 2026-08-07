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
`metric-selection`'s imbalanced-classification row.

The reason is *not* that ROC-AUC is inflated by the easy majority class. ROC-AUC is
**invariant to class balance** — TPR and FPR are each computed within a class, so the
578:1 negative-to-positive ratio in this file does not move it at all. That invariance
is the problem: ROC-AUC will look the same here as it would on a balanced dataset,
while the thing the fraud-ops team actually feels — how many genuine transactions get
held for every fraud caught — is driven entirely by the ratio. With 284,315 genuine
transactions and 492 frauds, a small *rate* is a large *count*:

| Operating point | False alarms | Per fraud that exists | Precision ceiling, even at 100% recall |
|---|---|---|---|
| FPR 1.0% | 2,843 | 5.8 | **14.8%** |
| FPR 0.1% | 284 | 0.58 | **63.4%** |

So a model can trace an excellent ROC curve and still swamp the review queue. PR-AUC
uses precision, which moves with that ratio, so it tracks what the decision depends on.
ROC-AUC is still reported, but never as the metric used to rank candidates.

**PR-AUC's own caveat, recorded here so no later stage misreads it:** unlike ROC-AUC it
has *no fixed anchor*. Its no-skill floor is the positive rate, not 0.5 — **0.00173** on
this raw file. Every PR-AUC quoted downstream is a multiple of that floor, and is not
comparable to a PR-AUC from a dataset with a different base rate.

> **The floor moves once, downstream, and that is expected.** `/ds-data` finds 1,081
> exact duplicate rows (19 of them fraud) and `/ds-prep` drops them as a train/test
> contamination control. The modelling set is therefore 283,726 rows at 0.167%, so
> `/ds-baseline` computes the floor as **0.00167** and every later stage compares
> against that. Framing sees the raw file; modelling sees the deduplicated one. Both
> numbers are correct for their stage — see `01-data.md`, `03-prep.md`, `04-baseline.md`.

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
