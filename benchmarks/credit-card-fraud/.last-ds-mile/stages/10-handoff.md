# Stage 10 — Reproducibility & Handoff

## Gate check — environment pinned

Same pinned environment as house-prices and telco-churn (shared `.venv`):

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

Python 3.13. Gate passed — no bare package names, every version exact.

## Model card

- **What it predicts:** `Class` (1=fraud) probability for a card transaction; the
  decision itself is `score >= 0.4932` (the frozen threshold).
- **What it is:** `Blend(LGBMClassifier 50%, CatBoostClassifier 50%)`, both
  `class_weight`/`auto_class_weights="Balanced"` (not `scale_pos_weight` — see
  `06-model.md`'s LightGBM-collapse finding).
- **Predict contract:** `0.5*lgbm_model.predict_proba(df)[:,1] +
  0.5*catboost_model.predict_proba(df)[:,1]`, recorded exactly in
  `artifacts/model_card_meta.json`'s `predict_contract` field.
- **Training data:** Kaggle "Credit Card Fraud Detection," 283,726 rows after
  deduplication (see `/ds-data`). Data hash: `sha256:76274b691b16a6c4…`.
- **Metric and baseline lift:** PR-AUC 0.8455 ± 0.0117 vs. baseline 0.00167 — a
  0.8438 lift, ~72x the model's own fold noise. **Reliability confirmed across 5
  independent seeds**: mean 0.8465, seed-to-seed std 0.0010 (see the seed-stability
  check).
- **Known limitations:** see `/ds-report` — missed fraud skews toward a small
  number of large-value tail cases, small-dollar fraud near the threshold is
  hardest, raw scores aren't calibrated probabilities, no domain-plausibility check
  possible on anonymized features, temporal holdout scored somewhat lower (noisy
  single estimate).
- **Intended use:** transaction-screening flag with human review routing.
  **Out-of-scope use:** automated blocking without review, deployment without
  periodic retraining as fraud patterns shift, any non-card or non-European-
  cardholder population outside this training distribution.

## Rerun confirmation

**Cross-script agreement:** `scripts/model.py`'s Blend result (PR-AUC 0.8455 ±
0.0117) and `scripts/evaluate.py`'s independently-computed OOF Blend result (fold
mean 0.8455 ± 0.0117, pooled 0.8451) match to 4 decimal places — two separately-
written scripts, same shared `pipeline_lib.py` contract, same result.
**Seed-stability run** (`scripts/seed_stability.py`) independently reproduced
seed=42's fold-level PR-AUC values exactly, as its first row.

## Artifact

- **Model file:** `artifacts/fraud_blend_pipeline.joblib` — `{lgbm_model,
  catboost_model, blend_weights, feature_lists, frozen_threshold}`, each component
  fit on all 283,726 deduplicated rows.
- **Metadata:** `artifacts/model_card_meta.json`.
- **Reproduction path:** `scripts/pipeline_lib.py` → `scripts/model.py` (candidate
  comparison, including the LightGBM-fix history) → `scripts/evaluate.py` (OOF
  evaluation, slices, figures) → `scripts/explain.py` (interpretation) →
  `scripts/serialize_artifact.py` (final artifact). `scripts/seed_stability.py` is
  the reliability check, not part of the shipped-model reproduction path itself.
