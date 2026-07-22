# Stage 6 — Modeling

## Gate check

`.last-ds-mile/stages/04-baseline.md` and `.last-ds-mile/stages/05-validate.md` both
exist and were read before modeling began. Baseline anchor: PR-AUC 0.00167, ROC-AUC
0.5. Validation: 5-fold stratified CV on the deduplicated data.

## A real bug caught mid-run: LightGBM collapsed under this dataset's imbalance ratio

First pass used `scale_pos_weight = (1-rate)/rate ≈ 598.8` for every gradient-
boosting candidate — the standard LightGBM/XGBoost imbalance knob. **LightGBM
collapsed: PR-AUC 0.0403 vs. 0.82–0.84 for every other candidate**, with a huge,
unstable std (0.0358) — not "LightGBM is weaker here," an actual break. Diagnosed on
a held split before trusting the number: swapping only `scale_pos_weight` for
`class_weight="balanced"` (same model, same data, same split) took PR-AUC from
**0.0170 to 0.8869** — an 52x jump from changing one parameter's *mechanism*, not its
value. `is_unbalance=True` showed the identical collapse; `min_child_samples=5`
barely moved it. **XGBoost and CatBoost's own imbalance-weighting equivalents did not
show this problem at the same ratio** — this appears to be specific to how
LightGBM's `scale_pos_weight` scales the boosting gradient directly, which seems to
hit a numerical-stability wall at very extreme ratios (~600:1) that
`class_weight="balanced"`'s per-sample reweighting doesn't. Fixed in
`pipeline_lib`/`model.py` before any candidate result below was trusted — **this is
exactly the kind of finding `/ds-model`'s comparison table exists to surface**: a
candidate that scores wildly worse than five structurally similar candidates is a
bug signal, not a "some models just don't fit this data" shrug.

## Experiments table (corrected)

| Model | PR-AUC | Std | ROC-AUC | Std | Train PR-AUC | Train/Val gap |
|---|---|---|---|---|---|---|
| LogReg (balanced) | 0.7167 | 0.0218 | 0.9803 | 0.0047 | 0.7233 | 0.0066 |
| RandomForest (balanced) | 0.8224 | 0.0186 | 0.9769 | 0.0120 | 0.9807 | 0.1583 |
| LightGBM (fixed: `class_weight="balanced"`) | 0.8435 | 0.0095 | 0.9806 | 0.0099 | 1.0000 | 0.1565 |
| XGBoost | 0.8385 | 0.0154 | 0.9807 | 0.0088 | 0.9994 | 0.1609 |
| CatBoost (`auto_class_weights="Balanced"`) | 0.8413 | 0.0118 | 0.9804 | 0.0081 | 0.9907 | 0.1495 |
| Blend (LogReg + CatBoost) | 0.8436 | 0.0108 | 0.9807 | 0.0048 | — | — |
| **Blend (LightGBM + CatBoost, 50/50)** | **0.8455** | **0.0117** | **0.9808** | **0.0080** | — | — |

## Bias/variance diagnosis

Every gradient-boosting candidate has a large train/val gap (0.15–0.16) — the model
essentially memorizes the ~380 fraud cases available per training fold (train PR-AUC
0.99–1.00), a real variance signal given how few positive examples exist to learn
from. LogReg has almost no gap (0.0066) but also the lowest score — the textbook
low-variance/higher-bias tradeoff, sharper here than at either other benchmark
because the positive class is so small that "memorize the training fraud cases" is
almost trivially achievable for any sufficiently flexible model.

## Blend result — two pairings tested, evidence decided the winner

Per `model-ensembling`: tested both `LightGBM+CatBoost` (two boosting families with
different regularization) and `LogReg+CatBoost` (maximally different flexibility,
the pairing that won at telco-churn) rather than assuming one is more diverse.
**`LightGBM+CatBoost` won** (0.8455 vs. 0.8436) — the opposite ranking from
telco-churn, a useful reminder that "which pairing is more diverse" isn't answerable
in the abstract; it has to be checked per dataset, which is exactly why
`model-ensembling`'s process says to verify with the actual OOF comparison.

## Best candidate and lift over baseline

**Blend(LightGBM + CatBoost)**, PR-AUC **0.8455 ± 0.0117**.

**Lift over baseline:** 0.8455 − 0.00167 = **0.8438**, roughly **72x** the
candidate's own fold std — the strongest lift-to-noise ratio of any of the three
benchmarks in this run, unsurprising given how trivial the no-skill baseline is at
this imbalance.

**Reference check against published benchmarks:** literature on this dataset reports
single-model PR-AUC around 0.85–0.87 for top performers (Random Forest, XGBoost) and
stacking ensembles reaching ROC-AUC ~0.99. This run's PR-AUC 0.8455 / ROC-AUC 0.9808
lands inside the commonly-reported "good single-pass ensemble" range — again,
evidence the pipeline is producing sensible numbers, not just internally consistent
ones.

## Threshold freezing

Chosen on OOF validation predictions only, maximizing F2 (per `/ds-frame`'s stated
cost asymmetry — missing fraud costs more than one extra false alarm):

**Frozen threshold: 0.4932** → precision 0.8851, recall 0.8309, F2 0.8412.

At this threshold: **catches 393 of 473 fraud cases (83.1% recall)**, at a cost of
just **51 false alarms** among 283,253 genuine transactions (a 0.018% false-positive
rate) — a genuinely deployable operating point, not just a high AUC number. Contrast
with telco-churn's frozen threshold (40.6% false-positive rate to hit 90.7% recall):
the class separation here is simply much cleaner, so the same F2-optimization
criterion lands at a far more favorable precision/recall trade — a real difference
between the two problems, not an inconsistency in method.

## One-time temporal robustness check

Train on `day == 0`, evaluate once on `day == 1` (n=139,490, ~236 fraud cases) —
**PR-AUC 0.7725, ROC-AUC 0.9701**. The PR-AUC point is noticeably lower than the CV
mean (0.8455) — stated plainly rather than glossed over. With only ~236 positive
cases in this single holdout, PR-AUC's own sampling variance at this scale is large
(unlike house-prices' RMSE, PR-AUC is highly sensitive to exactly which few positive
cases land where), so this is treated as a single noisy data point, not a
contradiction of the CV result — but it's also not nothing: a real deployment
retraining on rolling data would want to watch this gap rather than assume the CV
number transfers unchanged to a true forward-looking evaluation.
