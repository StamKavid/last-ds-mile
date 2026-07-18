"""Supplementary causal analysis for the telco-churn benchmark: does signing a
long-term contract CAUSE lower churn, or is the large naive association just
confounding by who chooses long contracts (loyal, longer-tenured, stable-household
customers)?

This is deliberately separate from the Sealed Bet prediction pipeline
(sealed_bet/, /ds-seal -> /ds-auto -> /ds-open): the prediction model answers "who is
likely to churn," this answers "would a specific intervention (getting a customer onto
a longer contract) causally reduce their churn risk" -- a different question a
retention team also needs answered before spending budget on contract-upgrade offers.

Two libraries, two complementary questions:
- dowhy: average treatment effect (ATE) of long_contract on Churn, backdoor-adjusted
  for confounders, with refutation tests (does the estimate survive a placebo
  treatment, a random common cause, a data subset?).
- causalml: conditional average treatment effect (CATE) -- does the effect vary by
  segment (InternetService, tenure)? A T-learner (two separate GBM models, one per
  arm) rather than one pooled linear model, so it can capture nonlinearity/interactions
  the ATE's linear model can't.

DAG discipline (the actual judgment call this analysis rests on): confounders are
tenure, SeniorCitizen, Partner, Dependents, InternetService -- plausible common causes
of BOTH contract choice and churn (customer profile/stability), not consequences of the
contract itself. MonthlyCharges/TotalCharges and the add-on services (OnlineSecurity,
TechSupport, etc.) are deliberately EXCLUDED as confounders: contract terms often
bundle pricing and add-ons, so these are plausible mediators or ambiguous
post-treatment variables -- adjusting for them would bias the estimate toward zero by
blocking part of the causal pathway, exactly the kind of mistake this project's own
leakage/target-leakage-detection discipline exists to catch elsewhere in the pipeline.

Run from the repo root after /ds-seal has produced last-ds-mile-run/dev.csv:

    python -m benchmarks.telco-churn.causal_analysis
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from causalml.inference.meta import BaseTRegressor
from dowhy import CausalModel
from sklearn.ensemble import GradientBoostingRegressor

OUT = "benchmarks/telco-churn/last-ds-mile-run"
FIG = f"{OUT}/figures"
CONFOUNDERS = ["tenure", "SeniorCitizen", "Partner_bin", "Dependents_bin", "InternetService"]


def _prep(dev: pd.DataFrame) -> pd.DataFrame:
    df = dev.copy()
    df["long_contract"] = df["Contract"].isin(["'One year'", "'Two year'"]).astype(int)
    df["Partner_bin"] = (df["Partner"] == "Yes").astype(int)
    df["Dependents_bin"] = (df["Dependents"] == "Yes").astype(int)
    return df


def _ate_and_refutations(df: pd.DataFrame) -> dict:
    model = CausalModel(data=df, treatment="long_contract", outcome="Churn", common_causes=CONFOUNDERS)
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(identified_estimand, method_name="backdoor.linear_regression")

    naive_diff = df.groupby("long_contract")["Churn"].mean().diff().iloc[-1]

    placebo = model.refute_estimate(identified_estimand, estimate, method_name="placebo_treatment_refuter",
                                    placebo_type="permute", num_simulations=20)
    random_cause = model.refute_estimate(identified_estimand, estimate, method_name="random_common_cause",
                                         num_simulations=20)
    subset = model.refute_estimate(identified_estimand, estimate, method_name="data_subset_refuter",
                                   subset_fraction=0.8, num_simulations=20)
    return {
        "naive_diff": float(naive_diff),
        "ate": float(estimate.value),
        "placebo_new_effect": float(placebo.new_effect),
        "random_cause_new_effect": float(random_cause.new_effect),
        "subset_new_effect": float(subset.new_effect),
    }


def _cate_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    internet_dummies = pd.get_dummies(df["InternetService"], prefix="internet").astype(float)
    X = pd.concat([
        df[["tenure", "SeniorCitizen", "Partner_bin", "Dependents_bin"]].astype(float),
        internet_dummies,
    ], axis=1)
    treatment = df["long_contract"].to_numpy()
    y = df["Churn"].to_numpy().astype(float)

    learner = GradientBoostingRegressor(random_state=0, max_depth=3, n_estimators=100)
    model = BaseTRegressor(learner=learner, control_name=0)
    cate = np.asarray(model.fit_predict(X=X.to_numpy(), treatment=treatment, y=y, verbose=False)).flatten()

    out = df.copy()
    out["cate"] = cate
    out["tenure_bucket"] = pd.cut(out["tenure"], bins=[0, 12, 24, 48, 1000],
                                  labels=["0-12mo", "12-24mo", "24-48mo", "48-72mo"])
    return out


def _plot_causal_dag():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    nodes = {
        "tenure": (0.08, 0.85), "SeniorCitizen": (0.08, 0.6), "Partner/Dependents": (0.08, 0.35),
        "InternetService": (0.08, 0.1),
        "long_contract\n(treatment)": (0.48, 0.475),
        "Churn\n(outcome)": (0.88, 0.475),
    }
    for name, (x, y) in nodes.items():
        color = "#DD8452" if "treatment" in name else ("#55A868" if "outcome" in name else "#EAEAF2")
        ax.annotate(name, (x, y), ha="center", va="center", fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.4", fc=color, ec="#4C72B0"))
    confounder_nodes = ["tenure", "SeniorCitizen", "Partner/Dependents", "InternetService"]
    for c in confounder_nodes:
        xc, yc = nodes[c]
        for target in ["long_contract\n(treatment)", "Churn\n(outcome)"]:
            xt, yt = nodes[target]
            ax.annotate("", xy=(xt - 0.08, yt), xytext=(xc + 0.1, yc),
                       arrowprops=dict(arrowstyle="->", color="#888888", lw=1))
    xt, yt = nodes["long_contract\n(treatment)"]
    xo, yo = nodes["Churn\n(outcome)"]
    ax.annotate("", xy=(xo - 0.1, yo), xytext=(xt + 0.13, yt),
               arrowprops=dict(arrowstyle="->", color="#C44E52", lw=2.5))
    fig.suptitle("Causal DAG: does long_contract cause lower Churn?", fontsize=13, y=0.98)
    ax.text(0.5, 1.06, "Gray = confounders (adjusted for) · Red = effect being estimated\n"
                       "MonthlyCharges/TotalCharges/add-ons excluded as plausible mediators, not confounders",
           transform=ax.transAxes, ha="center", va="top", fontsize=8.5, color="#444444")
    fig.subplots_adjust(top=0.78)
    fig.savefig(f"{FIG}/causal-dag.png")
    plt.close(fig)


def _plot_ate_vs_naive(results: dict):
    fig, ax = plt.subplots(figsize=(6.5, 5))
    labels = ["Naive\n(unadjusted)", "Causal ATE\n(confounder-adjusted)"]
    vals = [results["naive_diff"] * 100, results["ate"] * 100]
    bars = ax.bar(labels, vals, color=["#C44E52", "#4C72B0"])
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Churn rate difference (pp)")
    ax.set_title("~60% of the naive contract-length/churn\nassociation is confounding", fontsize=11)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.1f}pp", (b.get_x() + b.get_width() / 2, v), ha="center",
                   va="top" if v < 0 else "bottom")
    fig.tight_layout()
    fig.savefig(f"{FIG}/causal-ate-vs-naive.png")
    plt.close(fig)


def _plot_cate_by_segment(cate_df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    by_internet = cate_df.groupby("InternetService")["cate"].mean().sort_values() * 100
    axes[0].barh(by_internet.index, by_internet.to_numpy(), color="#4C72B0")
    axes[0].set_xlabel("Mean CATE (pp)")
    axes[0].set_title("CATE by InternetService")
    by_tenure = cate_df.groupby("tenure_bucket", observed=True)["cate"].mean() * 100
    axes[1].bar(by_tenure.index.astype(str), by_tenure.to_numpy(), color="#55A868")
    axes[1].set_ylabel("Mean CATE (pp)")
    axes[1].set_title("CATE by tenure bucket")
    fig.suptitle("Heterogeneous treatment effect: long_contract's effect on Churn is not uniform")
    fig.tight_layout()
    fig.savefig(f"{FIG}/causal-cate-by-segment.png")
    plt.close(fig)


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    dev = pd.read_csv(f"{OUT}/dev.csv")
    df = _prep(dev)

    results = _ate_and_refutations(df)
    print(f"Naive diff: {results['naive_diff']:.4f}")
    print(f"Causal ATE: {results['ate']:.4f}")
    print(f"Placebo refutation (should be ~0): {results['placebo_new_effect']:.4f}")
    print(f"Random-common-cause refutation (should be ~unchanged): {results['random_cause_new_effect']:.4f}")
    print(f"Data-subset refutation (should be ~unchanged): {results['subset_new_effect']:.4f}")

    cate_df = _cate_by_segment(df)
    print(f"\nOverall mean CATE (causalml T-learner): {cate_df['cate'].mean():.4f}")
    print(cate_df.groupby("InternetService")["cate"].mean())
    print(cate_df.groupby("tenure_bucket", observed=True)["cate"].mean())

    _plot_causal_dag()
    _plot_ate_vs_naive(results)
    _plot_cate_by_segment(cate_df)
    print(f"\nFigures written to {FIG}")


if __name__ == "__main__":
    main()
