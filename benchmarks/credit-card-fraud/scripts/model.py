"""Stage 6 — candidate comparison for credit-card-fraud.

Primary metric: PR-AUC (average precision), per metric-selection's imbalanced-
classification row — ROC-AUC stays misleadingly high under 0.17% fraud because it's
dominated by the easy majority-class true-negative rate. ROC-AUC reported alongside
as a secondary sanity check, never as the ranking metric.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, fbeta_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num]
y = df["Class"].values
pos_rate = y.mean()
scale_pos_weight = (1 - pos_rate) / pos_rate
print(f"Rows after dedup: {len(df)}  fraud: {y.sum()}  rate: {pos_rate:.5f}  "
      f"scale_pos_weight: {scale_pos_weight:.1f}")


def build_cv_splitter(y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))


def temporal_holdout_mask(df):
    return df["day"] == 0, df["day"] == 1


folds = build_cv_splitter(y)

candidates = {
    "LogReg(balanced)": Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=0)),
    ]),
    "RandomForest(balanced)": RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=0, n_jobs=-1),
    # NOTE: scale_pos_weight (LightGBM's usual imbalance knob) collapses at this
    # dataset's extreme ~599:1 ratio -- verified directly: PR-AUC 0.017 vs. 0.887
    # for the identical model swapped to class_weight="balanced" on a held split.
    # LightGBM's scale_pos_weight scales the gradient directly and appears to hit a
    # numerical-stability wall combined with default min_child_samples at this ratio;
    # class_weight="balanced" computes per-sample weights a different, more stable
    # way internally. XGBoost and CatBoost's own scale_pos_weight/auto_class_weights
    # equivalents did NOT show this problem at the same ratio -- a LightGBM-specific
    # gotcha, not a general finding about scale_pos_weight.
    "LightGBM": LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=31, class_weight="balanced",
        verbosity=-1, random_state=0),
    "XGBoost": XGBClassifier(
        n_estimators=400, learning_rate=0.05, max_depth=5, scale_pos_weight=scale_pos_weight,
        random_state=0, verbosity=0),
    "CatBoost": CatBoostClassifier(
        iterations=400, learning_rate=0.05, depth=6, auto_class_weights="Balanced",
        random_state=0, verbose=False),
}

results = {}
fold_train_pr = {}
oof_by_model = {}

for name, model in candidates.items():
    pr_scores, roc_scores, train_pr_scores = [], [], []
    oof = np.zeros(len(df))
    for tr_idx, va_idx in folds:
        model.fit(X.iloc[tr_idx], y[tr_idx])
        proba_va = model.predict_proba(X.iloc[va_idx])[:, 1]
        proba_tr = model.predict_proba(X.iloc[tr_idx])[:, 1]
        pr_scores.append(average_precision_score(y[va_idx], proba_va))
        roc_scores.append(roc_auc_score(y[va_idx], proba_va))
        train_pr_scores.append(average_precision_score(y[tr_idx], proba_tr))
        oof[va_idx] = proba_va
    pr_scores, roc_scores = np.array(pr_scores), np.array(roc_scores)
    results[name] = (pr_scores.mean(), pr_scores.std(), roc_scores.mean(), roc_scores.std())
    fold_train_pr[name] = np.mean(train_pr_scores)
    oof_by_model[name] = oof
    print(f"{name:24s} PR-AUC={pr_scores.mean():.4f}±{pr_scores.std():.4f}  "
          f"ROC-AUC={roc_scores.mean():.4f}±{roc_scores.std():.4f}  "
          f"train_PR={np.mean(train_pr_scores):.4f}  gap={np.mean(train_pr_scores)-pr_scores.mean():.4f}")

# --- Try two blend pairings, per model-ensembling: pick candidates likely to err
# differently, but verify with the actual OOF comparison rather than assume which
# pairing is more diverse. ---
for blend_name, (name_a, name_b) in {
    "Blend(LightGBM+CatBoost)": ("LightGBM", "CatBoost"),
    "Blend(LogReg+CatBoost)": ("LogReg(balanced)", "CatBoost"),
}.items():
    blend_oof = 0.5 * oof_by_model[name_a] + 0.5 * oof_by_model[name_b]
    blend_pr = np.array([average_precision_score(y[va_idx], blend_oof[va_idx]) for _, va_idx in folds])
    blend_roc = np.array([roc_auc_score(y[va_idx], blend_oof[va_idx]) for _, va_idx in folds])
    results[blend_name] = (blend_pr.mean(), blend_pr.std(), blend_roc.mean(), blend_roc.std())
    oof_by_model[blend_name] = blend_oof
    print(f"{blend_name:24s} PR-AUC={blend_pr.mean():.4f}±{blend_pr.std():.4f}  "
          f"ROC-AUC={blend_roc.mean():.4f}±{blend_roc.std():.4f}")

print("\n=== Full comparison (PR-AUC primary) ===")
for name, (pr_m, pr_s, roc_m, roc_s) in sorted(results.items(), key=lambda kv: -kv[1][0]):
    print(f"{name:26s} PR-AUC={pr_m:.4f}±{pr_s:.4f}  ROC-AUC={roc_m:.4f}±{roc_s:.4f}")

best_name = max(results, key=lambda k: results[k][0])
best_pr, best_pr_std, best_roc, best_roc_std = results[best_name]
print(f"\nBest candidate: {best_name}  PR-AUC={best_pr:.4f}±{best_pr_std:.4f}")

baseline_pr = pos_rate  # a classifier with no skill scores PR-AUC == base rate
print(f"Baseline (majority-class / no-skill) PR-AUC: {baseline_pr:.5f}  ROC-AUC: 0.5")
print(f"Lift over baseline: {best_pr - baseline_pr:.4f}  (candidate std: {best_pr_std:.4f})  "
      f"exceeds std? {(best_pr - baseline_pr) > best_pr_std}")

if best_name in fold_train_pr:
    print(f"\nBias/variance check ({best_name}): train_PR={fold_train_pr[best_name]:.4f}  "
          f"val_PR={best_pr:.4f}  gap={fold_train_pr[best_name]-best_pr:.4f}")

# --- Threshold freezing (new ds-model step): choose on OOF validation predictions
# only, using F2 (recall weighted 2x precision -- missing fraud costs more than a
# false alarm, per metric-selection), frozen before any further evaluation. ---
best_oof = oof_by_model[best_name]
precisions, recalls, thresholds = precision_recall_curve(y, best_oof)
f2_scores = (5 * precisions * recalls) / (4 * precisions + recalls + 1e-12)
best_idx = np.nanargmax(f2_scores[:-1])
frozen_threshold = thresholds[best_idx]
print(f"\nFrozen threshold (max F2 on OOF): {frozen_threshold:.4f}  "
      f"precision={precisions[best_idx]:.4f}  recall={recalls[best_idx]:.4f}  "
      f"F2={f2_scores[best_idx]:.4f}")
preds_at_threshold = (best_oof >= frozen_threshold).astype(int)
tp = int(((preds_at_threshold == 1) & (y == 1)).sum())
fp = int(((preds_at_threshold == 1) & (y == 0)).sum())
fn = int(((preds_at_threshold == 0) & (y == 1)).sum())
print(f"At frozen threshold: TP={tp}  FP={fp}  FN={fn}  "
      f"(catches {tp}/{tp+fn} fraud cases, {fp} false alarms among {len(y)-y.sum():.0f} genuine txns)")

# --- One-time temporal robustness check ---
train_mask, holdout_mask = temporal_holdout_mask(df)
if "LightGBM" in best_name or "CatBoost" in best_name or "Blend" in best_name:
    m1 = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                         scale_pos_weight=scale_pos_weight, verbosity=-1, random_state=0)
    m1.fit(X[train_mask], y[train_mask])
    p1 = m1.predict_proba(X[holdout_mask])[:, 1]
    m2 = CatBoostClassifier(iterations=400, learning_rate=0.05, depth=6,
                             auto_class_weights="Balanced", random_state=0, verbose=False)
    m2.fit(X[train_mask], y[train_mask])
    p2 = m2.predict_proba(X[holdout_mask])[:, 1]
    holdout_pred = 0.5 * p1 + 0.5 * p2
else:
    m = candidates[best_name]
    m.fit(X[train_mask], y[train_mask])
    holdout_pred = m.predict_proba(X[holdout_mask])[:, 1]

holdout_pr = average_precision_score(y[holdout_mask], holdout_pred)
holdout_roc = roc_auc_score(y[holdout_mask], holdout_pred)
print(f"\nTemporal holdout (train=day0, test=day1, n={holdout_mask.sum()}): "
      f"PR-AUC={holdout_pr:.4f}  ROC-AUC={holdout_roc:.4f}")
