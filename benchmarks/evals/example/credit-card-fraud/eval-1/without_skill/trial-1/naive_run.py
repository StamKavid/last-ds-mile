"""without_skill naive run (credit-card-fraud) — reproducible, real numbers.

Represents a common un-disciplined approach: train a classifier, report accuracy and
ROC-AUC on a plain random split, and call it done. No baseline, no PR-AUC, no operating
point, no stratification of the 0.167% positive class. The numbers this prints are what
the without_skill grading is judged against — run it to reproduce them.
"""
import pathlib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

REPO = pathlib.Path(__file__).resolve().parents[7]
df = pd.read_csv(REPO / "benchmarks/credit-card-fraud/creditcard.csv")
X, y = df.drop(columns="Class"), df["Class"]

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)  # not stratified
clf = RandomForestClassifier(random_state=0, n_jobs=-1).fit(Xtr, ytr)
acc = accuracy_score(yte, clf.predict(Xte))
auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])

print(f"Accuracy: {acc:.4f}")
print(f"ROC-AUC : {auc:.4f}")
print(f'Conclusion: "The model is {acc*100:.1f}% accurate with a {auc:.2f} ROC-AUC '
      '- it performs excellently at detecting fraud and looks ready to ship."')
