# Stage 10 — Reproducibility & Handoff

## Revision note

Re-serialized for the corrected shipped model, `Blend(LightGBM one-hot +
CatBoost-native)`, replacing the old single-CatBoost artifact.
`artifacts/house_prices_catboost_pipeline.joblib` deleted; the new artifact packages
both blend components together since neither alone is what's being shipped.

## Gate check — environment pinned

`requirements-lock.txt` pins exact versions of every package this pipeline used —
unchanged by the corrections (no new dependency was introduced; the fixes were to how
existing libraries were used, not which ones):

```
catboost==1.2.10
lightgbm==4.6.0
matplotlib==3.10.9
numpy==2.3.5
pandas==2.3.3
scikit-learn==1.7.2
scipy==1.16.3
shap==0.52.0
xgboost==3.1.3
```

Python 3.13 (this repo's `.venv`). Gate passed — no bare package names, every version
exact.

## Model card

- **What it predicts:** `log1p(SalePrice)` for a single-family Ames, Iowa residential
  sale; convert back with `expm1()` for a dollar figure.
- **What it is:** `Blend(LightGBM via sklearn Pipeline with one-hot categoricals, 50%;
  CatBoostRegressor with native categorical handling, 50%)` — a simple average of the
  two components' predictions, chosen per `model-ensembling` because they encode
  categorical features differently as well as being different model families, making
  genuinely different errors rather than correlated ones.
- **Predict contract:** `0.5 * lgbm_pipeline.predict(df) + 0.5 *
  catboost_model.predict(catboost_preprocessor.transform(df))`, both halves consuming
  the same `numeric + categorical` feature columns from `pipeline_lib.get_feature_lists`
  — recorded exactly in `artifacts/model_card_meta.json`'s `predict_contract` field so
  a future consumer doesn't have to reverse-engineer the blend from the pickle alone.
- **Training data:** Kaggle "House Prices — Advanced Regression Techniques" `train.csv`,
  1460 rows, 2006–2010 sales. Data hash: `sha256:ed142e0a97bd49fc…` — reconfirmed
  identical to the original run (see Rerun confirmation below).
- **Metric and baseline lift:** cross-validated RMSE 0.1244 ± 0.0141 (log-space) vs.
  a flat-median baseline of 0.3999 — a 0.2755 lift, ~19.5x the model's own fold noise
  (see `/ds-model`). In cost terms (`/ds-report`): a typical 13.2% relative price
  error overall, ~$21,600 at the dataset's median price — inside, not dramatically
  below, the agent's own assumed 10–15% manual accuracy.
- **Known limitations:** see `/ds-report` — degraded reliability on the cheapest
  price quintile (elevated non-arms-length sale rate; possibly *not* better than
  manual pricing there per the cost translation), two documented historical outlier
  rows (tested and rejected as a fix, twice), mild under-prediction at the top of the
  market.
- **Intended use:** listing-price *suggestion* for a pricing agent who retains
  override authority, weighted least heavily of all on sub-$130k listings. **Out-of-
  scope use:** automated pricing without human review, any property type outside
  single-family Ames residential, any sale outside the 2006–2010 training window
  without a retrain, and any use as a substitute for a licensed appraisal.

## Rerun confirmation

Two independent forms of reproducibility check, not one:

1. **Cross-script agreement:** `scripts/model.py` (candidate comparison) and
   `scripts/evaluate.py` (OOF evaluation), two separately-written scripts sharing only
   `pipeline_lib.py` and the same `random_state`/seeds, independently computed the
   *same* blend score — **mean 0.1244, std 0.0141, to 4 decimal places, in both
   scripts, run at different times.** This is a stronger check than rerunning one
   script twice: it also confirms the shared pipeline contract (`build_preprocessor`,
   `build_preprocessor_native`, `get_feature_lists`) behaves identically from two
   independent call sites, not just that one script is internally deterministic.
2. **Fresh full rerun of `scripts/explore.py`** (not from cached state) — identical
   skew, correlation, and collinearity numbers to the original run.

Every script fixes its own `random_state`/seed, so this reruns deterministically, not
just "close enough."

## Artifact

- **Model file:** `artifacts/house_prices_blend_pipeline.joblib` (1.7 MB) — a dict of
  `{lgbm_pipeline, catboost_preprocessor, catboost_model, blend_weights,
  feature_lists}`, each component fit on all 1460 training rows with the same code
  path as every CV fold.
- **Metadata:** `artifacts/model_card_meta.json` — model description, predict
  contract, metric, training row count, training-data hash, fit timestamp, and
  library versions, generated alongside the artifact rather than written by hand
  afterward.
- **Reproduction path:** `scripts/pipeline_lib.py` (shared feature engineering +
  preprocessing, imported by every later stage) → `scripts/model.py` (candidate
  comparison + blend + nested-CV tuning) → `scripts/evaluate.py` (OOF evaluation,
  slices, figures) → `scripts/explain.py` (interpretation) →
  `scripts/serialize_artifact.py` (final artifact). Each stage's corresponding
  `.last-ds-mile/stages/*.md` documents what ran and why.
