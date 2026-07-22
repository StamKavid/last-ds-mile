"""Battle-test: does the Blend's 0.1244 RMSE hold up across different random seeds,
or was it a lucky draw on seed=42's specific fold split? Runs the full CV comparison
5 times with different splitter seeds (model seeds fixed, since re-randomizing every
axis at once would make it impossible to attribute variation to the split vs. the model)."""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
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

SEEDS = [42, 1, 7, 123, 2024]
run_means, run_stds = [], []

for seed in SEEDS:
    price_bins = pd.qcut(train["logSalePrice"], q=5, labels=False)
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=seed).split(train, price_bins))

    fold_rmses = []
    for tr_idx, va_idx in folds:
        pre = build_preprocessor(num, cat)
        lgbm = LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=16, verbosity=-1, random_state=0)
        pipe = Pipeline([("pre", pre), ("model", lgbm)])
        pipe.fit(X.iloc[tr_idx], y[tr_idx])
        pred_lgbm = pipe.predict(X.iloc[va_idx])

        pre_native, cat_idx = build_preprocessor_native(num, cat)
        Xt = pre_native.fit_transform(X.iloc[tr_idx])
        Xv = pre_native.transform(X.iloc[va_idx])
        cb = CatBoostRegressor(iterations=600, learning_rate=0.03, depth=6, cat_features=cat_idx,
                                random_state=0, verbose=False)
        cb.fit(Xt, y[tr_idx])
        pred_cb = cb.predict(Xv)

        blend = 0.5 * pred_lgbm + 0.5 * pred_cb
        fold_rmses.append(np.sqrt(mean_squared_error(y[va_idx], blend)))

    fold_rmses = np.array(fold_rmses)
    run_means.append(fold_rmses.mean())
    run_stds.append(fold_rmses.std())
    print(f"seed={seed:5d}  folds={np.round(fold_rmses, 4)}  mean={fold_rmses.mean():.4f}  std={fold_rmses.std():.4f}")

run_means = np.array(run_means)
print(f"\nAcross {len(SEEDS)} independent seed splits:")
print(f"  Mean of means: {run_means.mean():.4f}")
print(f"  Std across seeds (seed-to-seed variability): {run_means.std():.4f}")
print(f"  Range: [{run_means.min():.4f}, {run_means.max():.4f}]")
print(f"  Original single-seed (42) result: 0.1244 -- within range: {run_means.min() <= 0.1244 <= run_means.max()}")
