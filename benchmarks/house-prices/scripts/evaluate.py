"""Stage 7 — evaluation: true out-of-fold predictions, slice performance, error analysis.

Revision note: v1 evaluated a single one-hot CatBoost. The shipped model per the
corrected /ds-model is Blend(LightGBM one-hot + CatBoost-native) — this now computes
OOF predictions for the actual shipped blend, not a stand-in single model.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_squared_error
from lightgbm import LGBMRegressor
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


folds = build_cv_splitter(train)
oof_lgbm = np.zeros(len(train))
oof_cat = np.zeros(len(train))
fold_rmses = []

for tr_idx, va_idx in folds:
    pre = build_preprocessor(num, cat)
    lgbm = LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=16, verbosity=-1, random_state=0)
    pipe = Pipeline([("pre", pre), ("model", lgbm)])
    pipe.fit(X.iloc[tr_idx], y[tr_idx])
    oof_lgbm[va_idx] = pipe.predict(X.iloc[va_idx])

    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X.iloc[tr_idx])
    Xv = pre_native.transform(X.iloc[va_idx])
    cb = CatBoostRegressor(iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx,
                            random_state=0, verbose=False)
    cb.fit(Xt, y[tr_idx])
    oof_cat[va_idx] = cb.predict(Xv)

    blend_va = 0.5 * oof_lgbm[va_idx] + 0.5 * oof_cat[va_idx]
    fold_rmses.append(np.sqrt(mean_squared_error(y[va_idx], blend_va)))

oof_pred = 0.5 * oof_lgbm + 0.5 * oof_cat
fold_rmses = np.array(fold_rmses)
overall_rmse = np.sqrt(mean_squared_error(y, oof_pred))
print("Out-of-fold overall RMSE (Blend): %.4f" % overall_rmse)
print("Per-fold RMSE: %s  mean=%.4f std=%.4f" % (np.round(fold_rmses, 4), fold_rmses.mean(), fold_rmses.std()))

residual = y - oof_pred  # actual - predicted, in log-space
print("\nMean residual (bias): %.4f" % residual.mean())

# Slice by price quintile
train = train.copy()
train["oof_pred"] = oof_pred
train["residual"] = residual
train["price_quintile"] = pd.qcut(train["logSalePrice"], q=5, labels=[f"Q{i+1}" for i in range(5)])

print("\n=== Slice by price quintile ===")
slice_q = train.groupby("price_quintile").apply(
    lambda g: pd.Series({
        "n": len(g),
        "RMSE": np.sqrt(mean_squared_error(g["logSalePrice"], g["oof_pred"])),
        "mean_residual": g["residual"].mean(),
    }),
    include_groups=False,
)
print(slice_q)

print("\n=== Slice by Neighborhood ===")
slice_n = train.groupby("Neighborhood").apply(
    lambda g: pd.Series({"n": len(g), "RMSE": np.sqrt(mean_squared_error(g["logSalePrice"], g["oof_pred"]))}),
    include_groups=False,
).sort_values("n")
print(slice_n.head(10))
print("...")
print(slice_n.sort_values("RMSE", ascending=False).head(5))

print("\n=== Worst 5 mispredictions ===")
worst = train.reindex(train["residual"].abs().sort_values(ascending=False).index).head(5)
print(worst[["Id", "Neighborhood", "OverallQual", "GrLivArea", "SalePrice", "residual"]])

# Save OOF predictions + fold assignment for the /ds-iterate outlier re-check.
oof_df = train[["Id", "Neighborhood", "logSalePrice", "oof_pred", "residual"]].copy()
fold_assignment = np.zeros(len(train), dtype=int)
for i, (_, va_idx) in enumerate(folds):
    fold_assignment[va_idx] = i
oof_df["fold"] = fold_assignment
oof_df.to_csv("artifacts/oof_predictions.csv", index=False)

# --- Figure: slice performance bar chart vs overall ---
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(slice_q.index.astype(str), slice_q["RMSE"], color="#4C72B0", label="Per-slice RMSE")
ax.axhline(overall_rmse, color="#C44E52", linestyle="--", label=f"Overall RMSE ({overall_rmse:.4f})")
ax.set_ylabel("RMSE (log-space)")
ax.set_title("Out-of-fold RMSE by price quintile vs. overall (Blend model)")
ax.legend()
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-slice-performance.png", dpi=110)
plt.close()

# --- Figure: residual calibration — raw scatter + decile means ---
train["pred_decile"] = pd.qcut(train["oof_pred"], q=10, labels=False)
decile_stats = train.groupby("pred_decile").agg(mean_pred=("oof_pred", "mean"), mean_actual=("logSalePrice", "mean"))
fig, ax = plt.subplots(figsize=(6, 5.5))
ax.scatter(train["oof_pred"], train["logSalePrice"], alpha=0.15, s=10, color="#4C72B0",
           label=f"Individual rows (n={len(train)}, RMSE={overall_rmse:.3f})")
ax.plot(decile_stats["mean_pred"], decile_stats["mean_actual"], "o-", color="#C44E52",
        linewidth=2, markersize=6, label="Decile means")
lims = [train["oof_pred"].min(), train["oof_pred"].max()]
ax.plot(lims, lims, "--", color="gray", label="Perfect calibration")
ax.set_xlabel("Predicted log(SalePrice)")
ax.set_ylabel("Actual log(SalePrice)")
ax.set_title("Calibration: row-level scatter + decile means (Blend)")
ax.legend(loc="upper left", fontsize=8)
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-calibration.png", dpi=110)
plt.close()

print("\nFigures and OOF predictions written.")
