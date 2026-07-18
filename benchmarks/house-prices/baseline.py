"""The real non-ML rival named in 00-frame.md/04-baseline.md but never scored
until now: a neighborhood-median $/sqft lookup, computed on dev only and
applied to held rows' GrLivArea. Returns log1p(SalePrice) predictions to match
the sealed metric (rmse of log1p(SalePrice))."""
from __future__ import annotations

import numpy as np
import pandas as pd


def neighborhood_price_per_sqft(dev_df: pd.DataFrame, held_features_df: pd.DataFrame) -> np.ndarray:
    price = np.expm1(dev_df["log_saleprice"])
    rate_by_neighborhood = (price / dev_df["GrLivArea"]).groupby(dev_df["Neighborhood"]).median()
    global_rate = rate_by_neighborhood.median()
    per_row_rate = held_features_df["Neighborhood"].map(rate_by_neighborhood).fillna(global_rate)
    pred_price = per_row_rate.to_numpy() * held_features_df["GrLivArea"].to_numpy()
    return np.log1p(np.maximum(pred_price, 0.0))
