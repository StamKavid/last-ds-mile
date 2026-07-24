"""without_skill naive run (house-prices) — reproducible, real numbers.

Represents a common un-disciplined approach: fit a model on the numeric columns,
report RMSE and R^2 on the SAME rows it trained on (in-sample), in raw dollars, and
call it done. No baseline, no log transform on a target spanning orders of magnitude,
no out-of-fold evaluation. The numbers this prints are what the without_skill grading
is judged against — run it to reproduce them.
"""
import pathlib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error

REPO = pathlib.Path(__file__).resolve().parents[7]
df = pd.read_csv(REPO / "benchmarks/house-prices/train.csv").select_dtypes("number").fillna(0)
X, y = df.drop(columns="SalePrice"), df["SalePrice"]

model = RandomForestRegressor(random_state=0, n_jobs=-1).fit(X, y)
pred = model.predict(X)                      # scored on the training rows themselves
rmse = root_mean_squared_error(y, pred)
r2 = model.score(X, y)

print(f"RMSE: ${rmse:,.0f}")
print(f"R^2 : {r2:.4f}")
print(f'Conclusion: "The model predicts sale price within about ${rmse:,.0f} '
      f'with an R-squared of {r2:.2f} - very accurate."')
