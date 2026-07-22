"""Battle-test: does the shipped Blend(LightGBM+CatBoost)'s PR-AUC hold up across
different CV splitter seeds, or was seed=42 a lucky draw? Model seeds fixed at 0 so
variation is attributable to the split, not to re-randomizing every axis at once."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import average_precision_score
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num]
y = df["Class"].values

SEEDS = [42, 1, 7, 123, 2024]
run_means, run_stds = [], []

for seed in SEEDS:
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y))
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
        fold_pr.append(average_precision_score(y[va_idx], blend))
    fold_pr = np.array(fold_pr)
    run_means.append(fold_pr.mean())
    run_stds.append(fold_pr.std())
    print(f"seed={seed:5d}  folds={np.round(fold_pr, 4)}  mean={fold_pr.mean():.4f}  std={fold_pr.std():.4f}")

run_means = np.array(run_means)
print(f"\nAcross {len(SEEDS)} independent seed splits:")
print(f"  Mean of means: {run_means.mean():.4f}")
print(f"  Std across seeds: {run_means.std():.4f}")
print(f"  Range: [{run_means.min():.4f}, {run_means.max():.4f}]")
