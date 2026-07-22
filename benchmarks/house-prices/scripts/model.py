"""Stage 6 — train candidates against the exact /ds-validate splitter, report mean±std.

Revision note: v1 of this script one-hot-encoded CatBoost (throwing away its native
categorical handling) and fed unscaled, skewed features to Ridge/Lasso. Both fixed in
pipeline_lib.py; this script now also adds a native-categorical CatBoost candidate, a
blended ensemble, a bias/variance check, and a light nested-CV tuning pass on the
winner — closing out the review's Tier 2 items.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from itertools import product
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_squared_error
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor, build_preprocessor_native

train, test = prepare_full()
num, cat = get_feature_lists(train)
X = train[num + cat]
y = train["logSalePrice"].values


def build_cv_splitter(df, n_splits=5, seed=42):
    price_bins = pd.qcut(df["logSalePrice"], q=5, labels=False)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(df, price_bins))


def temporal_holdout_mask(df):
    return df["YrSold"] <= 2009, df["YrSold"] == 2010


folds = build_cv_splitter(train)

candidates = {
    "Ridge(alpha=10)": Ridge(alpha=10.0),
    "Lasso(alpha=0.001)": Lasso(alpha=0.001, max_iter=20000),
    "RandomForest(300)": RandomForestRegressor(n_estimators=300, max_depth=None, random_state=0, n_jobs=-1),
    "LightGBM": LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=16, verbosity=-1, random_state=0),
    "XGBoost": XGBRegressor(n_estimators=600, learning_rate=0.03, max_depth=4, random_state=0, verbosity=0),
}

results = {}
fold_train_rmse = {}  # for the bias/variance check
oof_by_model = {}

for name, model in candidates.items():
    pre = build_preprocessor(num, cat)
    pipe = Pipeline([("pre", pre), ("model", model)])
    val_rmses, train_rmses = [], []
    oof = np.zeros(len(train))
    for tr_idx, va_idx in folds:
        pipe.fit(X.iloc[tr_idx], y[tr_idx])
        pred_va = pipe.predict(X.iloc[va_idx])
        pred_tr = pipe.predict(X.iloc[tr_idx])
        val_rmses.append(np.sqrt(mean_squared_error(y[va_idx], pred_va)))
        train_rmses.append(np.sqrt(mean_squared_error(y[tr_idx], pred_tr)))
        oof[va_idx] = pred_va
    val_rmses, train_rmses = np.array(val_rmses), np.array(train_rmses)
    results[name] = (val_rmses.mean(), val_rmses.std(), val_rmses)
    fold_train_rmse[name] = train_rmses.mean()
    oof_by_model[name] = oof
    print(f"{name:22s} val_mean={val_rmses.mean():.4f}  val_std={val_rmses.std():.4f}  "
          f"train_mean={train_rmses.mean():.4f}  gap={val_rmses.mean()-train_rmses.mean():.4f}")

# --- CatBoost, native categorical handling (not one-hot) ---
cat_val_rmses, cat_train_rmses = [], []
cat_oof = np.zeros(len(train))
for tr_idx, va_idx in folds:
    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X.iloc[tr_idx])
    Xv = pre_native.transform(X.iloc[va_idx])
    model = CatBoostRegressor(
        iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx,
        random_state=0, verbose=False,
    )
    model.fit(Xt, y[tr_idx])
    pred_va = model.predict(Xv)
    pred_tr = model.predict(Xt)
    cat_val_rmses.append(np.sqrt(mean_squared_error(y[va_idx], pred_va)))
    cat_train_rmses.append(np.sqrt(mean_squared_error(y[tr_idx], pred_tr)))
    cat_oof[va_idx] = pred_va
cat_val_rmses, cat_train_rmses = np.array(cat_val_rmses), np.array(cat_train_rmses)
results["CatBoost(native cat)"] = (cat_val_rmses.mean(), cat_val_rmses.std(), cat_val_rmses)
fold_train_rmse["CatBoost(native cat)"] = cat_train_rmses.mean()
oof_by_model["CatBoost(native cat)"] = cat_oof
print(f"{'CatBoost(native cat)':22s} val_mean={cat_val_rmses.mean():.4f}  val_std={cat_val_rmses.std():.4f}  "
      f"train_mean={cat_train_rmses.mean():.4f}  gap={cat_val_rmses.mean()-cat_train_rmses.mean():.4f}")

# --- Blend: simple average of the two strongest, structurally different candidates ---
# LightGBM (one-hot) and CatBoost (native categorical) are the two best-scoring
# non-linear-model candidates that also differ enough in how they see categoricals to
# plausibly make different mistakes — averaging genuinely different error patterns is
# what makes a blend work, not just averaging any two similar models.
blend_oof = 0.5 * oof_by_model["LightGBM"] + 0.5 * oof_by_model["CatBoost(native cat)"]
blend_fold_rmses = np.array([
    np.sqrt(mean_squared_error(y[va_idx], blend_oof[va_idx])) for _, va_idx in folds
])
results["Blend(LightGBM+CatBoost)"] = (blend_fold_rmses.mean(), blend_fold_rmses.std(), blend_fold_rmses)
oof_by_model["Blend(LightGBM+CatBoost)"] = blend_oof
print(f"{'Blend(LightGBM+CatBoost)':22s} val_mean={blend_fold_rmses.mean():.4f}  val_std={blend_fold_rmses.std():.4f}")

# --- Summary table ---
print("\n=== Full comparison (mean ± std) ===")
for name, (m, s, _) in sorted(results.items(), key=lambda kv: kv[1][0]):
    print(f"{name:26s} {m:.4f} ± {s:.4f}")

best_name = min(results, key=lambda k: results[k][0])
best_mean, best_std, best_folds = results[best_name]
print(f"\nBest candidate: {best_name}  {best_mean:.4f} ± {best_std:.4f}")

baseline_rmse = 0.3999
print(f"Lift over baseline: {baseline_rmse - best_mean:.4f}  (candidate std: {best_std:.4f})  "
      f"exceeds 1 std? {(baseline_rmse - best_mean) > best_std}")

# --- Bias/variance diagnosis for the winner ---
if best_name in fold_train_rmse:
    gap = best_mean - fold_train_rmse[best_name]
    print(f"\nBias/variance check ({best_name}): train_rmse={fold_train_rmse[best_name]:.4f}  "
          f"val_rmse={best_mean:.4f}  gap={gap:.4f}")

# --- Light nested-CV tuning of the winning single-model type (CatBoost) ---
# Small grid, tuned INSIDE each outer fold's training data only (inner 3-fold CV) —
# per validation-strategy's nested-CV pattern — so the reported outer score is an
# honest estimate of a *tuned* model, not optimistic re-use of the same folds used to
# pick hyperparameters. Manual grid loop, not RandomizedSearchCV/GridSearchCV: CatBoost's
# sklearn wrapper doesn't support sklearn's clone() when cat_features is set
# (RuntimeError: "constructor either does not set or modifies parameter cat_features"),
# which both of those tools require internally.
print("\n=== Nested CV: light tuning of CatBoost (native cat) ===")
import random as _random
param_combos = list(product([4, 6, 8], [0.02, 0.03, 0.05], [400, 600, 800]))
param_combos = _random.Random(0).sample(param_combos, 3)  # 3 of 27, fixed seed

outer_scores = []
for tr_idx, va_idx in folds:
    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X.iloc[tr_idx])
    Xv = pre_native.transform(X.iloc[va_idx])
    inner_price_bins = pd.qcut(train["logSalePrice"].iloc[tr_idx], q=5, labels=False)
    inner_cv = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=1).split(Xt, inner_price_bins))

    best_score, best_params = np.inf, None
    for depth, lr, iters in param_combos:
        inner_scores = []
        for in_tr, in_va in inner_cv:
            m = CatBoostRegressor(depth=depth, learning_rate=lr, iterations=iters,
                                   cat_features=cat_idx, random_state=0, verbose=False)
            m.fit(Xt[in_tr], y[tr_idx][in_tr])
            inner_scores.append(np.sqrt(mean_squared_error(y[tr_idx][in_va], m.predict(Xt[in_va]))))
        mean_inner = np.mean(inner_scores)
        if mean_inner < best_score:
            best_score, best_params = mean_inner, (depth, lr, iters)

    depth, lr, iters = best_params
    final_m = CatBoostRegressor(depth=depth, learning_rate=lr, iterations=iters,
                                 cat_features=cat_idx, random_state=0, verbose=False)
    final_m.fit(Xt, y[tr_idx])
    pred_va = final_m.predict(Xv)
    outer_scores.append(np.sqrt(mean_squared_error(y[va_idx], pred_va)))
    print(f"  outer fold best params: depth={depth} lr={lr} iters={iters}  outer RMSE: {outer_scores[-1]:.4f}")

outer_scores = np.array(outer_scores)
print(f"\nNested-CV tuned CatBoost: {outer_scores.mean():.4f} ± {outer_scores.std():.4f}  "
      f"(untuned native CatBoost was {cat_val_rmses.mean():.4f} ± {cat_val_rmses.std():.4f})")
tuning_gain = cat_val_rmses.mean() - outer_scores.mean()
print(f"Tuning gain: {tuning_gain:.4f} (candidate std: {outer_scores.std():.4f}) — "
      f"exceeds std? {abs(tuning_gain) > outer_scores.std()}")

# Temporal holdout check for the best untuned candidate (one-time, not used for tuning)
train_mask, holdout_mask = temporal_holdout_mask(train)
if best_name == "CatBoost(native cat)":
    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X[train_mask])
    Xv = pre_native.transform(X[holdout_mask])
    model = CatBoostRegressor(iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx, random_state=0, verbose=False)
    model.fit(Xt, y[train_mask])
    pred_holdout = model.predict(Xv)
else:
    pre = build_preprocessor(num, cat)
    model = candidates.get(best_name, LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=16, verbosity=-1, random_state=0))
    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(X[train_mask], y[train_mask])
    pred_holdout = pipe.predict(X[holdout_mask])

holdout_rmse = np.sqrt(mean_squared_error(y[holdout_mask], pred_holdout))
print(f"\nTemporal holdout RMSE ({best_name}, train<=2009 -> test=2010, n={holdout_mask.sum()}): {holdout_rmse:.4f}")
