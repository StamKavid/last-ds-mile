"""Generate the critical, hypothesis-driven figures for the house-prices benchmark:
target distribution, top correlations, slice performance, feature importance
(ensemble + cross-checked against the best single base learner), SHAP summary,
and a lite hypothesis DAG -- matching data-viz-standards' "state the hypothesis
first" discipline, not aimless plotting.

Run from the repo root after /ds-seal + /ds-auto + /ds-open have produced
last-ds-mile-run/{dev.csv, held/features.csv, held/revealed.csv, auto/refit/}:

    python -m benchmarks.house-prices.generate_figures
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from autogluon.tabular import TabularPredictor
from sklearn.preprocessing import OrdinalEncoder

OUT = "benchmarks/house-prices/last-ds-mile-run"
FIG = f"{OUT}/figures"


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    dev = pd.read_csv(f"{OUT}/dev.csv")
    held = pd.read_csv(f"{OUT}/held/features.csv")
    revealed = pd.read_csv(f"{OUT}/held/revealed.csv")
    target = "log_saleprice"
    feature_cols = [c for c in dev.columns if c != target]

    plt.rcParams.update({"figure.dpi": 110, "font.size": 10})

    _target_distribution(dev, target)
    _top_correlations(dev, feature_cols, target)
    y_true, y_pred = _slice_performance(revealed, target)
    predictor = TabularPredictor.load(f"{OUT}/auto/refit", require_version_match=False)
    _feature_importance(predictor, held, target, y_true)
    _shap_summary(predictor, dev, held, feature_cols)
    _hypothesis_dag()
    print("All house-prices figures written to", FIG)


def _target_distribution(dev, target):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    price = np.expm1(dev[target])
    axes[0].hist(price, bins=40, color="#4C72B0")
    axes[0].set_title(f"SalePrice (skew={price.skew():.2f})")
    axes[0].set_xlabel("SalePrice ($)")
    axes[1].hist(dev[target], bins=40, color="#55A868")
    axes[1].set_title(f"log1p(SalePrice) (skew={dev[target].skew():.2f})")
    axes[1].set_xlabel("log1p(SalePrice)")
    fig.suptitle("Target distribution: log transform corrects the right-skew")
    fig.tight_layout()
    fig.savefig(f"{FIG}/02-target-distribution.png")
    plt.close(fig)


def _top_correlations(dev, feature_cols, target):
    num_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(dev[c])]
    corrs = dev[[*num_cols, target]].corr()[target].drop(target).abs().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(corrs.index[::-1], corrs.to_numpy()[::-1], color="#4C72B0")
    ax.set_xlim(0, 1)
    ax.set_xlabel("|correlation| with log(SalePrice)")
    ax.set_title("Top 10 numeric features by |correlation| with target")
    fig.tight_layout()
    fig.savefig(f"{FIG}/02-top-correlations.png")
    plt.close(fig)


def _slice_performance(revealed, target):
    y_true = revealed[target].to_numpy()
    y_pred = revealed["pred"].to_numpy()
    price_true = np.expm1(y_true)
    order = np.argsort(price_true)
    tercile_idx = np.array_split(order, 3)
    labels = ["Low\n($35k-$137k)", "Mid\n($137k-$190k)", "High\n($190k-$612k)"]
    rmses = [float(np.sqrt(np.mean((y_true[idx] - y_pred[idx]) ** 2))) for idx in tercile_idx]
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(labels, rmses, color=["#C44E52", "#55A868", "#55A868"])
    ax.set_ylim(0, max(rmses) * 1.25)
    ax.set_ylabel("RMSE (log scale)")
    ax.set_title("Slice performance by price tercile — low tier is the weak spot")
    for b, v in zip(bars, rmses):
        ax.annotate(f"{v:.3f}", (b.get_x() + b.get_width() / 2, v), ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(f"{FIG}/07-slice-performance.png")
    plt.close(fig)
    return y_true, y_pred


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
    # Explains the ACTUAL shipped ensemble (a black-box callable), not a proxy
    # base model -- avoids AutoGluon's internal per-model preprocessing, which
    # is fragile/version-specific to reach into directly (verified: CatBoost's
    # raw native .predict() rejects a NaN-containing category column even
    # after predictor.transform_features(), so explaining the real
    # predictor.predict is both simpler AND more honest about what this model
    # card actually ships).
    cat_cols = [c for c in feature_cols if dev[c].dtype == object]
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    enc.fit(dev[cat_cols].astype(str))

    def _encode(df):
        out = df[feature_cols].copy()
        out[cat_cols] = enc.transform(df[cat_cols].astype(str))
        return out.astype(float)

    def _decode(x2d):
        out = pd.DataFrame(x2d, columns=feature_cols)
        codes = out[cat_cols].round().astype(int).clip(lower=0)
        out[cat_cols] = enc.inverse_transform(codes)
        return out

    def _predict(x2d):
        return predictor.predict(_decode(x2d)).to_numpy()

    rng = np.random.default_rng(0)
    background = _encode(dev.sample(30, random_state=0)).to_numpy()
    explain_n = min(60, len(held))
    explain_idx = rng.choice(len(held), size=explain_n, replace=False)
    explain_X = _encode(held.iloc[explain_idx]).to_numpy()

    explainer = shap.Explainer(_predict, background, feature_names=feature_cols)
    sv = explainer(explain_X, max_evals=250)

    fig = plt.figure(figsize=(7, 5))
    shap.summary_plot(sv.values, features=explain_X, feature_names=feature_cols,
                      show=False, max_display=12, plot_size=None)
    plt.title(f"SHAP summary — {explain_n} held rows, ensemble predict() as black box")
    plt.tight_layout()
    plt.savefig(f"{FIG}/08-shap-summary.png", dpi=110)
    plt.close(fig)


def _hypothesis_dag():
    # Visualizes 02-explore.md's Hypothesis log, not a fitted causal model --
    # see BENCHMARKS.md / this run's scope decision on causal analysis.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")
    nodes = {
        "OverallQual": (0.05, 0.8), "GrLivArea": (0.05, 0.55), "TotalBsmtSF/1stFlrSF": (0.05, 0.3),
        "GarageCars/GarageArea": (0.05, 0.05), "Neighborhood": (0.4, 0.9),
        "House size/quality\n(bundled signal)": (0.4, 0.4),
        "log(SalePrice)": (0.85, 0.5),
    }
    for name, (x, y) in nodes.items():
        ax.annotate(name, (x, y), ha="center", va="center",
                   bbox=dict(boxstyle="round,pad=0.4", fc="#EAEAF2", ec="#4C72B0"))
    edges = [
        ("OverallQual", "House size/quality\n(bundled signal)"),
        ("GrLivArea", "House size/quality\n(bundled signal)"),
        ("TotalBsmtSF/1stFlrSF", "House size/quality\n(bundled signal)"),
        ("GarageCars/GarageArea", "House size/quality\n(bundled signal)"),
        ("House size/quality\n(bundled signal)", "log(SalePrice)"),
        ("Neighborhood", "log(SalePrice)"),
    ]
    for a, b in edges:
        xa, ya = nodes[a]; xb, yb = nodes[b]
        ax.annotate("", xy=(xb - 0.06, yb), xytext=(xa + 0.1, ya),
                   arrowprops=dict(arrowstyle="->", color="#55A868", lw=1.5))
    ax.set_title("Hypothesized structure behind SalePrice (from 02-explore.md's hypothesis log)\n"
                "— a diagram of stated reasoning, not a fitted causal model")
    fig.tight_layout()
    fig.savefig(f"{FIG}/08-hypothesis-dag.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
