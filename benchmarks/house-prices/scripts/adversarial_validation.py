"""distribution-shift check: adversarial validation between train and Kaggle test.csv.

Labels every train row 0 and every test row 1, cross-validates a classifier's ability
to tell them apart. AUC near 0.5 = same distribution; AUC >> 0.5 = real shift.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from lightgbm import LGBMClassifier
from pipeline_lib import prepare_full, get_feature_lists, build_preprocessor
from sklearn.pipeline import Pipeline

train, test = prepare_full()
num, cat = get_feature_lists(train)

combined = pd.concat([train[num + cat], test[num + cat]], axis=0, ignore_index=True)
labels = np.array([0] * len(train) + [1] * len(test))

pre = build_preprocessor(num, cat)
clf = Pipeline([
    ("pre", pre),
    ("clf", LGBMClassifier(n_estimators=200, max_depth=4, verbosity=-1, random_state=0)),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_val_score(clf, combined, labels, cv=cv, scoring="roc_auc")
print("Adversarial validation AUC per fold:", np.round(scores, 4))
print("Mean AUC: %.4f  Std: %.4f" % (scores.mean(), scores.std()))

# Fit once on everything to inspect which features drive the separation
clf.fit(combined, labels)
importances = clf.named_steps["clf"].feature_importances_
feat_names = clf.named_steps["pre"].get_feature_names_out()
imp_series = pd.Series(importances, index=feat_names).sort_values(ascending=False)
print("\nTop 10 features driving train/test separation:")
print(imp_series.head(10))
