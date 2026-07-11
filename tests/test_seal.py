import hashlib
import pandas as pd

from sealed_bet.seal import seal


def _write_csv(tmp_path):
    df = pd.DataFrame({"x": range(100), "y": [i % 2 for i in range(100)]})
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    return p


def test_seal_creates_artifacts_and_hides_labels(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0,
         ledger_path=str(tmp_path / "LEDGER.md"))

    assert (out / "contract.json").exists()
    assert (out / "dev.csv").exists()
    assert (out / "held" / "features.csv").exists()
    assert (out / "held" / "_sealed_target.csv").exists()
    # the readable held features must NOT contain the target column
    feats = pd.read_csv(out / "held" / "features.csv")
    assert "y" not in feats.columns
    # ledger header written
    assert "Contract" in (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
