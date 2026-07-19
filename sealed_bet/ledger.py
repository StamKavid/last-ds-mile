"""The append-only LEDGER.md: Contract header, experiments, and the final verdict."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sealed_bet.contract import Contract


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_header(ledger_path, contract: Contract) -> None:
    lines = [
        "# The Sealed Bet — LEDGER",
        "",
        "## Contract",
        f"- target: `{contract.target}`  ·  task: `{contract.task}`  ·  metric: `{contract.metric}`",
        f"- split: `{contract.split['strategy']}`  ·  baseline_score: `{contract.baseline_score:.4f}` "
        f"(`{contract.baseline_kind}`)",
        f"- ceiling_score: `{contract.ceiling_score:.4f}`  ·  ceiling_source: `{contract.ceiling_source}`  ·  budget: `{contract.budget}`",
        f"- input_mode: `{contract.input_mode}`  ·  data_hash: `{contract.data_hash}`  ·  sealed_at: `{_now()}`",
        "",
        "## Experiments (dev only — none of these count yet)",
        "",
    ]
    Path(ledger_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_experiment(ledger_path, note: str, dev_score: float) -> None:
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(f"- {_now()} · {note} → dev {dev_score:.4f}\n")


def append_verdict(ledger_path, sealed_score: float, baseline_score: float,
                   sigma: float, lift_val: float, shipped: bool) -> None:
    gap = sealed_score - baseline_score
    stamp = "SHIPPED ✅" if shipped else "NOT SHIPPED ⛔"
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write("\n## Verdict (seal opened once)\n")
        f.write(f"- sealed_score: {sealed_score:.4f} · baseline: {baseline_score:.4f} "
                f"· σ (paired, model−baseline): {sigma:.4f}\n")
        f.write(f"- **lift = {lift_val:.2f}σ** → {stamp}  (ship iff lift > 2σ)\n")
        f.write(f"- sealed−baseline gap: {gap:+.4f}\n")


def append_probe(ledger_path, auc: float, sigma: float, lift_val: float, certified: bool,
                 n_rows: int | None = None, n_rows_total: int | None = None) -> None:
    stamp = "CERTIFIED ✅" if certified else "⚠ SUSPECT — split may leak a forgotten group/time key"
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write("\n## Probe (split-adversary, warn-only)\n")
        f.write(f"- train-vs-held AUC: {auc:.4f} · σ: {sigma:.4f} · lift: {lift_val:.2f}σ\n")
        # State the row count the verdict actually rests on whenever the probe
        # subsampled. A capped probe that reports its number as though it saw
        # every row would be exactly the kind of quiet overclaim this project
        # exists to catch.
        if n_rows is not None and n_rows_total is not None and n_rows < n_rows_total:
            f.write(f"- scored on a stratified {n_rows:,}-row sample of {n_rows_total:,} "
                    f"(probe cap — see sealed_bet.adversary.PROBE_MAX_ROWS)\n")
        f.write(f"- **{stamp}**\n")


def append_probe_na(ledger_path, reason: str) -> None:
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write("\n## Probe (split-adversary, N/A for this split strategy)\n")
        f.write(f"- **N/A** — {reason}\n")


def append_leakage_probe(ledger_path, findings: list[dict]) -> None:
    flagged = [f for f in findings if f["flagged"]]
    stamp = (
        f"⚠ SUSPECT — {len(flagged)} feature(s) solo-predict the target implausibly well"
        if flagged else "CLEAR ✅ — no feature solo-predicts the target implausibly well"
    )
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write("\n## Probe (leakage-adversary, warn-only)\n")
        for finding in sorted(findings, key=lambda x: x["solo_score"], reverse=True)[:5]:
            flag = " ⚠" if finding["flagged"] else ""
            f.write(f"- `{finding['feature']}`: solo_score {finding['solo_score']:.4f}{flag}\n")
        f.write(f"- **{stamp}**\n")


def append_build_iteration(ledger_path, i: int, regime: str, framing_note: str,
                           dev_score: float, accepted: bool) -> None:
    stamp = "ACCEPTED (new best)" if accepted else "rejected (within noise floor)"
    with open(ledger_path, "a", encoding="utf-8") as f:
        if i == 1:
            f.write("\n## Build (auto)\n")
        f.write(f"- iter {i} · {regime} · {framing_note!r} → dev {dev_score:.4f} · {stamp}\n")
