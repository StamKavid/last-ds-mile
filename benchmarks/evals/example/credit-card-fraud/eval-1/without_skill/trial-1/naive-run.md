# without_skill run (ILLUSTRATIVE naive baseline)

> Hand-authored to represent a common un-disciplined output. NOT a captured agent run.

```
df = pd.read_csv("creditcard.csv")
X, y = df.drop(columns="Class"), df["Class"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)
clf = RandomForestClassifier().fit(Xtr, ytr)
print("Accuracy:", accuracy_score(yte, clf.predict(Xte)))            # 0.9994
print("ROC-AUC :", roc_auc_score(yte, clf.predict_proba(Xte)[:,1]))  # 0.96
```

**Conclusion:** "The model is 99.94% accurate with a 0.96 ROC-AUC - it performs
excellently at detecting fraud and looks ready to ship."
