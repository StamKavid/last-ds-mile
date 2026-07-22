"""Stage 10 — serialize the shipped Blend(LightGBM+CatBoost), fit on all rows."""
import sys, json, hashlib
sys.path.insert(0, "scripts")
from datetime import datetime, timezone
import joblib
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num]
y = df["Class"].values

lgbm = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                       class_weight="balanced", verbosity=-1, random_state=0)
lgbm.fit(X, y)

cb = CatBoostClassifier(iterations=400, learning_rate=0.05, depth=6,
                         auto_class_weights="Balanced", random_state=0, verbose=False)
cb.fit(X, y)

artifact = {
    "lgbm_model": lgbm,
    "catboost_model": cb,
    "blend_weights": {"lgbm": 0.5, "catboost": 0.5},
    "feature_lists": {"numeric": num, "categorical": cat},
    "frozen_threshold": 0.4932,
}
joblib.dump(artifact, "artifacts/fraud_blend_pipeline.joblib")

with open("creditcard.csv", "rb") as f:
    data_hash = hashlib.sha256(f.read()).hexdigest()

meta = {
    "model": "Blend(LGBMClassifier 50%, CatBoostClassifier 50%), both class-weight-balanced",
    "target": "Class (1=fraud, 0=genuine)",
    "cv_pr_auc_mean": 0.8455,
    "cv_pr_auc_std": 0.0117,
    "baseline_pr_auc": 0.00167,
    "frozen_threshold": 0.4932,
    "training_rows": len(df),
    "training_data_sha256_16": data_hash[:16],
    "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    "lightgbm_version": __import__("lightgbm").__version__,
    "catboost_version": __import__("catboost").__version__,
    "predict_contract": (
        "score(df) = 0.5*lgbm_model.predict_proba(df[numeric])[:,1] "
        "+ 0.5*catboost_model.predict_proba(df[numeric])[:,1]; "
        "flag if score >= frozen_threshold"
    ),
}
with open("artifacts/model_card_meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print("Artifact written: artifacts/fraud_blend_pipeline.joblib")
print(json.dumps(meta, indent=2))
