# 05 — Validation Design

## Time dimension check
Yes — `Time` is a genuine chronological order (seconds elapsed across ~48 hours),
not an arbitrary index. A model deployed for fraud detection would train on past
transactions and score future ones, so **a shuffled/stratified random split would be
optimistic**: it lets the model implicitly see patterns from later in the window
while "predicting" earlier transactions, which can't happen in deployment.

**Decision: temporal split.** Sort by `Time`, train on the first 70% (0s–132,928s),
test on the last 30% (132,929s–172,792s). No shuffling, no k-fold across the time
boundary.

## Group check
No customer/card identifier is present in this anonymized dataset, so grouped
CV (e.g. same card in both splits) can't be checked or applied — noted as a
limitation, not skipped by choice.

## Imbalance check
Yes, severe (0.17% fraud). Within the temporal split this can't be "stratified" in
the usual sense (stratification would require shuffling, which is exactly what the
time constraint rules out) — instead this is monitored via the distribution-shift
check below, and reported per-split fraud counts so small-sample variance is visible.

## Distribution-shift check (train period vs test period)
- Train (first 70%): 384 fraud / 199,365 rows = 0.1927%
- Test (last 30%): 108 fraud / 84,361 rows = 0.1280%

Fraud rate drops ~34% (relative) in the later period. This is a real shift, not a
bug — flagging it explicitly rather than assuming train and test are drawn from an
identical distribution. Implication: test-set PR-AUC is evaluated against a
*rarer*-fraud population than the model trained on, which if anything makes the
held-out evaluation a harder, more conservative test — not a source of inflated
metrics. Proceeding on this basis rather than re-shuffling to "fix" the imbalance
mismatch (that would reintroduce the temporal leakage this split is designed to
avoid).

## Split code (reused identically in `/ds-model`)
```python
df = df.sort_values("Time").reset_index(drop=True)
split_idx = int(len(df) * 0.7)
train, test = df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()
```

## Fixed external test set?
No — this is not a Kaggle leaderboard submission with a hidden test set; the split
above is the only evaluation population.
