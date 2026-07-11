import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.tree import DecisionTreeClassifier

from sealed_bet.seal import seal
from sealed_bet.score import open_seal, score_dev


def _make_dataset(tmp_path, seed=0):
    rng = np.random.default_rng(seed)
    n = 600
    signal = rng.normal(size=n)
    # scale=2.0 (not 0.5): a single strong feature is so separable that even
    # a fully overfit tree finds it via the top splits and generalizes anyway.
    # Weakening the label's signal-to-noise ratio here is what actually lets
    # the tree get confused between the real feature and the 20 noise columns
    # -- reproducing the "looks great in dev, collapses on the seal" failure
    # this test exists to catch, while leaving enough real signal for an
    # honestly cross-validated model to clear the 2-sigma ship bar.
    y = (signal + rng.normal(scale=2.0, size=n) > 0).astype(int)
    noise = rng.normal(size=(n, 20))  # 20 pure-noise columns
    df = pd.DataFrame(noise, columns=[f"n{i}" for i in range(20)])
    df["real"] = signal
    df["y"] = y
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    return data


def test_optimistic_overfit_model_is_refused(tmp_path):
    data = _make_dataset(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=0, ledger_path=str(led))

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
    pd.DataFrame({"pred": held_pred}).to_csv(preds, index=False)

    result = open_seal(str(preds), str(out), str(led))
    assert result["shipped"] is False              # refused
    gap = dev_auc - result["sealed_score"]
    assert gap > 0.20                              # the dev−sealed gap is the tell
    assert "NOT SHIPPED" in led.read_text(encoding="utf-8")


def test_honest_model_ships(tmp_path):
    data = _make_dataset(tmp_path, seed=1)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=1, ledger_path=str(led))

    dev = pd.read_csv(out / "dev.csv")
    Xcols = [c for c in dev.columns if c != "y"]

    # Honest: out-of-fold CV predictions on dev, then a model trained on all dev.
    model = LogisticRegression(max_iter=1000)
    oof = cross_val_predict(model, dev[Xcols], dev["y"], cv=5, method="predict_proba")[:, 1]
    score_dev(dev["y"], oof, "roc_auc", ledger_path=str(led), note="logreg, 5-fold OOF")

    model.fit(dev[Xcols], dev["y"])
    held_feats = pd.read_csv(out / "held" / "features.csv")
    held_pred = model.predict_proba(held_feats[Xcols])[:, 1]
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": held_pred}).to_csv(preds, index=False)

    result = open_seal(str(preds), str(out), str(led))
    assert result["shipped"] is True               # beats baseline by > 2σ
    assert result["lift"] > 2.0
