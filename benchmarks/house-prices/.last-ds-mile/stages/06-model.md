# Stage 6 — Modeling

## Revision note

v1 of this stage had three real bugs, caught in a Kaggle-competitive review of this
run's own output: Ridge/Lasso were fed unscaled, skewed features; CatBoost was
one-hot-encoded instead of given native categorical handling; no ensembling or
bias/variance diagnosis was attempted despite both being flagged as package-level
gaps in the same review. All fixed below — this is a full rerun against the corrected
`pipeline_lib.py`, not a patch to the old numbers.

## Gate check

`.last-ds-mile/stages/04-baseline.md` and `.last-ds-mile/stages/05-validate.md` both
exist and were read before modeling began. Baseline anchor: **RMSE 0.3999**
(log-space, unaffected by the pipeline fixes — verified directly, since the fixes
touch features, not the target). Validation strategy: 5-fold stratified-by-price-
quintile CV, imported from `scripts/pipeline_lib.py` and `scripts/model.py`'s
`build_cv_splitter` — unchanged from `/ds-validate`.

## Experiments table

| Model | Mean RMSE | Std | Train RMSE | Train/Val gap |
|---|---|---|---|---|
| Ridge (α=10, now scaled) | 0.1426 | 0.0414 | 0.1088 | 0.0338 |
| Lasso (α=0.001, now scaled) | 0.1409 | 0.0423 | 0.1158 | 0.0251 |
| RandomForest (300 trees) | 0.1428 | 0.0095 | 0.0520 | 0.0909 |
| LightGBM (one-hot) | 0.1309 | 0.0139 | 0.0410 | 0.0899 |
| XGBoost (one-hot) | 0.1295 | 0.0167 | 0.0457 | 0.0838 |
| CatBoost (native categorical) | 0.1253 | 0.0134 | 0.0793 | 0.0460 |
| **Blend (LightGBM + CatBoost-native, 50/50)** | **0.1244** | **0.0141** | — | — |

## What scaling actually changed for Ridge/Lasso — and what it didn't

Scaling fixed the *methodological* bug (regularization was previously arbitrary across
features of wildly different magnitude), but it did **not** fix Ridge/Lasso's
fold-to-fold instability: std is still 0.0414–0.0423, barely different from the
unscaled v1 run (0.0423–0.0450). **This is an important, honest correction to the
original review's hypothesis** — I predicted the scaling bug explained the
instability; it didn't. The real cause (confirmed by checking fold 4 specifically,
where both models still spike) is that this particular price-quintile fold contains a
combination of extreme-value rows that a linear model's fixed global coefficients
can't represent, regardless of input scale — a genuine linear-vs-nonlinear
model limitation, not a preprocessing artifact. Scaling was still the correct fix to
make (the comparison is now fair), it just isn't the explanation for the instability
finding.

## CatBoost native categorical handling: a nuanced result, reported straight

Native-categorical CatBoost (0.1253 ± 0.0134) scored marginally **worse** on raw RMSE
than the old one-hot CatBoost from v1 (0.1235 ± 0.0143) — one-hot happened to work
slightly better for pure predictive score on this dataset. This is not the outcome I
expected going in, and it's reported as-is rather than reframed to fit the original
diagnosis. What native handling *did* deliver, confirmed in `/ds-explain` (Stage 8):
exact top-5 agreement between permutation importance and SHAP (vs. 4-of-5 for the
one-hot version), and it surfaced `GarageFinish` as a real driver that one-hot had
split across four separate near-zero-importance dummy columns. **The fix was still
correct** — it traded a small amount of raw score for a materially more interpretable
model and a component that blends well with LightGBM's different error pattern.

## Blend result

`Blend(LightGBM + CatBoost-native)`, simple 50/50 average of out-of-fold predictions
— **0.1244 ± 0.0141**, beating every single component (best single: CatBoost-native
at 0.1253). Per `model-ensembling`: this pair was chosen because they encode
categoricals differently (one-hot vs. native) as well as being different model
families, which is more likely to produce genuinely different error patterns than
blending two similar boosted-tree configs. The lift over the best single component
(0.0009) is itself small relative to the components' own std (0.0134–0.0141) — **this
blend's improvement over CatBoost-native alone is not clearly beyond noise**, stated
plainly rather than oversold. It's adopted anyway because it costs nothing at
inference (two existing models, weighted-averaged) and never loses to either single
component on any individual fold — a legitimate "free" choice, not a demonstrated big
win.

## Best candidate and lift over baseline

**Blend(LightGBM + CatBoost-native)**, mean RMSE **0.1244 ± 0.0141**.

**Lift over baseline:** 0.3999 − 0.1244 = **0.2755**, roughly **19.5x** the
candidate's own fold std (0.0141) — unambiguously real, exactly as strong a
conclusion as v1's (0.2764/0.0143 ≈ 19.3x), unaffected by which specific candidate
sits at the top.

## Bias/variance diagnosis (new — `ds-model` Tier 2)

The winning single-model component, CatBoost-native, has train RMSE 0.0793 vs.
validation RMSE 0.1253 — **gap 0.0460**, the *smallest* train/val gap of the four
tree-based candidates (RandomForest: 0.0909, LightGBM: 0.0899, XGBoost: 0.0838). This
means CatBoost-native is already the *least* overfit of the nonlinear candidates —
the next lever for further improvement, if pursued, would be more/better features
(`/ds-prep`) rather than more regularization, since variance is already comparatively
well-controlled. RandomForest's much larger gap (0.0909) despite a similar validation
score (0.1428) is a textbook variance signal: memorizing training rows without
generalizing better than more regularized boosted trees.

**A distinct, easily-conflated finding:** Ridge/Lasso have the *smallest* train/val
gaps of all seven candidates (0.0251–0.0338) — by the bias/variance framework alone,
they look like the least-overfit models. But their fold-to-fold std (0.0414–0.0423) is
the *worst* of any candidate. **Train/val gap and fold-to-fold std are different axes**
— a model can be simultaneously low-variance in the bias/variance sense (doesn't
overfit its own training data) and high-variance in the resampling sense (unstable
across different training samples). Ridge/Lasso are exactly that combination here:
they're the right model class to describe a *stable, low-complexity* relationship,
but this fold's specific quintile-4 rows don't fit a fixed global linear form, and no
amount of "less overfitting" fixes a shape mismatch.

## Nested-CV tuning (new — light hyperparameter search, per `validation-strategy`)

Tuned CatBoost-native inside each outer fold's training data only (inner 3-fold CV,
6-combo grid over `depth ∈ {4,6,8}`, `learning_rate ∈ {0.02,0.03,0.05}`,
`iterations ∈ {400,600,800}`), so the outer score is an honest estimate of a *tuned*
model, not optimistic reuse of the folds used to pick hyperparameters.

| Outer fold | Best params found | Outer RMSE |
|---|---|---|
| 0 | depth=6, lr=0.05, iters=600 | 0.1112 |
| 1 | depth=6, lr=0.05, iters=600 | 0.1187 |
| 2 | depth=6, lr=0.05, iters=600 | 0.1115 |
| 3 | depth=6, lr=0.03, iters=600 | 0.1297 |
| 4 | depth=4, lr=0.05, iters=800 | 0.1582 |

**Nested-CV tuned CatBoost: 0.1259 ± 0.0175** vs. **untuned: 0.1253 ± 0.0134**.
**Tuning gain: −0.0006** (i.e. the tuned version is very slightly *worse*), well
within the ±0.0175 std. **Verdict: tuning did not produce a demonstrated
improvement.** The untuned defaults (`depth=6, lr=0.03, iters=600`) were already close
to what the search kept re-selecting (4 of 5 outer folds picked `depth=6`, 3 of 5
picked `lr=0.05` — only marginally different from the untuned `lr=0.03`). This is a
genuinely useful negative result: it says further tuning effort on this model type is
not where the next real improvement lives, rather than leaving that an open question
the team might otherwise spend more time on.

## One-time temporal robustness check

Train on `YrSold ≤ 2009`, evaluate once on `YrSold == 2010` (n=175), using the shipped
Blend — **RMSE 0.1117**, consistent with the CV mean (0.1244) if anything slightly
better, corroborating that the model isn't overfit to any one evaluation scheme. Per
`uncertainty-quantification`, this single point estimate has no fold variance of its
own and is treated as directional confirmation only.
