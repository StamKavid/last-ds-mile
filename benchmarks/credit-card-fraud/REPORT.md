# Credit Card Fraud — benchmark report

Third benchmark. Dataset: [Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
(ULB Machine Learning Group) — 284,807 transactions over 48 hours, 492 fraudulent
(**0.173%** positive rate), features `V1..V28` (unsupervised PCA components),
plus `Time` and `Amount`.

Run with `benchmarks/credit-card-fraud/run_benchmark.py --time-limit 300`.

## Why this dataset

It was queued to exercise two things built specifically for it: the `auprc`
metric (the dataset's own authors recommend AUPRC over accuracy at this
imbalance) and `auto_stratify_col` (at 0.173% positives, an unstratified split
risks a holdout with too few positives to score). Both worked.

## The framing question, and why the run is doubled

`validation-strategy` and `lessons/the-leaderboard-that-lied.md` both say a
time-ordered dataset must be split on time. `BENCHMARKS.md` separately queued
this dataset to validate stratification, which implies a random split. Those
pull in opposite directions, so the benchmark runs **both**, against the same
data, the same heuristic baseline, and the same model budget.

`Time` is excluded from features in both variants (`--exclude-from-features`).
It is seconds since the first transaction *in this CSV* — the key the time split
is built from, but meaningless at decision time in production. Excluding it from
both means the only thing differing between the variants is the split itself.

## Baseline: a real rival, not a floor

`baseline.py` scores each row by its squared Mahalanobis-style distance from the
dev set's centre in PCA-component space, using dev-only means and standard
deviations. It is **label-free** — the unsupervised anomaly rule a fraud team
ships before anyone trains anything, not a weak supervised model in disguise.

AUPRC's constant-prediction floor here is the positive-class prevalence,
~0.0017. The heuristic scores **0.0518** (time) / **0.1327** (random) — roughly
30–75× the floor. A rival worth beating.

## Results

| variant | sealed AUPRC | baseline | σ (paired) | lift | held rows | held positives |
|---|---|---|---|---|---|---|
| **time** | **0.8158** | 0.0518 | 0.0374 | **20.45σ** | 56,962 | 75 |
| **random** | **0.6882** | 0.1327 | 0.0439 | **12.65σ** | 56,962 | 98 |

Both ship (lift > 2σ). Sealed once each; verdicts in each variant's `LEDGER.md`.

## The hypothesis was wrong

**Predicted:** the random split would inflate the sealed score, by letting the
model see future transactions and learn fraud campaigns that also appear in the
holdout — the-leaderboard-that-lied, reproduced on demand.

**Observed:** `random − time = −0.1275 AUPRC`. The random split scored
*lower*.

The clean confirmation story does not exist, and this report is not going to
manufacture one. What can honestly be said is narrow:

> On this dataset, the random split did not inflate the sealed score.

Anything stronger would be the exact over-reading this project exists to
prevent. Specifically, **this is not a controlled experiment** — the two runs
differ in more than the split strategy:

- **The baseline moved too.** The same anomaly heuristic scores 0.0518 on
  time-held but 0.1327 on random-held — 2.5× higher. The random holdout is
  intrinsically *easier for an anomaly detector*, yet the model did worse on it.
  That is a genuine puzzle this run does not resolve.
- **Different holdout composition:** 75 vs 98 positives; prevalence 0.132% vs
  0.173%. The time holdout is the last 20% of the window, where fraud happens to
  be rarer.
- **Underpowered.** With 75–98 positives and σ ≈ 0.04, the 0.1275 gap is roughly
  3σ. Real, but not enough to attribute a *cause*.
- **Not bit-reproducible.** AutoGluon's internal model search is unseeded (see
  `BENCHMARKS.md`), so a rerun could move these numbers.

A properly controlled version — same holdout rows, same model, only the
*training* data's temporal relationship varying — would be a different and
better experiment. It is not what ran here.

## What the probes said

**split-adversary.** Correctly skipped for the time split (dev and held are
*supposed* to differ there). On the random split: AUC 0.4990, lift −0.76σ,
**CERTIFIED** — dev and held are statistically indistinguishable, exactly as a
stratified random split should be. `auto_stratify_col` did its job.

**leakage-adversary: a false positive worth recording.** Both variants flagged
`⚠ SUSPECT` on `V14` (solo_score 0.9513 / 0.9529, just over the 0.95 threshold),
with V12/V4/V11/V10 close behind.

This is **not** leakage. `V1..V28` are PCA components computed unsupervised over
transaction attributes; they never saw the `Class` label. A single component
solo-predicting fraud at 0.95 AUC is genuine discriminative power in a dataset
whose whole design concentrates signal into a few components.

Read alongside the house-prices finding in `BENCHMARKS.md`, this bounds the
probe from both directions:

| case | probe said | truth |
|---|---|---|
| house-prices `SaleCondition` | CLEAR (R²=0.123) | a real violation — known-at-prediction-time, not statistical |
| fraud `V14` | ⚠ SUSPECT (0.9513) | not a violation — genuine unsupervised signal |

The probe detects *one* thing: a feature that is nearly a copy of the target. It
does not detect timeline violations, and it cannot tell strong legitimate signal
from a leak. Both verdicts need a human reading them, which is why it is
warn-only.

## What this run found in the product

**The split-adversary did not scale, and it blocked the run.** With
`strategy="random"` the seal took **27m38s**; with `strategy="time"`, where the
probe is skipped, the same pipeline took **2m47s**. The AutoGluon fit itself was
~2m46s. A warn-only diagnostic was costing ~10× the model it exists to protect,
with no output and no way to skip — a user on a few-hundred-thousand-row dataset
would reasonably conclude `/ds-seal` had hung.

Cause: `cross_val_predict(RandomForestClassifier(n_estimators=100), cv=5)` over
every row (500 trees on ~228k rows each), then a 1000-resample `roc_auc`
bootstrap over all 284,807.

Fixed via `sealed_bet.adversary.PROBE_MAX_ROWS` (50,000), a seeded stratified
cap. Measured on this dataset's own random split:

| | rows scored | wall clock | AUC | σ | verdict |
|---|---|---|---|---|---|
| before | 284,807 | ~25 min | 0.4990 | 0.0013 | CERTIFIED |
| after | 50,000 | 178 s | 0.4930 | 0.0032 | CERTIFIED |

Same verdict, ~8× faster, and σ honestly widens to reflect the smaller sample.
The cap is written into the Ledger line, so a reader always knows how many rows
a verdict rests on.

## Limitations

- **Model budget was 300s per fit.** AutoGluon fit only LightGBM and LightGBMXT
  in that window on 227,845 rows. These are not maximally-tuned scores and are
  not offered as such.
- **One seal per variant.** No repeated runs, so the between-run variance of
  these numbers is unmeasured.
- Ceiling (0.85 AUPRC) is a human, community-informed estimate of what an
  honest model tops out at here — same convention as the other two benchmarks,
  and deliberately not the public leaderboard.
- The 75-positive time holdout is small. Slice analysis below that is not
  meaningful and was not attempted.
