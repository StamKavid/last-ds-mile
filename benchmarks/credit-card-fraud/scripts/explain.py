"""Stage 8 — interpretation for credit-card-fraud. Explains the CatBoost component of
the shipped Blend via exact shap.TreeExplainer (fast, exact path for a single
non-ensemble model, same reasoning as house-prices' explain.py)."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from catboost import CatBoostClassifier
import shap

from pipeline_lib import prepare_full, get_feature_lists

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num]
y = df["Class"].values

X_dev, X_held, y_dev, y_held = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)

model = CatBoostClassifier(iterations=400, learning_rate=0.05, depth=6,
                            auto_class_weights="Balanced", random_state=0, verbose=False)
model.fit(X_dev, y_dev)


feature_names = num
perm = permutation_importance(model, X_held, y_held, n_repeats=15, random_state=0,
                               scoring="average_precision")
perm_series = pd.Series(perm.importances_mean, index=feature_names).sort_values(ascending=False)
print("Top 10 permutation importance (PR-AUC drop when shuffled):")
print(perm_series.head(10))

fig, ax = plt.subplots(figsize=(7, 5))
top10 = perm_series.head(10).iloc[::-1]
ax.barh(top10.index, top10.values, color="#4C72B0")
ax.set_xlabel("Permutation importance (PR-AUC decrease when shuffled)")
ax.set_title("CatBoost — permutation feature importance (held set)")
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/08-permutation-importance.png", dpi=110)
plt.close()

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_held)
if isinstance(shap_values, list):
    shap_values = shap_values[1]  # positive-class SHAP for a binary classifier, if returned as a list

mean_abs_shap = pd.Series(np.abs(shap_values).mean(axis=0), index=feature_names).sort_values(ascending=False)
print("\nTop 10 mean |SHAP| (all held rows, exact TreeExplainer):")
print(mean_abs_shap.head(10))

fig, ax = plt.subplots(figsize=(7, 5))
top10_shap = mean_abs_shap.head(10).iloc[::-1]
ax.barh(top10_shap.index, top10_shap.values, color="#55A868")
ax.set_xlabel("Mean |SHAP value|")
ax.set_title("CatBoost — SHAP summary (%d held rows)" % len(X_held))
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/08-shap-summary.png", dpi=110)
plt.close()

top_share = mean_abs_shap.iloc[0] / mean_abs_shap.sum()
print(f"\nTop feature's share of total |SHAP| attribution: {top_share:.3f}")
print("Rank agreement (top 5): perm=%s shap=%s" % (
    list(perm_series.head(5).index), list(mean_abs_shap.head(5).index)
))
