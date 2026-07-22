# Stage 6 — Modeling

## Gate check

`.last-ds-mile/stages/04-baseline.md` and `.last-ds-mile/stages/05-validate.md` both
exist and were read before modeling began. Baseline anchor: ROC-AUC 0.5, PR-AUC
0.2654. Validation: 5-fold stratified CV, imported from `pipeline_lib.py` and
`model.py`'s `build_cv_splitter`.

## Experiments table

| Model | ROC-AUC | Std | PR-AUC | Std | Train ROC-AUC | Train/Val gap |
|---|---|---|---|---|---|---|
| LogReg (balanced) | 0.8450 | 0.0133 | 0.6555 | 0.0273 | 0.8485 | 0.0035 |
| RandomForest (balanced) | 0.8443 | 0.0124 | 0.6572 | 0.0276 | 0.9057 | 0.0614 |
| LightGBM | 0.8385 | 0.0114 | 0.6509 | 0.0273 | 0.9264 | 0.0879 |
| XGBoost | 0.8426 | 0.0108 | 0.6568 | 0.0252 | 0.9098 | 0.0673 |
| CatBoost (native categorical) | 0.8453 | 0.0095 | 0.6624 | 0.0186 | 0.8842 | 0.0389 |
| **Blend (LogReg + CatBoost-native, 50/50)** | **0.8477** | **0.0113** | **0.6675** | **0.0218** | — | — |

## Bias/variance diagnosis — a clean, textbook result

Unlike house-prices (where train/val gap and fold-to-fold std pointed in different
directions for the linear models), this dataset gives an unambiguous bias/variance
ordering: **LogReg has essentially no train/val gap (0.0035)** — the least flexible
model, correctly the least overfit. **LightGBM has the largest gap (0.0879)** despite
a middling validation score — memorizing training rows without generalizing better
than the more regularized candidates. CatBoost-native sits in between (0.0389) with
the best single-model validation score, the same "least overfit of the nonlinear
candidates" pattern found at house-prices.

## Blend result

Per `model-ensembling`: LogReg and CatBoost were chosen for the blend specifically
because they're maximally different in flexibility (a near-linear decision boundary
vs. a fully nonlinear tree ensemble) — more likely to make different errors than
blending two boosted-tree configs. **Result: 0.8477 ± 0.0113 ROC-AUC, beating every
single component**, including CatBoost-native alone (0.8453). The lift over the best
single component (0.0024) is itself smaller than either component's own std — a
small, not clearly-beyond-noise win, reported as such rather than oversold, same
honesty standard as house-prices' blend.

## Best candidate and lift over baseline

**Blend(LogReg + CatBoost-native)**, ROC-AUC **0.8477 ± 0.0113**.

**Lift over baseline:** 0.8477 − 0.5 = **0.3477**, roughly **30.8x** the candidate's
own fold std — unambiguously real.

**Reference check against published benchmarks** (found via search, not this run):
independently-published kernels on this same dataset report ROC-AUC ≈ 0.84–0.86 for
LogReg/XGBoost, up to ~0.92–0.93 for heavily tuned ensembles. This run's 0.8477 lands
squarely inside the commonly-reported range for a reasonably-tuned single pass —
evidence the pipeline itself is behaving sensibly, not just internally consistent.

## Threshold freezing (classification decision point, per `/ds-model`'s Tier 2 step)

Chosen on OOF validation predictions only, maximizing **F2** (recall weighted 2x
precision, per `/ds-frame`'s stated cost asymmetry):

**Frozen threshold: 0.3338** → precision 0.4466, recall 0.9069, F2 0.7519.

At this threshold: **catches 1695 of 1869 churners (90.7% recall)**, at a cost of
**2100 false alarms** among the ~5174 non-churners (a 40.6% false-positive rate among
loyal customers). This is the number the retention team actually needs: an
aggressive, recall-favoring threshold that catches nearly all at-risk customers but
requires contacting roughly 2.2 customers for every genuine churner caught — a
concrete input to a capacity-planning conversation, not an abstract AUC number.
