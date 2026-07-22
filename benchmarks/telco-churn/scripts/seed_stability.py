"""Battle-test: does the Blend's 0.8477 ROC-AUC hold up across different CV splitter
seeds? Model seeds fixed at 0 so variation is attributable to the split."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from catboost import CatBoostClassifier

from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor_native

df = prepare_full()
num, cat = get_feature_lists(df)
X = df[num + cat]
y = df["Churn"].values

SEEDS = [42, 1, 7, 123, 2024]
run_means, run_stds = [], []

for seed in SEEDS:
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y))
    fold_roc = []
    for tr_idx, va_idx in folds:
        pre_native, cat_idx = build_preprocessor_native(num, cat)
        Xt = pre_native.fit_transform(X.iloc[tr_idx])
        Xv = pre_native.transform(X.iloc[va_idx])
        cb = CatBoostClassifier(iterations=300, learning_rate=0.05, depth=6, cat_features=cat_idx,
                                 auto_class_weights="Balanced", random_state=0, verbose=False)
        cb.fit(Xt, y[tr_idx])
        p_cb = cb.predict_proba(Xv)[:, 1]

        from sklearn.pipeline import Pipeline
        from pipeline_lib import build_preprocessor
        pre = build_preprocessor(num, cat)
        lr = Pipeline([("pre", pre), ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=0))])
        lr.fit(X.iloc[tr_idx], y[tr_idx])
        p_lr = lr.predict_proba(X.iloc[va_idx])[:, 1]

        blend = 0.5 * p_lr + 0.5 * p_cb
        fold_roc.append(roc_auc_score(y[va_idx], blend))
    fold_roc = np.array(fold_roc)
    run_means.append(fold_roc.mean())
    run_stds.append(fold_roc.std())
    print(f"seed={seed:5d}  folds={np.round(fold_roc, 4)}  mean={fold_roc.mean():.4f}  std={fold_roc.std():.4f}")

run_means = np.array(run_means)
print(f"\nAcross {len(SEEDS)} independent seed splits:")
print(f"  Mean of means: {run_means.mean():.4f}")
print(f"  Std across seeds: {run_means.std():.4f}")
print(f"  Range: [{run_means.min():.4f}, {run_means.max():.4f}]")
