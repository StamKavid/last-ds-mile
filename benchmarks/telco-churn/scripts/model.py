"""Stage 6 — candidate comparison for telco-churn.

Primary metric: ROC-AUC (moderate imbalance, 26.5% churn — not severe enough for
ROC-AUC to be misleading the way it is at credit-card-fraud's 0.17%, per
metric-selection). PR-AUC reported alongside as the stricter secondary check anyway,
per metric-selection's own rationalization table ("ROC-AUC is standard, I'll just
report that" — check PR-AUC too).
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor, build_preprocessor_native

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num + cat]
y = df["Churn"].values
pos_rate = y.mean()
scale_pos_weight = (1 - pos_rate) / pos_rate
print(f"Rows: {len(df)}  churned: {y.sum()}  rate: {pos_rate:.4f}  scale_pos_weight: {scale_pos_weight:.2f}")


def build_cv_splitter(y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))


folds = build_cv_splitter(y)

results = {}
fold_train_auc = {}
oof_by_model = {}

# --- One-hot-based candidates ---
onehot_candidates = {
    "LogReg(balanced)": LogisticRegression(class_weight="balanced", max_iter=2000, random_state=0),
    "RandomForest(balanced)": RandomForestClassifier(
        n_estimators=300, max_depth=8, class_weight="balanced", random_state=0, n_jobs=-1),
    "LightGBM": LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=15,
                                scale_pos_weight=scale_pos_weight, verbosity=-1, random_state=0),
    "XGBoost": XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=4,
                              scale_pos_weight=scale_pos_weight, random_state=0, verbosity=0),
}

for name, model in onehot_candidates.items():
    pre = build_preprocessor(num, cat)
    pipe = Pipeline([("pre", pre), ("model", model)])
    roc_scores, pr_scores, train_roc = [], [], []
    oof = np.zeros(len(df))
    for tr_idx, va_idx in folds:
        pipe.fit(X.iloc[tr_idx], y[tr_idx])
        proba_va = pipe.predict_proba(X.iloc[va_idx])[:, 1]
        proba_tr = pipe.predict_proba(X.iloc[tr_idx])[:, 1]
        roc_scores.append(roc_auc_score(y[va_idx], proba_va))
        pr_scores.append(average_precision_score(y[va_idx], proba_va))
        train_roc.append(roc_auc_score(y[tr_idx], proba_tr))
        oof[va_idx] = proba_va
    roc_scores, pr_scores = np.array(roc_scores), np.array(pr_scores)
    results[name] = (roc_scores.mean(), roc_scores.std(), pr_scores.mean(), pr_scores.std())
    fold_train_auc[name] = np.mean(train_roc)
    oof_by_model[name] = oof
    print(f"{name:24s} ROC-AUC={roc_scores.mean():.4f}±{roc_scores.std():.4f}  "
          f"PR-AUC={pr_scores.mean():.4f}±{pr_scores.std():.4f}  "
          f"train_ROC={np.mean(train_roc):.4f}  gap={np.mean(train_roc)-roc_scores.mean():.4f}")

# --- CatBoost, native categorical handling ---
roc_scores, pr_scores, train_roc = [], [], []
cat_oof = np.zeros(len(df))
for tr_idx, va_idx in folds:
    pre_native, cat_idx = build_preprocessor_native(num, cat)
    Xt = pre_native.fit_transform(X.iloc[tr_idx])
    Xv = pre_native.transform(X.iloc[va_idx])
    model = CatBoostClassifier(iterations=300, learning_rate=0.05, depth=6, cat_features=cat_idx,
                                auto_class_weights="Balanced", random_state=0, verbose=False)
    model.fit(Xt, y[tr_idx])
    proba_va = model.predict_proba(Xv)[:, 1]
    proba_tr = model.predict_proba(Xt)[:, 1]
    roc_scores.append(roc_auc_score(y[va_idx], proba_va))
    pr_scores.append(average_precision_score(y[va_idx], proba_va))
    train_roc.append(roc_auc_score(y[tr_idx], proba_tr))
    cat_oof[va_idx] = proba_va
roc_scores, pr_scores = np.array(roc_scores), np.array(pr_scores)
results["CatBoost(native cat)"] = (roc_scores.mean(), roc_scores.std(), pr_scores.mean(), pr_scores.std())
fold_train_auc["CatBoost(native cat)"] = np.mean(train_roc)
oof_by_model["CatBoost(native cat)"] = cat_oof
print(f"{'CatBoost(native cat)':24s} ROC-AUC={roc_scores.mean():.4f}±{roc_scores.std():.4f}  "
      f"PR-AUC={pr_scores.mean():.4f}±{pr_scores.std():.4f}  "
      f"train_ROC={np.mean(train_roc):.4f}  gap={np.mean(train_roc)-roc_scores.mean():.4f}")

# --- Blend: LogReg (linear, very different error shape) + CatBoost-native ---
blend_oof = 0.5 * oof_by_model["LogReg(balanced)"] + 0.5 * oof_by_model["CatBoost(native cat)"]
blend_roc = np.array([roc_auc_score(y[va_idx], blend_oof[va_idx]) for _, va_idx in folds])
blend_pr = np.array([average_precision_score(y[va_idx], blend_oof[va_idx]) for _, va_idx in folds])
results["Blend(LogReg+CatBoost)"] = (blend_roc.mean(), blend_roc.std(), blend_pr.mean(), blend_pr.std())
oof_by_model["Blend(LogReg+CatBoost)"] = blend_oof
print(f"{'Blend(LogReg+CatBoost)':24s} ROC-AUC={blend_roc.mean():.4f}±{blend_roc.std():.4f}  "
      f"PR-AUC={blend_pr.mean():.4f}±{blend_pr.std():.4f}")

print("\n=== Full comparison (ROC-AUC primary) ===")
for name, (roc_m, roc_s, pr_m, pr_s) in sorted(results.items(), key=lambda kv: -kv[1][0]):
    print(f"{name:26s} ROC-AUC={roc_m:.4f}±{roc_s:.4f}  PR-AUC={pr_m:.4f}±{pr_s:.4f}")

best_name = max(results, key=lambda k: results[k][0])
best_roc, best_roc_std, best_pr, best_pr_std = results[best_name]
print(f"\nBest candidate: {best_name}  ROC-AUC={best_roc:.4f}±{best_roc_std:.4f}")

baseline_roc = 0.5
baseline_pr = pos_rate
print(f"Baseline (majority-class): ROC-AUC={baseline_roc}  PR-AUC={baseline_pr:.4f}")
print(f"Lift over baseline (ROC-AUC): {best_roc - baseline_roc:.4f}  (candidate std: {best_roc_std:.4f})  "
      f"exceeds std? {(best_roc - baseline_roc) > best_roc_std}")

if best_name in fold_train_auc:
    print(f"\nBias/variance check ({best_name}): train_ROC={fold_train_auc[best_name]:.4f}  "
          f"val_ROC={best_roc:.4f}  gap={fold_train_auc[best_name]-best_roc:.4f}")

# --- Threshold freezing: max F2 on OOF predictions of the winner ---
best_oof = oof_by_model[best_name]
precisions, recalls, thresholds = precision_recall_curve(y, best_oof)
f2_scores = (5 * precisions * recalls) / (4 * precisions + recalls + 1e-12)
best_idx = np.nanargmax(f2_scores[:-1])
frozen_threshold = thresholds[best_idx]
print(f"\nFrozen threshold (max F2 on OOF): {frozen_threshold:.4f}  "
      f"precision={precisions[best_idx]:.4f}  recall={recalls[best_idx]:.4f}  F2={f2_scores[best_idx]:.4f}")
preds_at_threshold = (best_oof >= frozen_threshold).astype(int)
tp = int(((preds_at_threshold == 1) & (y == 1)).sum())
fp = int(((preds_at_threshold == 1) & (y == 0)).sum())
fn = int(((preds_at_threshold == 0) & (y == 1)).sum())
print(f"At frozen threshold: TP={tp}  FP={fp}  FN={fn}  (catches {tp}/{tp+fn} churners, {fp} false alarms)")
