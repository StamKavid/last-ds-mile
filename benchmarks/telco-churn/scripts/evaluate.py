"""Stage 7 — evaluation for telco-churn: OOF predictions from the shipped
Blend(LogReg+CatBoost-native), slices, calibration, error analysis."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor, build_preprocessor_native

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num + cat]
y = df["Churn"].values

folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(y)), y))
oof = np.zeros(len(df))
fold_roc = []
for tr_idx, va_idx in folds:
    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X.iloc[tr_idx])
    Xv = pre_native.transform(X.iloc[va_idx])
    cb = CatBoostClassifier(iterations=300, learning_rate=0.05, depth=6, cat_features=cat_idx,
                             auto_class_weights="Balanced", random_state=0, verbose=False)
    cb.fit(Xt, y[tr_idx])
    p_cb = cb.predict_proba(Xv)[:, 1]

    pre = build_preprocessor(num, cat)
    lr = Pipeline([("pre", pre), ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=0))])
    lr.fit(X.iloc[tr_idx], y[tr_idx])
    p_lr = lr.predict_proba(X.iloc[va_idx])[:, 1]

    blend = 0.5 * p_lr + 0.5 * p_cb
    oof[va_idx] = blend
    fold_roc.append(roc_auc_score(y[va_idx], blend))

fold_roc = np.array(fold_roc)
overall_roc = roc_auc_score(y, oof)
overall_pr = average_precision_score(y, oof)
print(f"Out-of-fold ROC-AUC: {overall_roc:.4f}  PR-AUC: {overall_pr:.4f}")
print(f"Per-fold ROC-AUC: {np.round(fold_roc, 4)}  mean={fold_roc.mean():.4f} std={fold_roc.std():.4f}")

df = df.copy()
df["oof_score"] = oof

# --- Calibration ---
df["score_decile"] = pd.qcut(df["oof_score"].rank(method="first"), q=10, labels=False)
decile_stats = df.groupby("score_decile").agg(
    mean_score=("oof_score", "mean"), actual_rate=("Churn", "mean"), n=("Churn", "size"))
print("\n=== Calibration by predicted decile ===")
print(decile_stats)

# --- Slice by Contract ---
CONTRACT_NAMES = {0: "Month-to-month", 1: "One year", 2: "Two year"}
df["ContractName"] = df["Contract"].map(CONTRACT_NAMES)
print("\n=== Slice by Contract ===")
slice_contract = df.groupby("ContractName", observed=True).apply(
    lambda g: pd.Series({
        "n": len(g), "churn_rate": g["Churn"].mean(),
        "ROC-AUC": roc_auc_score(g["Churn"], g["oof_score"]) if g["Churn"].nunique() > 1 else np.nan,
    }), include_groups=False)
print(slice_contract)

# --- Slice by tenure bucket ---
df["tenure_bucket"] = pd.cut(df["tenure"], bins=[-1, 6, 12, 24, 48, 100],
                              labels=["0-6mo", "7-12mo", "13-24mo", "25-48mo", "49mo+"])
print("\n=== Slice by tenure bucket ===")
slice_tenure = df.groupby("tenure_bucket", observed=True).apply(
    lambda g: pd.Series({
        "n": len(g), "churn_rate": g["Churn"].mean(),
        "ROC-AUC": roc_auc_score(g["Churn"], g["oof_score"]) if g["Churn"].nunique() > 1 else np.nan,
    }), include_groups=False)
print(slice_tenure)

# --- Slice by InternetService ---
print("\n=== Slice by InternetService ===")
slice_internet = df.groupby("InternetService", observed=True).apply(
    lambda g: pd.Series({
        "n": len(g), "churn_rate": g["Churn"].mean(),
        "ROC-AUC": roc_auc_score(g["Churn"], g["oof_score"]) if g["Churn"].nunique() > 1 else np.nan,
    }), include_groups=False)
print(slice_internet)

# --- Error analysis at frozen threshold ---
FROZEN_THRESHOLD = 0.3338
preds = (df["oof_score"] >= FROZEN_THRESHOLD).astype(int)
fn_mask = (preds == 0) & (df["Churn"] == 1)
fp_mask = (preds == 1) & (df["Churn"] == 0)
print(f"\n=== Missed churners (false negatives), {fn_mask.sum()} total, lowest-scored 5 ===")
print(df.loc[fn_mask, ["tenure", "Contract", "MonthlyCharges", "oof_score"]].sort_values("oof_score").head(5))
print(f"\n=== False alarms (false positives), {fp_mask.sum()} total, highest-scored 5 ===")
print(df.loc[fp_mask, ["tenure", "Contract", "MonthlyCharges", "oof_score"]].sort_values("oof_score", ascending=False).head(5))

df[["tenure", "Contract", "MonthlyCharges", "Churn", "oof_score"]].to_csv("artifacts/oof_predictions.csv", index=False)

# --- Figures ---
fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(decile_stats["mean_score"], decile_stats["actual_rate"], "o-", color="#C44E52", label="Observed")
lims = [0, 1]
ax.plot(lims, lims, "--", color="gray", label="Perfect calibration")
ax.set_xlabel("Mean predicted score per decile")
ax.set_ylabel("Actual churn rate per decile")
ax.set_title("Calibration by predicted-score decile (Blend)")
ax.legend()
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-calibration.png", dpi=110)
plt.close()

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(slice_contract.index.astype(str), slice_contract["ROC-AUC"], color="#4C72B0")
ax.axhline(overall_roc, color="#C44E52", linestyle="--", label=f"Overall ROC-AUC ({overall_roc:.4f})")
ax.set_ylabel("ROC-AUC")
ax.set_title("Out-of-fold ROC-AUC by Contract type")
ax.legend()
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/07-slice-performance.png", dpi=110)
plt.close()

print("\nFigures and OOF predictions written.")
