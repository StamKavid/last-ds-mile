# Stage 10 — Reproducibility & Handoff

## Gate check — environment pinned

Same pinned environment as the other two benchmarks (shared `.venv`):

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

- **What it predicts:** `Churn` probability for a customer account; the decision
  itself is `score >= 0.3338` (the frozen threshold).
- **What it is:** `Blend(LogisticRegression one-hot+balanced 50%, CatBoostClassifier
  native-categorical+balanced 50%)`.
- **Predict contract:** `0.5*lr_pipeline.predict_proba(df)[:,1] +
  0.5*catboost_model.predict_proba(catboost_preprocessor.transform(df))[:,1]`,
  recorded exactly in `artifacts/model_card_meta.json`.
- **Training data:** IBM/Kaggle "Telco Customer Churn," 7,043 rows (no dedup — see
  `/ds-data`'s stated reasoning). Data hash: `sha256:88be4b93fbe0cc83…`.
- **Metric and baseline lift:** ROC-AUC 0.8477 ± 0.0113 vs. baseline 0.5 — a 0.3477
  lift, ~30.8x the model's own fold noise. **Reliability confirmed across 5
  independent seeds**: mean 0.8477, seed-to-seed std 0.0004.
- **Known limitations:** see `/ds-report` — weaker discrimination within the
  highest-risk segments specifically, a large false-alarm volume at this recall-
  favoring threshold, raw scores overstate churn probability mid-range, some
  loyal-profile customers churn with no flagging feature in this dataset.
- **Intended use:** per-cycle retention-outreach prioritization, human-planned
  contact. **Out-of-scope use:** automated retention offers without human planning,
  any customer population or product mix meaningfully different from this
  snapshot without a retrain, lifetime-value or discount-sizing decisions (this
  model scores churn risk only).

## Rerun confirmation

**Cross-script agreement:** `scripts/model.py`'s Blend result (ROC-AUC 0.8477 ±
0.0113) and `scripts/evaluate.py`'s independently-computed OOF Blend result (fold
mean 0.8477 ± 0.0113, pooled 0.8475) match to 4 decimal places. **Seed-stability
run** (`scripts/seed_stability.py`) reproduced seed=42's fold-level ROC-AUC values
exactly as its first row — three independent script executions, one number.

## Artifact

- **Model file:** `artifacts/telco_churn_blend_pipeline.joblib` — `{lr_pipeline,
  catboost_preprocessor, catboost_model, blend_weights, feature_lists,
  frozen_threshold}`, each component fit on all 7,043 rows.
- **Metadata:** `artifacts/model_card_meta.json`.
- **Reproduction path:** `scripts/pipeline_lib.py` → `scripts/model.py` →
  `scripts/evaluate.py` → `scripts/explain.py` → `scripts/serialize_artifact.py`.
  `scripts/seed_stability.py` is the reliability check, not part of the
  shipped-model reproduction path itself.
