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


def test_reseal_after_open_does_not_destroy_prior_holdout(tmp_path):
    import pytest
    from sealed_bet.state import mark_opened

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led))

    original_target_bytes = (out / "held" / "_sealed_target.csv").read_bytes()
    original_contract_bytes = (out / "contract.json").read_bytes()
    mark_opened(out)

    with pytest.raises(RuntimeError, match="already opened"):
        seal(str(data), target="y", task="classification", metric="roc_auc",
             out_dir=str(out), strategy="random", seed=1, ledger_path=str(led))

    # the ORIGINAL sealed holdout must be completely untouched by the refused re-seal
    assert (out / "held" / "_sealed_target.csv").read_bytes() == original_target_bytes
    assert (out / "contract.json").read_bytes() == original_contract_bytes


def test_seal_records_a_probe_verdict_in_the_ledger(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led))
    text = led.read_text(encoding="utf-8")
    assert "train-vs-held AUC" in text
    assert "probe skipped" not in text.lower()


def test_seal_survives_a_probe_failure(tmp_path, monkeypatch):
    import sealed_bet.seal as seal_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated probe failure")

    monkeypatch.setattr(seal_module, "split_adversary", _boom)

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    # seal() must still succeed and write its core artifacts even if the probe blows up
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0, ledger_path=str(led))
    assert (out / "contract.json").exists()
    assert contract.metric == "roc_auc"
    text = led.read_text(encoding="utf-8")
    assert "probe skipped" in text.lower()
