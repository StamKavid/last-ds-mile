# 05 — Validation Design

## Structural questions

1. **Time dimension?** Yes — `Time` orders transactions, and in real
   deployment a model always scores *future* transactions after training on
   *past* ones. Checked for drift: splitting into 8 equal-count time bins,
   fraud rate ranges 0.09%–0.29% with no monotonic trend (bin-to-bin
   variation looks like noise from small counts, not a real drift pattern —
   see numbers below). Given `01-data.md`'s point that `Time` isn't a real
   wall-clock timestamp (just a 48-hour window), I'm not confident this
   sample has genuine temporal drift to model — but the *possibility* of
   optimistic random-shuffle evaluation is real regardless, so I still use
   a chronological split for the final held-out test set (see below),
   rather than defaulting to shuffled CV just because drift wasn't obvious.

   | Time bin (1/8) | fraud count | fraud rate |
   |---|---|---|
   | 0 (earliest) | 103 | 0.290% |
   | 1 | 74 | 0.209% |
   | 2 | 52 | 0.147% |
   | 3 | 33 | 0.093% |
   | 4 | 83 | 0.234% |
   | 5 | 35 | 0.099% |
   | 6 | 55 | 0.155% |
   | 7 (latest) | 38 | 0.107% |

2. **Groups spanning rows?** No customer/card ID exists in this anonymized
   dataset, so no group-based leakage vector beyond the exact-duplicate rows
   already removed in `/ds-prep`.
3. **Imbalanced target?** Yes, severely (0.167% positive) — every split must
   be stratified where randomization is used, or checked to retain enough
   positives where it isn't (chronological split naturally isn't stratified;
   verified below that it still leaves a usable number of fraud cases).
4. **Fixed test set / known deployment population?** No external test set
   or production population is available to adversarially validate against
   — this dataset is self-contained.

## Chosen strategy

**Outer split — chronological 80/20 holdout**, sorted by `Time`, used as the
final, only-touched-once test set reported in `/ds-evaluate`. This avoids
the "leaderboard that lied" failure mode (`lessons/the-leaderboard-that-lied.md`)
where a shuffled split can look better than a model would actually perform
scored forward in time, even though drift here looks mild.

- Train: rows with earliest 80% of `Time` (226,980 rows, 399 fraud, cut at
  `Time` ≈ 145,234s / 40.3h of the 48h window).
- Test: latest 20% (56,746 rows, 74 fraud) — never used for any fitting,
  scaling, feature selection, or hyperparameter choice.

**Inner loop — stratified 5-fold CV on the training 80% only**, used for
model selection and hyperparameter tuning in `/ds-model`. This is a
deliberate, documented compromise: a fully rigorous approach would nest
forward-chaining (`TimeSeriesSplit`) CV inside the training window too, but
with only ~400 fraud cases in train, chronological inner folds would leave
some early folds with very few positives, adding variance disproportionate
to this being an exploratory (not deployment-calibrated) exercise per
`/ds-frame`. Stratification within the training window keeps every inner
fold's class balance stable for comparing candidate models fairly. The
outer chronological holdout is what protects the final reported number from
this compromise's optimism.

## Split/CV code (reused identically in `/ds-model`)

```python
import pandas as pd
from sklearn.model_selection import StratifiedKFold

df = pd.read_csv("creditcard.csv").drop_duplicates(keep="first")
df = df.sort_values("Time").reset_index(drop=True)

n = len(df)
cut = int(n * 0.8)
train_df, test_df = df.iloc[:cut].copy(), df.iloc[cut:].copy()

X_train, y_train = train_df.drop(columns=["Class"]), train_df["Class"]
X_test, y_test = test_df.drop(columns=["Class"]), test_df["Class"]

inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

## Distribution-shift check

Train (first 80% by time) vs. test (last 20%) fraud rate: 0.176% vs 0.130%
— a modest drop, consistent with the noisy per-bin rates above, not a sharp
regime change. No adversarial-validation classifier was built to
distinguish train vs. test rows beyond this rate comparison, since there's
no external deployment population to validate against (question 4, above)
— the chronological split itself *is* the distribution-shift stress test
here.
