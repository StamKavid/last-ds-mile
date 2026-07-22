"""Stage 10 — serialize the shipped Blend(LogReg+CatBoost-native), fit on all rows."""
import sys, json, hashlib
sys.path.insert(0, "scripts")
from datetime import datetime, timezone
import joblib
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor, build_preprocessor_native

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num + cat]
y = df["Churn"].values

lr_pipe = Pipeline([
    ("pre", build_preprocessor(num, cat)),
    ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=0)),
])
lr_pipe.fit(X, y)

cat_pre, cat_idx = build_preprocessor_native(num, cat)
Xt_full = cat_pre.fit_transform(X)
cb = CatBoostClassifier(iterations=300, learning_rate=0.05, depth=6, cat_features=cat_idx,
                         auto_class_weights="Balanced", random_state=0, verbose=False)
cb.fit(Xt_full, y)

artifact = {
    "lr_pipeline": lr_pipe,
    "catboost_preprocessor": cat_pre,
    "catboost_model": cb,
    "blend_weights": {"logreg": 0.5, "catboost": 0.5},
    "feature_lists": {"numeric": num, "categorical": cat},
    "frozen_threshold": 0.3338,
}
joblib.dump(artifact, "artifacts/telco_churn_blend_pipeline.joblib")

with open("WA_Fn-UseC_-Telco-Customer-Churn.csv", "rb") as f:
    data_hash = hashlib.sha256(f.read()).hexdigest()

meta = {
    "model": "Blend(LogisticRegression one-hot+balanced 50%, CatBoostClassifier native-cat+balanced 50%)",
    "target": "Churn (1=Yes, 0=No)",
    "cv_roc_auc_mean": 0.8477,
    "cv_roc_auc_std": 0.0113,
    "baseline_roc_auc": 0.5,
    "frozen_threshold": 0.3338,
    "training_rows": len(df),
    "training_data_sha256_16": data_hash[:16],
    "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    "catboost_version": __import__("catboost").__version__,
    "predict_contract": (
        "score(df) = 0.5*lr_pipeline.predict_proba(df[numeric+categorical])[:,1] "
        "+ 0.5*catboost_model.predict_proba(catboost_preprocessor.transform(df[numeric+categorical]))[:,1]; "
        "flag if score >= frozen_threshold"
    ),
}
with open("artifacts/model_card_meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print("Artifact written: artifacts/telco_churn_blend_pipeline.joblib")
print(json.dumps(meta, indent=2))
