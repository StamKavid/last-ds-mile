"""Stage 8 — interpretation: permutation importance + SHAP for the shipped CatBoost model.

Revision note: v1 used shap.Explainer wrapping the whole sklearn Pipeline (the slow,
generic callable path) on a single CatBoost model. ds-explain's own skill text reserves
that path for black-box ensembles (AutoGluon, stacked/blended) — a single CatBoost
model should use the fast, exact shap.TreeExplainer on the native booster instead. Also
switched to CatBoost's native categorical handling (build_preprocessor_native),
matching the corrected /ds-model candidate.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from catboost import CatBoostRegressor
import shap

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor_native

train, test = prepare_full()
num, cat = get_feature_lists(train)
X = train[num + cat]
y = train["logSalePrice"].values
quintile = pd.qcut(train["logSalePrice"], q=5, labels=False)

X_dev, X_held, y_dev, y_held = train_test_split(X, y, test_size=0.15, stratify=quintile, random_state=42)

pre, cat_idx = build_preprocessor_native(num, cat)
Xt_dev = pre.fit_transform(X_dev)
Xt_held = pre.transform(X_held)

model = CatBoostRegressor(iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx,
                           random_state=0, verbose=False)
model.fit(Xt_dev, y_dev)

held_rmse = np.sqrt(np.mean((model.predict(Xt_held) - y_held) ** 2))
print("Held-set RMSE (dev-fit sanity check, native-cat CatBoost):", held_rmse)


# permutation_importance needs an sklearn-shaped estimator over the already-transformed
# array (avoids re-running the ColumnTransformer inside every permutation).
class _FittedCatBoostWrapper(BaseEstimator, RegressorMixin):
    def __init__(self, fitted_model):
        self.fitted_model = fitted_model

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return self.fitted_model.predict(X)


feature_names = num + cat
wrapper = _FittedCatBoostWrapper(model)
perm = permutation_importance(wrapper, Xt_held, y_held, n_repeats=15, random_state=0,
                               scoring="neg_root_mean_squared_error")
perm_series = pd.Series(perm.importances_mean, index=feature_names).sort_values(ascending=False)
print("\nTop 10 permutation importance:")
print(perm_series.head(10))

fig, ax = plt.subplots(figsize=(7, 5))
top10 = perm_series.head(10).iloc[::-1]
ax.barh(top10.index, top10.values, color="#4C72B0")
ax.set_xlabel("Permutation importance (RMSE increase when shuffled)")
ax.set_title("CatBoost (native cat) — permutation feature importance (held set)")
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/08-permutation-importance.png", dpi=110)
plt.close()

# --- SHAP: fast, exact TreeExplainer directly on the native CatBoost booster ---
# No callable-wrapping, no background sample, no encode/decode round-trip — this is
# exactly the "not a black-box ensemble" case ds-explain's own text calls out for the
# native fast path, and CatBoost's categorical columns are supported by name via
# feature_names passed at Pool-construction time (shap reads them from the model).
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(Xt_held)

mean_abs_shap = pd.Series(np.abs(shap_values).mean(axis=0), index=feature_names).sort_values(ascending=False)
print("\nTop 10 mean |SHAP| (all held rows, exact TreeExplainer):")
print(mean_abs_shap.head(10))

fig, ax = plt.subplots(figsize=(7, 5))
top10_shap = mean_abs_shap.head(10).iloc[::-1]
ax.barh(top10_shap.index, top10_shap.values, color="#55A868")
ax.set_xlabel("Mean |SHAP value| (log-space impact)")
ax.set_title("CatBoost (native cat) — SHAP summary (%d held rows)" % len(X_held))
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/08-shap-summary.png", dpi=110)
plt.close()

print("\nRank agreement (top 5): perm=%s shap=%s" % (
    list(perm_series.head(5).index), list(mean_abs_shap.head(5).index)
))

# Correlated-feature note: check whether the perm-vs-SHAP magnitude gap is explained
# by collinearity among the top features (TotalSF/GrLivArea/TotalBsmtSF correlate).
top_corr = train[["TotalSF", "GrLivArea", "TotalBsmtSF"]].corr()
print("\nCollinearity among size features (for the perm-vs-SHAP magnitude discussion):")
print(top_corr.round(2))
