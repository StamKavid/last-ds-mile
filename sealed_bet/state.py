"""Seal state: enforce that the holdout is opened exactly once."""
from __future__ import annotations

import json
from pathlib import Path

_NAME = "seal_state.json"


def _path(out_dir) -> Path:
    return Path(out_dir) / _NAME


def init_state(out_dir) -> None:
    p = _path(out_dir)
    if is_opened(out_dir):
        raise RuntimeError(
            f"seal state at {p} was already opened and cannot be re-initialized"
        )
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"opened": False}), encoding="utf-8")


def is_opened(out_dir) -> bool:
    p = _path(out_dir)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        opened = data["opened"]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        raise RuntimeError(
            f"seal state file {p} is corrupted and cannot be trusted — the "
            f"holdout's opened/unopened status is unknown; resolve manually before proceeding"
        )
    if not isinstance(opened, bool):
        raise RuntimeError(
            f"seal state file {p} is corrupted and cannot be trusted — the "
            f"holdout's opened/unopened status is unknown; resolve manually before proceeding"
        )
    return opened


def mark_opened(out_dir) -> None:
    _path(out_dir).write_text(json.dumps({"opened": True}), encoding="utf-8")
