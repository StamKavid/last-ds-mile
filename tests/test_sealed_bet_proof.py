import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.tree import DecisionTreeClassifier

from sealed_bet.score import open_seal, score_dev
from sealed_bet.seal import seal


def _make_dataset(tmp_path, seed=0, scale=30.0):
    rng = np.random.default_rng(seed)
    n = 600
    signal = rng.normal(size=n)
    # Default scale=30.0 (not 0.5): this is what test_optimistic_overfit_model_is_refused
    # needs. A moderately weak signal (e.g. scale=2.0) still lets the overfit tree
    # accidentally generalize often enough to clear the 2-sigma ship bar by pure luck:
    # a 100-seed sweep at scale=2.0 showed ~20-35% of seeds spuriously shipping. Scale
    # has to be pushed hard enough that "real" is fully drowned out by the noise columns
    # for the overfit-to-noise failure mode to be reliably caught -- at scale=30.0 a
    # 100-seed sweep shows only the statistical floor's ~2-3% false-ship rate (the same
    # irreducible Type-I rate any fixed 2-sigma threshold has for a genuinely zero-skill
    # model; no dataset scale can drive that below the threshold's own significance
    # level). Callers demonstrating a different property (e.g. estimate reliability) can
    # pass a different scale for a more/less separable dataset.
    y = (signal + rng.normal(scale=scale, size=n) > 0).astype(int)
    noise = rng.normal(size=(n, 20))  # 20 pure-noise columns
    df = pd.DataFrame(noise, columns=[f"n{i}" for i in range(20)])
    df["real"] = signal
    df["y"] = y
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    return data


def test_optimistic_overfit_model_is_refused(tmp_path):
    # scale=30.0: weak enough real signal that the overfit tree's noise-fitting
    # doesn't accidentally generalize to the sealed set (verified over a 100-seed
    # sweep -- see _make_dataset's comment for the full reasoning and numbers).
    data = _make_dataset(tmp_path, seed=0, scale=30.0)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)

    dev = pd.read_csv(out / "dev.csv")
    Xcols = [c for c in dev.columns if c != "y"]

    # The classic lie: an unregularized deep tree, scored by RESUBSTITUTION on dev
    # (train == eval). Reported dev ROC-AUC ≈ 1.0.
    overfit = DecisionTreeClassifier(random_state=0).fit(dev[Xcols], dev["y"])
    dev_pred = overfit.predict_proba(dev[Xcols])[:, 1]
    dev_auc = score_dev(dev["y"], dev_pred, "roc_auc", ledger_path=str(led),
                        note="deep tree, resubstitution (the lie)")
    assert dev_auc > 0.95  # looks glorious

    # Reality: same model, predicting the SEALED features it never saw.
    held_feats = pd.read_csv(out / "held" / "features.csv")
    held_pred = overfit.predict_proba(held_feats[Xcols])[:, 1]
    preds = tmp_path / "preds.csv"
    row_ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"]
    pd.DataFrame({"row_id": row_ids, "pred": held_pred}).to_csv(preds, index=False)

    result = open_seal(str(preds), str(out), str(led))
    assert result["shipped"] is False              # refused
    gap = dev_auc - result["sealed_score"]
    assert gap > 0.20                              # the dev−sealed gap is the tell
    assert "NOT SHIPPED" in led.read_text(encoding="utf-8")


def test_honest_model_ships(tmp_path):
    # More separable than the default (scale=0.5, not 2.0): this test is
    # demonstrating that an honest dev estimate is a reliable proxy for the
    # sealed score, which benefits from a comfortable, non-boundary-scraping
    # margin -- a different goal from test 1's "make the tree get confused".
    data = _make_dataset(tmp_path, seed=1, scale=0.5)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=1, ledger_path=str(led), ceiling_estimate=0.9)

    dev = pd.read_csv(out / "dev.csv")
    Xcols = [c for c in dev.columns if c != "y"]

    # Honest: out-of-fold CV predictions on dev, then a model trained on all dev.
    model = LogisticRegression(max_iter=1000)
    oof = cross_val_predict(model, dev[Xcols], dev["y"], cv=5, method="predict_proba")[:, 1]
    dev_auc = score_dev(dev["y"], oof, "roc_auc", ledger_path=str(led), note="logreg, 5-fold OOF")

    model.fit(dev[Xcols], dev["y"])
    held_feats = pd.read_csv(out / "held" / "features.csv")
    held_pred = model.predict_proba(held_feats[Xcols])[:, 1]
    preds = tmp_path / "preds.csv"
    row_ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"]
    pd.DataFrame({"row_id": row_ids, "pred": held_pred}).to_csv(preds, index=False)

    result = open_seal(str(preds), str(out), str(led))
    assert result["shipped"] is True               # beats baseline by > 2σ
    assert result["lift"] > 2.0
    gap = abs(dev_auc - result["sealed_score"])
    assert gap < 0.15                              # the honest estimate was a reliable proxy
