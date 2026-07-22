"""Stage 10 — serialize the actual shipped model: Blend(LightGBM one-hot + CatBoost-native),
fit on all training rows, with both components saved together plus the blend weight."""
import sys, json, hashlib
sys.path.insert(0, "scripts")
from datetime import datetime, timezone
import joblib
from sklearn.pipeline import Pipeline
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor, build_preprocessor_native

train, test = prepare_full()
num, cat = get_feature_lists(train)
X = train[num + cat]
y = train["logSalePrice"].values

lgbm_pipe = Pipeline([
    ("pre", build_preprocessor(num, cat)),
    ("model", LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=16, verbosity=-1, random_state=0)),
])
lgbm_pipe.fit(X, y)

cat_pre, cat_idx = build_preprocessor_native(num, cat)
Xt_full = cat_pre.fit_transform(X)
cat_model = CatBoostRegressor(iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx,
                               random_state=0, verbose=False)
cat_model.fit(Xt_full, y)

artifact = {
    "lgbm_pipeline": lgbm_pipe,
    "catboost_preprocessor": cat_pre,
    "catboost_model": cat_model,
    "blend_weights": {"lgbm": 0.5, "catboost": 0.5},
    "feature_lists": {"numeric": num, "categorical": cat},
}
joblib.dump(artifact, "artifacts/house_prices_blend_pipeline.joblib")

with open("train.csv", "rb") as f:
    data_hash = hashlib.sha256(f.read()).hexdigest()

meta = {
    "model": "Blend(LightGBM via sklearn Pipeline one-hot, 50%; CatBoostRegressor native-categorical, 50%)",
    "target": "log1p(SalePrice)",
    "cv_mean_rmse": 0.1244,
    "cv_std_rmse": 0.0141,
    "baseline_rmse": 0.3999,
    "training_rows": len(train),
    "training_data_sha256_16": data_hash[:16],
    "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    "lightgbm_version": __import__("lightgbm").__version__,
    "catboost_version": __import__("catboost").__version__,
    "predict_contract": (
        "predict(df) = 0.5 * lgbm_pipeline.predict(df[numeric+categorical]) "
        "+ 0.5 * catboost_model.predict(catboost_preprocessor.transform(df[numeric+categorical])); "
        "result is log1p(SalePrice), apply expm1() for a dollar figure"
    ),
}
with open("artifacts/model_card_meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print("Artifact written: artifacts/house_prices_blend_pipeline.joblib")
print(json.dumps(meta, indent=2))
