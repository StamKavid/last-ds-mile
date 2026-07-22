"""Re-verify /ds-iterate Loop 1 against the CORRECTED shipped model (Blend), not the
old single one-hot CatBoost. Same diagnosis, same fix, same paired-fold discipline."""
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

OUTLIER_IDS = [524, 1299]
outlier_mask = train["Id"].isin(OUTLIER_IDS)


def build_cv_splitter(df, n_splits=5, seed=42):
    price_bins = pd.qcut(df["logSalePrice"], q=5, labels=False)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(df, price_bins))


folds = build_cv_splitter(train)


def fit_blend_fold(tr_idx, va_idx):
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
    return 0.5 * pred_lgbm + 0.5 * pred_cb


before_rmses, after_rmses = [], []
oof_before, oof_after = np.zeros(len(train)), np.zeros(len(train))
for tr_idx, va_idx in folds:
    pred_before = fit_blend_fold(tr_idx, va_idx)
    oof_before[va_idx] = pred_before
    before_rmses.append(np.sqrt(mean_squared_error(y[va_idx], pred_before)))

    tr_idx_clean = np.array([i for i in tr_idx if not outlier_mask.iloc[i]])
    pred_after = fit_blend_fold(tr_idx_clean, va_idx)
    oof_after[va_idx] = pred_after
    after_rmses.append(np.sqrt(mean_squared_error(y[va_idx], pred_after)))

before_rmses, after_rmses = np.array(before_rmses), np.array(after_rmses)
print("BEFORE (all rows):", np.round(before_rmses, 4), "mean=%.4f std=%.4f" % (before_rmses.mean(), before_rmses.std()))
print("AFTER (outliers excluded from training):", np.round(after_rmses, 4), "mean=%.4f std=%.4f" % (after_rmses.mean(), after_rmses.std()))
print("Paired per-fold diff (before-after):", np.round(before_rmses - after_rmses, 4))
print("Mean paired diff: %.4f" % (before_rmses - after_rmses).mean())

edwards_mask = (train["Neighborhood"] == "Edwards").values
rmse_edwards_before = np.sqrt(mean_squared_error(y[edwards_mask], oof_before[edwards_mask]))
rmse_edwards_after = np.sqrt(mean_squared_error(y[edwards_mask], oof_after[edwards_mask]))
print("\nEdwards RMSE before: %.4f  after: %.4f" % (rmse_edwards_before, rmse_edwards_after))

rmse_overall_before = np.sqrt(mean_squared_error(y, oof_before))
rmse_overall_after = np.sqrt(mean_squared_error(y, oof_after))
print("Overall OOF RMSE before: %.4f  after: %.4f" % (rmse_overall_before, rmse_overall_after))
