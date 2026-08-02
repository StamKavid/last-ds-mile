# 00 — Problem Frame

## Problem statement
Detect fraudulent credit card transactions from transaction-level data so that
suspicious transactions can be routed to a fraud-ops review queue.

## Assumptions made explicit (no interactive user available to confirm)
The user's request ("build a model to detect fraud and tell me how well it
works") didn't specify how the output is consumed. In an interactive session
I'd press on this before proceeding; here I'm stating the assumptions I'm
using instead of silently picking a metric:

- **Decision / action**: predictions feed a manual fraud-review queue
  (flag-for-review), not an automatic block. This is the safer default — it
  doesn't assume the business is willing to auto-decline legitimate customer
  transactions on model output alone.
- **Cost asymmetry**: a missed fraud (false negative) costs a chargeback/loss
  roughly equal to the transaction amount; a false positive costs analyst
  review time and minor friction. These are **not symmetric** — missed fraud
  is assumed materially worse. This rules out accuracy as a success metric
  (see below) and favors recall-oriented evaluation.
- If these assumptions are wrong (e.g. this is actually powering an
  auto-block decision, or false positives are the bigger concern because
  customer trust is paramount), the metric and threshold choice below should
  be revisited — flag this to the user in the final report.

## Unit of analysis
One row = one card transaction.

## Target definition
`Class` column: `1` = confirmed fraudulent transaction, `0` = genuine
transaction. This is the classic Kaggle "Credit Card Fraud Detection"
dataset (European cardholders, Sept 2013): 284,807 transactions over two
days, `Time` = seconds elapsed since the first transaction in the dataset,
`Amount` = transaction amount, `V1`–`V28` = PCA-transformed features (raw
features unavailable for confidentiality, per dataset documentation) — so no
per-feature information-inventory check is possible on V1–V28 beyond
confirming they're pre-computed per-transaction values, not aggregates that
could reach into the future.

## Information inventory
- **Known at prediction time**: `Time`, `Amount`, `V1`–`V28` — all are
  per-transaction attributes computed from that transaction (and, per the
  dataset's own documentation, PCA components of underlying transaction
  features), not derived from the outcome.
- **Not known at prediction time / must not be used as features**: `Class`
  itself, obviously, and nothing else in this dataset — there are no
  post-outcome fields (e.g. chargeback date, dispute status) present.
- **Caveat**: `Time` is seconds-since-first-transaction, i.e. it encodes row
  order. It's legitimate to use (time-of-day pattern is real fraud signal),
  but the validation split must respect chronological order or at minimum be
  stratified so we're not implicitly leaking future fraud patterns into
  training in a way a real deployment couldn't replicate. Addressed in
  `/ds-validate`.

## Do we even need ML?
Yes. Fraud is a rare, non-linearly-separable pattern across 28+ anonymized
dimensions — no simple rule or lookup table over these PCA components would
approach usable precision/recall. A trivial rule baseline (e.g. flag top
X% by `Amount`) is included in `/ds-baseline` specifically to prove ML is
earning its keep rather than assuming it.

## Success metric
**Primary**: PR-AUC (average precision) on the fraud class. With fraud at
~0.17% of transactions, accuracy and even ROC-AUC are misleading (a
do-nothing classifier scores 99.8% accuracy and can still look decent on
ROC-AUC due to the large true-negative volume) — PR-AUC is sensitive to
exactly the confusion that matters here: false positives among a huge
negative class.

**Secondary / decision-relevant**: recall at a fixed precision operating
point (report the achievable recall at ~50–90% precision, since that's the
range a review queue could realistically sustain), plus a confusion matrix
at the chosen threshold. This ties the modeling metric back to the assumed
decision (review-queue capacity vs. missed-fraud cost) rather than reporting
PR-AUC alone as an abstraction.

## Non-goals
- Not building a real-time scoring pipeline or latency-optimized model.
- Not tuning for an auto-block use case (see assumptions above).
- Not treating `Time` as a forecasting target — this is transaction-level
  classification, not time-series forecasting of future volumes.
- Not attempting to recover the real meaning of `V1`–`V28` (PCA-anonymized
  by the dataset publisher) or engineer domain features on top of them
  beyond what `Time`/`Amount` allow.
