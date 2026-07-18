"""Generate the critical, hypothesis-driven figures for the telco-churn benchmark:
churn-by-contract, tenure relationship, calibration, slice AUC, feature importance
(ensemble + best base learner), SHAP summary, and a lite hypothesis DAG.

Run from the repo root after /ds-seal + /ds-auto + /ds-open have produced
last-ds-mile-run/{dev.csv, held/features.csv, held/revealed.csv, auto/refit/}:

    python -m benchmarks.telco-churn.generate_figures
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from autogluon.tabular import TabularPredictor
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OrdinalEncoder

OUT = "benchmarks/telco-churn/last-ds-mile-run"
FIG = f"{OUT}/figures"


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    dev = pd.read_csv(f"{OUT}/dev.csv")
    held = pd.read_csv(f"{OUT}/held/features.csv")
    revealed = pd.read_csv(f"{OUT}/held/revealed.csv")
    target = "Churn"
    feature_cols = [c for c in dev.columns if c != target]

    plt.rcParams.update({"figure.dpi": 110, "font.size": 10})

    _churn_by_contract(dev, target)
    _tenure_relationship(dev, target)
    y_true, y_pred = _calibration(revealed, target)
    _slice_performance(held, y_true, y_pred)
    predictor = TabularPredictor.load(f"{OUT}/auto/refit", require_version_match=False)
    _feature_importance(predictor, held, target, y_true)
    _shap_summary(predictor, dev, held, feature_cols)
    _hypothesis_dag()
    print("All telco-churn figures written to", FIG)


def _churn_by_contract(dev, target):
    rates = dev.groupby("Contract")[target].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(rates.index, rates.to_numpy() * 100, color="#C44E52")
    ax.set_ylim(0, max(rates.to_numpy() * 100) * 1.2)
    ax.set_ylabel("Churn rate (%)")
    ax.set_title("Churn rate by Contract type — the single strongest driver")
    for b, v in zip(bars, rates.to_numpy() * 100):
        ax.annotate(f"{v:.1f}%", (b.get_x() + b.get_width() / 2, v), ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(f"{FIG}/02-churn-by-contract.png")
    plt.close(fig)


def _tenure_relationship(dev, target):
    bins = [0, 12, 24, 48, 1000]
    bin_labels = ["0-12mo", "12-24mo", "24-48mo", "48-72mo"]
    dev_binned = dev.assign(tenure_bucket=pd.cut(dev["tenure"], bins=bins, labels=bin_labels))
    rates_t = dev_binned.groupby("tenure_bucket", observed=True)[target].mean()
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(rates_t.index.astype(str), rates_t.to_numpy() * 100, marker="o", color="#4C72B0")
    ax.set_ylim(0, max(rates_t.to_numpy() * 100) * 1.2)
    ax.set_ylabel("Churn rate (%)")
    ax.set_xlabel("Tenure bucket")
    ax.set_title("Churn rate decays monotonically with tenure")
    fig.tight_layout()
    fig.savefig(f"{FIG}/02-tenure-relationship.png")
    plt.close(fig)


def _calibration(revealed, target):
    y_true = revealed[target].to_numpy()
    y_pred = revealed["pred"].to_numpy()
    order = np.argsort(y_pred)
    deciles = np.array_split(order, 10)
    mean_pred = [y_pred[idx].mean() for idx in deciles]
    actual_rate = [y_true[idx].mean() for idx in deciles]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "--", color="gray", label="perfect calibration")
    ax.plot(mean_pred, actual_rate, marker="o", color="#55A868", label="observed deciles")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Actual churn rate")
    ax.set_title("Calibration: predicted deciles track actual rate closely")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{FIG}/07-calibration.png")
    plt.close(fig)
    return y_true, y_pred


def _slice_performance(held, y_true, y_pred):
    aucs, ns = {}, {}
    for c in held["Contract"].unique():
        mask = (held["Contract"] == c).to_numpy()
        aucs[c] = roc_auc_score(y_true[mask], y_pred[mask])
        ns[c] = int(mask.sum())
    order_c = sorted(aucs, key=aucs.get)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(order_c, [aucs[c] for c in order_c], color=["#C44E52", "#DD8452", "#55A868"])
    ax.axhline(0.8268, ls="--", color="gray", label="overall AUC 0.8268")
    ax.set_ylim(0, 1)
    ax.set_ylabel("AUC (within-slice)")
    ax.set_title("Within-slice AUC is much lower than the overall number")
    ax.legend()
    for b, c in zip(bars, order_c):
        ax.annotate(f"{aucs[c]:.3f}\n(n={ns[c]})", (b.get_x() + b.get_width() / 2, aucs[c]),
                   ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(f"{FIG}/07-slice-performance.png")
    plt.close(fig)


def _feature_importance(predictor, held, target, y_true):
    held_labeled = held.copy()
    held_labeled[target] = y_true
    imp_ensemble = predictor.feature_importance(data=held_labeled, silent=True)["importance"].head(9)

    leaderboard = predictor.leaderboard(silent=True)
    best_base = leaderboard[leaderboard["model"] != "WeightedEnsemble_L2"].iloc[0]["model"]
    imp_base = predictor.feature_importance(data=held_labeled, model=best_base, silent=True)["importance"].head(9)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    idx = np.arange(len(imp_ensemble))
    width = 0.38
    ax.barh(idx + width / 2, imp_ensemble.to_numpy()[::-1], height=width, label="Ensemble (winner)", color="#4C72B0")
    base_vals = imp_base.reindex(imp_ensemble.index).fillna(0).to_numpy()
    ax.barh(idx - width / 2, base_vals[::-1], height=width, label=f"{best_base} (best single model)", color="#DD8452")
    ax.set_yticks(idx)
    ax.set_yticklabels(imp_ensemble.index[::-1])
    ax.set_xlabel("Permutation importance")
    ax.set_title("Feature importance: ensemble vs. best single base model")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{FIG}/08-feature-importance.png")
    plt.close(fig)
    print(f"Best single base model: {best_base}")


def _shap_summary(predictor, dev, held, feature_cols):
    cat_cols = [c for c in feature_cols if dev[c].dtype == object]
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    enc.fit(dev[cat_cols].astype(str))

    def _encode(df):
        out = df[feature_cols].copy()
        out[cat_cols] = enc.transform(df[cat_cols].astype(str))
        num_cols = [c for c in feature_cols if c not in cat_cols]
        out[num_cols] = out[num_cols].apply(pd.to_numeric, errors="coerce")
        return out.astype(float)

    def _decode(x2d):
        out = pd.DataFrame(x2d, columns=feature_cols)
        codes = out[cat_cols].round().astype(int).clip(lower=0)
        out[cat_cols] = enc.inverse_transform(codes)
        return out

    def _predict(x2d):
        return predictor.predict_proba(_decode(x2d), as_multiclass=False).to_numpy()

    rng = np.random.default_rng(0)
    background = _encode(dev.sample(30, random_state=0)).to_numpy()
    explain_n = min(60, len(held))
    explain_idx = rng.choice(len(held), size=explain_n, replace=False)
    explain_X = _encode(held.iloc[explain_idx]).to_numpy()

    explainer = shap.Explainer(_predict, background, feature_names=feature_cols)
    sv = explainer(explain_X, max_evals=100)

    fig = plt.figure(figsize=(7, 5))
    shap.summary_plot(sv.values, features=explain_X, feature_names=feature_cols,
                      show=False, max_display=12, plot_size=None)
    plt.title(f"SHAP summary — {explain_n} held rows, P(Churn) ensemble predict_proba as black box")
    plt.tight_layout()
    plt.savefig(f"{FIG}/08-shap-summary.png", dpi=110)
    plt.close(fig)


def _hypothesis_dag():
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")
    nodes = {
        "Contract length": (0.05, 0.85), "Switching cost /\ncommitment": (0.35, 0.85),
        "tenure": (0.05, 0.5),
        "InternetService\n(Fiber optic)": (0.05, 0.15), "Price sensitivity /\nservice perception": (0.35, 0.15),
        "MonthlyCharges": (0.6, 0.3),
        "Churn": (0.85, 0.5),
    }
    for name, (x, y) in nodes.items():
        ax.annotate(name, (x, y), ha="center", va="center",
                   bbox=dict(boxstyle="round,pad=0.4", fc="#EAEAF2", ec="#4C72B0"))
    edges = [
        ("Contract length", "Switching cost /\ncommitment"),
        ("Switching cost /\ncommitment", "Churn"),
        ("tenure", "Churn"),
        ("InternetService\n(Fiber optic)", "Price sensitivity /\nservice perception"),
        ("Price sensitivity /\nservice perception", "Churn"),
        ("InternetService\n(Fiber optic)", "MonthlyCharges"),
    ]
    for a, b in edges:
        xa, ya = nodes[a]; xb, yb = nodes[b]
        ax.annotate("", xy=(xb - 0.08, yb), xytext=(xa + 0.12, ya),
                   arrowprops=dict(arrowstyle="->", color="#55A868", lw=1.5))
    ax.set_title("Hypothesized structure behind Churn (from 02-explore.md's hypothesis log)\n"
                "— a diagram of stated reasoning, not a fitted causal model")
    fig.tight_layout()
    fig.savefig(f"{FIG}/08-hypothesis-dag.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
