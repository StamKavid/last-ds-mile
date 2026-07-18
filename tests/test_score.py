import numpy as np
import pandas as pd
import pytest

from sealed_bet.score import open_seal, reveal
from sealed_bet.seal import seal


def _seal_a_problem(tmp_path):
    df = pd.DataFrame({"x": range(200), "y": [i % 2 for i in range(200)]})
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=0, ledger_path=str(tmp_path / "LEDGER.md"),
         ceiling_estimate=0.9)
    return out


def _write_preds(out, path, values):
    """Write preds.csv the way a correct pipeline does: row_id echoed from
    held/row_ids.csv, alongside the prediction."""
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"].to_numpy()
    pd.DataFrame({"row_id": ids, "pred": values}).to_csv(path, index=False)
    return path


def test_open_once_then_refuses_second_open(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    _write_preds(out, preds, np.full(n, 0.5))

    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert set(["sealed_score", "baseline", "sigma", "lift", "shipped"]).issubset(result)

    with pytest.raises(RuntimeError, match="already opened"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_open_seal_writes_a_revealed_csv_for_post_hoc_analysis(tmp_path):
    # /ds-evaluate and /ds-explain's own SKILL.md instruct producing a slice
    # table and feature importance "on the held set" -- this is the sanctioned
    # path for that now that the bet is settled, instead of no path at all.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    n = len(held)
    preds = tmp_path / "preds.csv"
    model_preds = (held["x"].to_numpy() % 2).astype(float)  # this dataset's y IS x % 2
    _write_preds(out, preds, model_preds)

    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    revealed_path = out / "held" / "revealed.csv"
    assert revealed_path.exists()
    revealed = pd.read_csv(revealed_path)
    assert list(revealed.columns) == ["y", "pred"]
    assert len(revealed) == n
    assert np.array_equal(revealed["pred"].to_numpy(), model_preds)
    # row order matches held/features.csv, so it can be joined with it directly
    assert np.array_equal(revealed["y"].to_numpy(), model_preds)  # y IS x % 2 here


def test_revealed_csv_is_not_blocked_by_the_seal_guard(tmp_path):
    import json
    import subprocess
    import sys as _sys
    from pathlib import Path

    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    _write_preds(out, preds, np.full(n, 0.5))
    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    hook = Path(__file__).resolve().parents[1] / "hooks" / "seal_guard.py"
    payload = json.dumps({"tool_name": "Read",
                          "tool_input": {"file_path": str(out / "held" / "revealed.csv")}})
    proc = subprocess.run([_sys.executable, str(hook)], input=payload,
                         capture_output=True, text=True)
    assert '"deny"' not in proc.stdout


def test_reveal_refuses_before_the_seal_is_opened(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    _write_preds(out, preds, np.full(n, 0.5))
    with pytest.raises(RuntimeError, match="refuses to run before"):
        reveal(str(out), str(preds))


def test_reveal_can_backfill_an_already_opened_seal(tmp_path):
    # The exact situation this was built for: a seal opened before reveal()
    # existed. reveal() must still work standalone once is_opened is True.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    preds = tmp_path / "preds.csv"
    model_preds = (held["x"].to_numpy() % 2).astype(float)
    _write_preds(out, preds, model_preds)
    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    (out / "held" / "revealed.csv").unlink()  # simulate a pre-reveal() historical seal
    revealed_path = reveal(str(out), str(preds))
    assert revealed_path == out / "held" / "revealed.csv"
    assert revealed_path.exists()


def test_constant_pred_does_not_ship(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    _write_preds(out, preds, np.full(n, 0.5))
    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert result["shipped"] is False  # no lift over a constant baseline


def test_open_seal_raises_a_clear_error_when_baseline_preds_missing(tmp_path):
    # Simulates a seal written before the paired-baseline fix: contract.json
    # and _sealed_target.csv exist but _sealed_baseline_preds.csv doesn't.
    # This must fail loudly, not silently fall back to a meaningless sigma --
    # the same "explain, don't guess" pattern Contract.load already uses for
    # a pre-Phase-C contract.json.
    out = _seal_a_problem(tmp_path)
    (out / "held" / "_sealed_baseline_preds.csv").unlink()
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    _write_preds(out, preds, np.full(n, 0.5))
    with pytest.raises(FileNotFoundError, match="_sealed_baseline_preds"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


# --- the prediction/label join ------------------------------------------------
#
# Predictions used to be matched to sealed labels by row POSITION alone. Row
# count was validated, order never was, so any pipeline that sorted or
# reindexed before writing preds.csv scored against the wrong labels with no
# error and no way to notice. These pin the fix.


def test_seal_writes_row_ids_for_the_scoring_join(tmp_path):
    out = _seal_a_problem(tmp_path)
    ids = pd.read_csv(out / "held" / "row_ids.csv")
    held = pd.read_csv(out / "held" / "features.csv")
    assert list(ids.columns) == ["row_id"]
    assert len(ids) == len(held)
    assert ids["row_id"].is_unique
    # row_id must NOT be inside the feature matrix: an id column is a row-order
    # proxy, and on sorted data that is a leakage vector.
    assert "row_id" not in held.columns


def test_shuffled_preds_score_identically_when_row_ids_are_carried(tmp_path):
    # THE point of the fix. The same predictions, shuffled, must produce the
    # same verdict -- order in preds.csv is now irrelevant because the join is
    # on identity.
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    out_a = _seal_a_problem(tmp_path / "a")
    held_a = pd.read_csv(out_a / "held" / "features.csv")
    ids_a = pd.read_csv(out_a / "held" / "row_ids.csv")["row_id"].to_numpy()
    model_preds = (held_a["x"].to_numpy() % 2).astype(float)

    in_order = tmp_path / "in_order.csv"
    pd.DataFrame({"row_id": ids_a, "pred": model_preds}).to_csv(in_order, index=False)
    score_in_order = open_seal(str(in_order), str(out_a), str(tmp_path / "A.md"))

    # identical seal, identical predictions, but the rows are shuffled
    out_b = _seal_a_problem(tmp_path / "b")
    shuffled = (
        pd.DataFrame({"row_id": ids_a, "pred": model_preds})
        .sample(frac=1, random_state=7)
        .reset_index(drop=True)
    )
    shuffled_path = tmp_path / "shuffled.csv"
    shuffled.to_csv(shuffled_path, index=False)
    score_shuffled = open_seal(str(shuffled_path), str(out_b), str(tmp_path / "B.md"))

    assert score_shuffled["sealed_score"] == pytest.approx(score_in_order["sealed_score"])


def test_shuffled_preds_would_have_scored_wrong_under_positional_join(tmp_path):
    # Proves the bug was real rather than theoretical: the SAME shuffled file,
    # joined positionally, produces a materially different (wrong) score. This
    # is what used to happen silently on every run.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"].to_numpy()
    model_preds = (held["x"].to_numpy() % 2).astype(float)  # perfect predictions

    shuffled_path = tmp_path / "shuffled.csv"
    (
        pd.DataFrame({"row_id": ids, "pred": model_preds})
        .sample(frac=1, random_state=3)
        .reset_index(drop=True)
        .to_csv(shuffled_path, index=False)
    )
    wrong = open_seal(str(shuffled_path), str(out), str(tmp_path / "LEDGER.md"),
                      unsafe_positional_join=True)
    # perfect predictions scored against shuffled labels collapse toward chance
    assert wrong["sealed_score"] < 0.75


def test_preds_without_row_id_are_refused_with_actionable_instructions(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    with pytest.raises(ValueError, match="no 'row_id' column"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_preds_missing_a_held_row_are_refused(tmp_path):
    out = _seal_a_problem(tmp_path)
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"].to_numpy()
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"row_id": ids[:-1], "pred": np.full(len(ids) - 1, 0.5)}).to_csv(
        preds, index=False
    )
    with pytest.raises(ValueError, match="do not match the sealed held set"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_preds_with_a_duplicate_row_id_are_refused(tmp_path):
    out = _seal_a_problem(tmp_path)
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"].to_numpy()
    dupes = ids.copy()
    dupes[-1] = dupes[0]  # one row predicted twice, another not at all
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"row_id": dupes, "pred": np.full(len(ids), 0.5)}).to_csv(
        preds, index=False
    )
    with pytest.raises(ValueError, match="duplicate row_id"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_legacy_seal_without_row_ids_still_opens_positionally(tmp_path):
    # Backward compatibility: seals written before row_ids.csv existed have no
    # identity to join on, so the positional read stays available for them.
    out = _seal_a_problem(tmp_path)
    (out / "held" / "row_ids.csv").unlink()  # simulate a pre-fix seal
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert "sealed_score" in result


def test_revealed_csv_rows_align_with_held_order_after_a_shuffled_submission(tmp_path):
    # reveal() must apply the same join, or the post-hoc slice/calibration
    # analysis in /ds-evaluate would read from misaligned rows.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"].to_numpy()
    model_preds = (held["x"].to_numpy() % 2).astype(float)

    shuffled_path = tmp_path / "shuffled.csv"
    (
        pd.DataFrame({"row_id": ids, "pred": model_preds})
        .sample(frac=1, random_state=11)
        .reset_index(drop=True)
        .to_csv(shuffled_path, index=False)
    )
    open_seal(str(shuffled_path), str(out), str(tmp_path / "LEDGER.md"))

    revealed = pd.read_csv(out / "held" / "revealed.csv")
    # y IS x % 2 in this fixture, so a correctly aligned reveal has them equal
    assert np.array_equal(revealed["pred"].to_numpy(), model_preds)
    assert np.array_equal(revealed["y"].to_numpy(), model_preds)


def test_open_seal_against_a_heuristic_baseline_uses_paired_sigma(tmp_path):
    # A model that's only marginally better than a strong heuristic baseline
    # should ship with a modest, not astronomical, lift -- proving the paired
    # sigma (and a real baseline_fn) actually constrains the verdict, instead
    # of every non-broken model scoring 20-30 sigma against a constant 0.5.
    df = pd.DataFrame({"x": range(300), "y": [i % 2 for i in range(300)]})
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"

    def heuristic(dev_df, held_features_df):
        return (held_features_df["x"].to_numpy() % 2).astype(float)  # this dataset's y IS x % 2

    contract = seal(str(data), "y", "classification", "roc_auc", str(out),
                    strategy="random", seed=0, ledger_path=str(tmp_path / "LEDGER.md"),
                    ceiling_estimate=0.99, baseline_fn=heuristic)
    assert contract.baseline_score > 0.9  # the heuristic already nails this dataset

    held = pd.read_csv(out / "held" / "features.csv")
    # a model barely better than the heuristic on a couple of rows
    model_preds = (held["x"].to_numpy() % 2).astype(float)
    model_preds[:2] = 1.0 - model_preds[:2]
    preds_path = tmp_path / "preds.csv"
    _write_preds(out, preds_path, model_preds)

    result = open_seal(str(preds_path), str(out), str(tmp_path / "LEDGER.md"))
    assert result["lift"] < 20.0  # nowhere near the old constant-baseline-style blowout
