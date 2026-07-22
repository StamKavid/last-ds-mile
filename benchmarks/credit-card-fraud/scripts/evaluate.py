"""Stage 7 — evaluation for credit-card-fraud: OOF predictions from the shipped
Blend(LightGBM+CatBoost), slices, calibration, error analysis."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num]
y = df["Class"].values

folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(y)), y))
oof = np.zeros(len(df))
fold_pr = []
for tr_idx, va_idx in folds:
    lgbm = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                           class_weight="balanced", verbosity=-1, random_state=0)
    lgbm.fit(X.iloc[tr_idx], y[tr_idx])
    p_lgbm = lgbm.predict_proba(X.iloc[va_idx])[:, 1]

    cb = CatBoostClassifier(iterations=400, learning_rate=0.05, depth=6,
                             auto_class_weights="Balanced", random_state=0, verbose=False)
    cb.fit(X.iloc[tr_idx], y[tr_idx])
    p_cb = cb.predict_proba(X.iloc[va_idx])[:, 1]

    blend = 0.5 * p_lgbm + 0.5 * p_cb
    oof[va_idx] = blend
    fold_pr.append(average_precision_score(y[va_idx], blend))

fold_pr = np.array(fold_pr)
overall_pr = average_precision_score(y, oof)
overall_roc = roc_auc_score(y, oof)
print(f"Out-of-fold PR-AUC: {overall_pr:.4f}  ROC-AUC: {overall_roc:.4f}")
print(f"Per-fold PR-AUC: {np.round(fold_pr, 4)}  mean={fold_pr.mean():.4f} std={fold_pr.std():.4f}")

df = df.copy()
df["oof_score"] = oof

# --- Calibration: predicted-decile vs actual fraud rate ---
df["score_decile"] = pd.qcut(df["oof_score"].rank(method="first"), q=10, labels=False)
decile_stats = df.groupby("score_decile").agg(
    mean_score=("oof_score", "mean"), actual_rate=("Class", "mean"), n=("Class", "size"))
print("\n=== Calibration by predicted decile ===")
print(decile_stats)

# --- Slice by Amount bucket ---
df["amount_bucket"] = pd.cut(df["Amount"], bins=[-0.01, 10, 50, 200, 1000, 1e9],
                              labels=["<$10", "$10-50", "$50-200", "$200-1000", ">$1000"])
print("\n=== Slice by Amount bucket ===")
slice_amt = df.groupby("amount_bucket", observed=True).apply(
    lambda g: pd.Series({
        "n": len(g), "n_fraud": g["Class"].sum(),
        "PR-AUC": average_precision_score(g["Class"], g["oof_score"]) if g["Class"].sum() > 1 else np.nan,
    }), include_groups=False)
print(slice_amt)

# --- Slice by hour_of_day (bucketed into quartile-of-day for cell size) ---
df["day_period"] = pd.cut(df["hour_of_day"], bins=[-1, 5, 11, 17, 23],
                           labels=["night(0-5)", "morning(6-11)", "afternoon(12-17)", "evening(18-23)"])
print("\n=== Slice by day period ===")
slice_period = df.groupby("day_period", observed=True).apply(
    lambda g: pd.Series({
        "n": len(g), "n_fraud": g["Class"].sum(), "fraud_rate": g["Class"].mean(),
        "PR-AUC": average_precision_score(g["Class"], g["oof_score"]) if g["Class"].sum() > 1 else np.nan,
    }), include_groups=False)
print(slice_period)

# --- Error analysis: false negatives (missed fraud) at the frozen threshold ---
FROZEN_THRESHOLD = 0.4932
preds = (df["oof_score"] >= FROZEN_THRESHOLD).astype(int)
fn_mask = (preds == 0) & (df["Class"] == 1)
fp_mask = (preds == 1) & (df["Class"] == 0)
print(f"\n=== Missed fraud (false negatives) at frozen threshold {FROZEN_THRESHOLD}: {fn_mask.sum()} ===")
print(df.loc[fn_mask, ["Time", "Amount", "oof_score"]].sort_values("oof_score", ascending=False).head(10))
print(f"\n=== False alarms (false positives), {fp_mask.sum()} total, highest-scored 5 ===")
print(df.loc[fp_mask, ["Time", "Amount", "oof_score"]].sort_values("oof_score", ascending=False).head(5))

# Save OOF for /ds-explain and /ds-report use.
df[["Time", "Amount", "Class", "oof_score"]].to_csv("artifacts/oof_predictions.csv", index=False)

# --- Figures ---
fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(decile_stats["mean_score"], decile_stats["actual_rate"], "o-", color="#C44E52", label="Observed")
ax.set_yscale("symlog", linthresh=0.001)
ax.set_xlabel("Mean predicted score per decile")
ax.set_ylabel("Actual fraud rate per decile (log scale)")
ax.set_title("Calibration by predicted-score decile (Blend)")
ax.legend()
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-calibration.png", dpi=110)
plt.close()

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(slice_amt.index.astype(str), slice_amt["PR-AUC"], color="#4C72B0")
ax.axhline(overall_pr, color="#C44E52", linestyle="--", label=f"Overall PR-AUC ({overall_pr:.4f})")
ax.set_ylabel("PR-AUC")
ax.set_title("Out-of-fold PR-AUC by transaction-amount bucket")
ax.legend()
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-slice-performance.png", dpi=110)
plt.close()

print("\nFigures and OOF predictions written.")
