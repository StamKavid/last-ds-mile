# 00 — Problem Framing

## Problem statement

Detect fraudulent credit card transactions in a historical transaction log so that
fraud cases can be distinguished from genuine ones. `creditcard.csv` contains 284,807
transactions made by European cardholders over two days in September 2013.

## Assumptions stated explicitly (no stakeholder available to confirm)

The user's request ("build a model to detect fraud and tell me how well it works")
did not specify a deployment context or cost tradeoff, and the clarifying-question tool
was unavailable this session. Rather than block, I'm proceeding with stated defaults:

- **Decision this feeds**: none specified — treated as a model-quality evaluation
  exercise (this is the standard, well-known Kaggle "Credit Card Fraud Detection"
  dataset, most often used this way), not a live review-queue or auto-block system.
  If this is actually feeding a real decision, the metric below should be revisited.
- **Cost asymmetry**: not quantified. Fraud detection is *typically* asymmetric (a
  missed fraud case usually costs more than a false alarm reviewed and cleared), but
  with no actual $ figures I won't collapse this to one threshold. Reported instead as
  a curve (precision/recall at multiple thresholds) so the tradeoff stays visible
  rather than assumed.

## Unit of analysis

One row = one card transaction. Target: `Class` (1 = fraud, 0 = genuine), already
provided per-transaction — no derivation needed, so no ambiguity about how to compute
it (unlike e.g. "churn" needing a time-window definition).

## Information inventory

All features are transaction-level and available at transaction time — this is not a
forecasting problem and there's no future-value target:

- `Time`: seconds elapsed since the first transaction in the dataset. Usable as a
  transaction-order signal but not a wall-clock feature (no date/day-of-week
  available).
- `V1`–`V28`: PCA-transformed components of the original features, already anonymized
  by the dataset provider. Original meaning is not recoverable; nothing to leak from
  because we don't know what they encode.
- `Amount`: transaction amount, unscaled — known at authorization time in a real
  system.
- `Class`: target, not a feature.

No feature here is a post-outcome artifact (e.g. "chargeback filed" or
"confirmed_fraud_date") — everything is plausibly available before a fraud
determination is made. One caveat: because `V1`-`V28` are opaque PCA outputs, I can't
independently rule out that the anonymization process used any post-hoc information
(e.g., fit PCA on the full dataset including test rows) — flagging this as a limitation
of working with a pre-anonymized public dataset rather than raw features.

## Do we even need ML?

Yes. A simple rule/lookup (e.g. thresholding on `Amount`) is not competitive here —
fraud and genuine transactions overlap heavily on transaction amount alone, and the
whole point of the 28 PCA features is to carry signal that isn't visible in a single
raw field. This is a legitimate case for a classifier.

## Success metric

Given class imbalance (fraud is ~0.17% of transactions), accuracy is not usable — a
model predicting "genuine" for everything scores ~99.8%. Primary metrics:

- **PR-AUC (average precision)** as the headline metric — appropriate for severe
  class imbalance and doesn't reward the majority-class trivial model.
- **ROC-AUC** reported secondarily for comparability with common benchmarks on this
  dataset.
- **Precision/recall at multiple thresholds** (not a single collapsed number) since
  the real operating threshold depends on the unresolved cost tradeoff above.

## Non-goals

- Not a forecasting problem (no future time-index prediction).
- Not optimizing for a specific real-world cost function — no $ costs were provided.
- Not attempting to reverse-engineer or reinterpret the anonymized `V1`–`V28` features.
- Not a real-time/latency-constrained deployment exercise — this is offline model
  evaluation only.
