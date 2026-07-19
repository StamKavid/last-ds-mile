"""The real non-ML rival named in 00-frame.md/04-baseline.md but never scored
until now: the historical churn rate per Contract type (dev-only), applied to
held rows by their Contract value. This is the scored version of "target by
contract type using the historical rate" -- what a retention analyst would
actually compute without a model, using Contract, the single strongest
categorical driver found in 02-explore.md."""
from __future__ import annotations

import numpy as np
import pandas as pd


def contract_churn_rate(dev_df: pd.DataFrame, held_features_df: pd.DataFrame) -> np.ndarray:
    rate_by_contract = dev_df.groupby("Contract")["Churn"].mean()
    global_rate = dev_df["Churn"].mean()
    return held_features_df["Contract"].map(rate_by_contract).fillna(global_rate).to_numpy()
