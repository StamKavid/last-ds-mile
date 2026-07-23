# without_skill run (ILLUSTRATIVE naive baseline)

> Hand-authored to represent a common un-disciplined output. NOT a captured agent run.

```
df = pd.read_csv("train.csv").select_dtypes("number").fillna(0)
X, y = df.drop(columns="SalePrice"), df["SalePrice"]
model = RandomForestRegressor().fit(X, y)
print("RMSE:", mean_squared_error(y, model.predict(X), squared=False))  # ~$28,000
print("R^2 :", model.score(X, y))                                       # 0.98
```

**Conclusion:** "The model predicts sale price within about $28k with an R-squared of
0.98 - very accurate."
