"""Stage 2 EDA — univariate + bivariate passes, exports the figures /ds-explore requires."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

train = pd.read_csv("train.csv")
train["logSalePrice"] = np.log1p(train["SalePrice"])

print("=== SalePrice skew ===")
print("raw skew:", train["SalePrice"].skew())
print("log1p skew:", train["logSalePrice"].skew())

print("\n=== top numeric correlations with logSalePrice ===")
num = train.select_dtypes("number")
corr = num.corr()["logSalePrice"].drop(["SalePrice", "logSalePrice", "Id"]).sort_values(ascending=False)
print(corr.head(10))
print(corr.tail(5))

print("\n=== collinearity among top features ===")
top_feats = corr.head(6).index.tolist()
print(num[top_feats].corr().round(2))

# --- Figure 1: target distribution, raw vs log ---
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].hist(train["SalePrice"], bins=40, color="#4C72B0")
axes[0].set_title("SalePrice (raw) — skew %.2f" % train["SalePrice"].skew())
axes[0].set_xlabel("SalePrice ($)")
axes[1].hist(train["logSalePrice"], bins=40, color="#55A868")
axes[1].set_title("log1p(SalePrice) — skew %.2f" % train["logSalePrice"].skew())
axes[1].set_xlabel("log1p(SalePrice)")
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/02-target-distribution.png", dpi=110)
plt.close()

# --- Figure 2: strongest bivariate relationship ---
# strongest is OverallQual, a 10-level ordinal — a raw scatter overplots into vertical
# stripes at each integer and hides the within-level spread. A boxplot per level shows
# the median/IQR/outliers at each quality level, the honest way to show an
# ordinal-vs-continuous relationship (flagged in review of the first pass, which used
# a plain scatter here).
strongest = corr.index[0]
fig, ax = plt.subplots(figsize=(7, 4.5))
levels = sorted(train[strongest].unique())
data_by_level = [train.loc[train[strongest] == lvl, "logSalePrice"].values for lvl in levels]
bp = ax.boxplot(data_by_level, tick_labels=levels, patch_artist=True)
for patch in bp["boxes"]:
    patch.set_facecolor("#4C72B0")
    patch.set_alpha(0.6)
ax.set_xlabel(strongest)
ax.set_ylabel("log1p(SalePrice)")
ax.set_title(f"{strongest} vs log(SalePrice) — r={corr[strongest]:.2f} (boxplot per level)")
plt.tight_layout()
plt.savefig(".last-ds-mile/figures/02-top-correlation.png", dpi=110)
plt.close()

print("\nStrongest bivariate relationship:", strongest, "r=%.3f" % corr[strongest])

# Check a couple of near-perfect-separation candidates (leakage-shape red flag)
print("\n=== any feature suspiciously close to target? ===")
print(corr[corr.abs() > 0.7])
